# **********************************************************************************************************************
# Copyright (c) 2025 David Briant. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
# **********************************************************************************************************************

import antlr4
from typing import Text

from bones.core.sentinels import Missing

from bones.lang._type_lang.TypeLangLexer import TypeLangLexer
from bones.lang._type_lang.TypeLangParser import TypeLangParser
from bones.lang._type_lang.ast_builder import TypeLangAstBuilder



class TypeLangInterpreter:
    def __init__(self, tm):
        self._tm = tm

    def parse(self, src):
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
            last = element.eval(self._tm, Missing) or last
        return last

