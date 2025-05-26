# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

import antlr4, traceback as tb, sys
from typing import Text

from bones.jones import BTypeError
from bones.core.sentinels import Missing
from bones.ts.core import TLError
from bones.ts._type_lang.TypeLangLexer import TypeLangLexer
from bones.ts._type_lang.TypeLangParser import TypeLangParser
from bones.ts._type_lang.ast_builder import TypeLangAstBuilder



class TypeLangInterpreter:
    def __init__(self, tm):
        self._tm = tm

    def eval(self, src):
        if isinstance(src, Text): src = antlr4.InputStream(src)
        l = TypeLangLexer(src)
        stream = antlr4.CommonTokenStream(l)
        p = TypeLangParser(stream)
        tree = p.tl_body()

        w = antlr4.ParseTreeWalker()
        b = TypeLangAstBuilder()
        w.walk(b, tree)
        last = Missing
        for element in b.ast:
            try:
                last = element.eval(self._tm) or last
            except BTypeError as ex:
                stackAndTbToStderr(ex, 'TypeLangInterpreter')
                raise TLError(f'{element} {element.loc.l1}:{element.loc.l2}') from ex
        return last


def stackAndTbToStderr(ex, title):
    s_fss = list(reversed(tb.StackSummary.extract(tb.walk_stack(None))))
    tb_fss = tb.StackSummary.extract(tb.walk_tb(ex.__traceback__))
    first = f'---------------- {title} -----------------'
    last = len(first) * '-'
    print(f'\n{first}\n', file=sys.stderr)
    for fs in s_fss[:-2]:
        if 'Users' in fs.filename:
            print(f'  File "{fs.filename}", line {fs.lineno}, {fs.name}', file=sys.stderr)
    for fs in s_fss[-2:-1]:
        if 'Users' in fs.filename:
            print(f'>>File "{fs.filename}", line {fs.lineno}, {fs.name}', file=sys.stderr)

    for fs in tb_fss[:][0:-3]:
        print(f'  File "{fs.filename}", line {fs.lineno}, {fs.name}', file=sys.stderr)

    for fs in tb_fss[:][-3:]:
        print(f'  File "{fs.filename}", line {fs.lineno}, {fs.name}', file=sys.stderr)
        print(f'    {fs.line}', file=sys.stderr)

    print(f'\n{"".join(tb.format_exception_only(ex))}', file=sys.stderr)
    print(f'{last}\n\n', file=sys.stderr)
