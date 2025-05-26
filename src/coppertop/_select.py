# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

from bones.core.context import context
from bones.core.sentinels import Missing
from bones.core.errors import ProgrammerError, ErrSite
from bones.ts.metatypes import updateSchemaVarsWith, fitsWithin, BType
from bones.ts.core import SchemaError, BTypeError
from bones.core.utils import raiseLess



py = BType('py: atom in mem')

def _selectFunction(callerSig, fnBySig, nameForError, fnBySigByNumArgsForError):
    matches = []
    fallbacks = []
    # search though each bound function ignoring discrepancies where the declared type is py
    distance = 10000
    for fnSig, fn in fnBySig.items():
        distance = 10000
        fallback = False
        match = True
        argDistances = []
        schemaVars = {}
        for tArg, tParam in zip(callerSig, fnSig):
            if tParam is py:
                fallback = True
                argDistances.append(0.5)
            else:
                fits = fitsWithin(tArg, tParam)
                if not fits:
                    match = False
                    break
                try:
                    schemaVars, argDistance = updateSchemaVarsWith(schemaVars, 0, fits)
                except SchemaError:
                    match = False
                    break
                argDistances.append(argDistance)
        if match:
            distance = sum(argDistances)
            if fallback:
                fallbacks.append((fn, schemaVars, distance, argDistances))
            else:
                matches.append((fn, schemaVars, distance, argDistances))
        if distance == 0:
            break
    if distance == 0:
        fn, tByT, distance, argDistances = matches[-1]
    elif len(matches) == 0 and len(fallbacks) == 0:
        raiseLess(_cantFindMatchError(callerSig, nameForError, fnBySigByNumArgsForError), ErrSite("#1"))
    elif len(matches) == 1:
        fn, tByT, distance, argDistances = matches[0]
    elif len(matches) == 0 and len(fallbacks) == 1:
        fn, tByT, distance, argDistances = fallbacks[0]
    elif len(matches) > 0:
        matches.sort(key=lambda x: x[2])
        # MUSTDO warn of potential conflicts that have not been explicitly noted
        if matches[0][2] != matches[1][2]:
            fn, tByT, distance, argDistances = matches[0]
        else:
            # DOES_NOT_UNDERSTAND
            # too many at same distance so report the situation nicely
            caller = f'{nameForError}({",".join([repr(e) for e in callerSig])})'
            print(f'1. {caller} fitsWithin:', file=sys.stderr)
            for fn, tByT, distance, argDistances in matches:
                callee = f'{fn.name}({",".join([repr(argT) for argT in fn.sig])}) (argDistances: {argDistances}) defined in {fn.modname}'
                print(f'  {callee}', file=sys.stderr)
            raiseLess(TypeError(f'Found {len(matches)} matches and {len(fallbacks)} fallbacks for {caller}', ErrSite("#2")))
    elif len(fallbacks) > 0:
        fallbacks.sort(key=lambda x: x[2])
        # MUSTDO warn of potential conflicts that have not been explicitly noted
        if fallbacks[0][2] != fallbacks[1][2]:
            fn, tByT, distance, argDistances = fallbacks[0]
        else:
            # DOES_NOT_UNDERSTAND
            # too many at same distance so report the situation nicely
            caller = f'2. {actual, expectednameForError}({",".join([repr(e) for e in callerSig])})'
            print(f'{caller} fitsWithin:', file=sys.stderr)
            for fn, tByT, distance, argDistances in matches:
                callee = f'{fn.name}({",".join([repr(argT) for argT in fn.sig])}) (argDistances: {argDistances}) defined in {fn.modname}'
                print(f'  {callee}', file=sys.stderr)
            raiseLess(TypeError(f'Found {len(matches)} matches and {len(fallbacks)} fallbacks for {caller}', ErrSite("#3")))
        # if not match:
        #     # DOES_NOT_UNDERSTAND`
        #     with context(showFullType=True):
        #         lines = [
        #             f"Can't find {_ppFn(sd.name, callerSig)} ({len(callerSig)} args) in:",
        #             f'  {_ppFn(sd.name, sd.sig, sd._argNames)} ({len(sd.sig)} args) in {sd.modname} - {sd.modname}'
        #         ]
        #         print('\n'.join(lines), file=sys.stderr)
        #         raiseLess(TypeError('\n'.join(lines), ErrSite("#1")))
    else:
        raise ProgrammerError('Can\'t get here', ErrSite("#4"))
    return fn, tByT



def _cantFindMatchError(sig, nameForError, fnBySigByNumArgsForError):
    with context(showFullType=True):
        # DOES_NOT_UNDERSTAND
        context.EE(f"Can't find {_ppFn(nameForError, sig)} in:")
        for fnBySig in fnBySigByNumArgsForError:
            for fnSig, fn in fnBySig.items():
                context.EE(f'  {_ppFn(fn.name, fnSig)} in {fn.modname} - {fn.fullname}')

    return BTypeError(f"Can't find {_ppFn(nameForError, sig)}")


def _ppFn(name, sig, argNames=Missing):
    if argNames is Missing:
        return f'{name}({", ".join([_ppType(t) for t in sig])})'
    else:
        return f'{name}({", ".join([f"{n}:{_ppType(t)}" for t, n in zip(sig, argNames)])})'


def _ppType(t):
    if t is py:
        return "py"
    elif type(t) is type:
        return t.__name__
    else:
        return repr(t)

