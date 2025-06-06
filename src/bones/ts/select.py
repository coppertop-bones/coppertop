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
from bones.ts.metatypes import updateSchemaVarsWith, fitsWithin
from bones.ts.core import SchemaError, BTypeError
from bones.core.utils import raiseLess



def selectFunction(callerSig, fnBySig, catchAllType, fnNameForErr, familyFnForErr):
    fallbacks, matches = [], []
    # search though each function in fnBySig recording catchAll matches separately from actual matches
    distance = 10000
    for fnSig, fn in fnBySig.items():
        distance = 10000
        fallback = False
        match = True
        argDistances = []
        schemaVars = {}
        for tArg, tFnArg in zip(callerSig, fnSig):
            if tFnArg == catchAllType:
                fallback = True
                argDistances.append(0.5)
            else:
                fits = fitsWithin(tArg, tFnArg)
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
            distance = sum(argDistances)        # effective L1, could do L2 or something else but needs to be easy to understand and intuit
            if fallback:
                fallbacks.append((fn, schemaVars, distance, argDistances))
            else:
                matches.append((fn, schemaVars, distance, argDistances))
        if distance == 0:
            # OPEN: instead of escaping at first match complete the search and warn of potential conflicts (i.e. fns that have the same distance to the signature)
            return fn, schemaVars, distance, argDistances

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        matches.sort(key=lambda x: x[2])
        # OPEN: warn of potential conflicts (i.e. fns that have the same distance to the signature)
        if matches[0][2] != matches[1][2]:
            return matches[0]
        else:
            # DOES_NOT_UNDERSTAND - too many matches at the same distance so report the situation nicely
            caller = f'{fnNameForErr}({",".join([repr(e) for e in callerSig])})'
            print(f'1. {caller} fitsWithin:', file=sys.stderr)
            for fn, tByT, distance, argDistances in matches:
                callee = f'{fn.name}({",".join([repr(argT) for argT in fn.sig])}) (argDistances: {argDistances}) defined in {fn.modname}'
                print(f'  {callee}', file=sys.stderr)
            raiseLess(TypeError(f'Found {len(matches)} matches and {len(fallbacks)} fallbacks for {caller}', ErrSite("#2")))
    elif len(fallbacks) == 1:
        return fallbacks[0]
    elif len(fallbacks) > 0:
        fallbacks.sort(key=lambda x: x[2])
        # OPEN: warn of potential conflicts that have not been explicitly noted (i.e. that have the same distance to the signature)
        if fallbacks[0][2] != fallbacks[1][2]:
            return fallbacks[0]
        else:
            # DOES_NOT_UNDERSTAND - too many fallbacks at the same distance so report the situation nicely
            caller = f'2. {fnNameForErr}({",".join([repr(e) for e in callerSig])})'
            print(f'{caller} fitsWithin:', file=sys.stderr)
            for fn, tByT, distance, argDistances in matches:
                callee = f'{fn.name}({",".join([repr(argT) for argT in fn.sig])}) (argDistances: {argDistances}) defined in {fn.modname}'
                print(f'  {callee}', file=sys.stderr)
            raiseLess(TypeError(f'Found {len(matches)} matches and {len(fallbacks)} fallbacks for {caller}', ErrSite("#3")))
    else:
        raiseLess(_cantFindMatchError(callerSig, fnNameForErr, fnBySig, familyFnForErr), ErrSite("#1"))


def _cantFindMatchError(sig, fnNameForErr, fnBySig, familyFnForErr):
    with context(showFullType=True):
        context.EE(f"Can't find {_ppFn(fnNameForErr, sig)} in:")
        # for nArgs, fnBySig in familyFnForErr().items():
        for fnSig, fn in fnBySig.items():
            context.EE(f'  {_ppFn(fn.name, fnSig)} in {fn.modname} - {fn.fullname}')

    return BTypeError(f"Can't find {_ppFn(fnNameForErr, sig)}")


def _ppFn(name, sig, argNames=Missing):
    if argNames is Missing:
        return f'{name}({", ".join([_ppType(t) for t in sig])})'
    else:
        return f'{name}({", ".join([f"{n}:{_ppType(t)}" for t, n in zip(sig, argNames)])})'


def _ppType(t):
    if type(t) is type:
        return t.__name__
    else:
        return repr(t)
