# **********************************************************************************************************************
#
#                             Copyright (c) 2019-2022 David Briant. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#    disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. All advertising materials mentioning features or use of this software must display the following acknowledgement:
#    This product includes software developed by the copyright holders.
#
# 4. Neither the name of the copyright holder nor the names of the  contributors may be used to endorse or promote
#    products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# **********************************************************************************************************************


import sys, time
from bones.core.context import context
from bones.core.sentinels import Missing
from bones.core.errors import ProgrammerError, ErrSite
from bones.lang.metatypes import cacheAndUpdate, fitsWithin, BTAtom
from bones.lang.types import obj
from bones.core.utils import raiseLess


py = BTAtom.ensure("py").setOrthogonal(obj)


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
        tByT = {}
        for tArg, tParam in zip(callerSig, fnSig):
            if tParam is py:
                fallback = True
                argDistances.append(0.5)
            else:
                doesFit, tByTLocal, argDistance = cacheAndUpdate(fitsWithin(tArg, tParam, False), tByT, 0)
                if not doesFit:
                    match = False
                    break
                tByT = tByTLocal
                argDistances.append(argDistance)
        if match:
            distance = sum(argDistances)
            if fallback:
                fallbacks.append((fn, tByT, distance, argDistances))
            else:
                matches.append((fn, tByT, distance, argDistances))
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
                callee = f'{fn.name}({",".join([repr(argT) for argT in fn.sig])}) (argDistances: {argDistances}) defined in {fn.bmodname}<{fn.pymodname}>'
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
                callee = f'{fn.name}({",".join([repr(argT) for argT in fn.sig])}) (argDistances: {argDistances}) defined in {fn.pymodname}'
                print(f'  {callee}', file=sys.stderr)
            raiseLess(TypeError(f'Found {len(matches)} matches and {len(fallbacks)} fallbacks for {caller}', ErrSite("#3")))
        # if not match:
        #     # DOES_NOT_UNDERSTAND`
        #     with context(showFullType=True):
        #         lines = [
        #             f"Can't find {_ppFn(sd.name, callerSig)} ({len(callerSig)} args) in:",
        #             f'  {_ppFn(sd.name, sd.sig, sd._argNames)} ({len(sd.sig)} args) in {sd.bmodname} - {sd.pymodname}'
        #         ]
        #         print('\n'.join(lines), file=sys.stderr)
        #         raiseLess(TypeError('\n'.join(lines), ErrSite("#1")))
    else:
        raise ProgrammerError('Can\'t get here', ErrSite("#4"))
    return fn, tByT



def _cantFindMatchError(sig, nameForError, fnBySigByNumArgsForError):
    with context(showFullType=True):
        # DOES_NOT_UNDERSTAND
        print(f"Can't find {_ppFn(nameForError, sig)} in:", file=sys.stderr)
        for fnBySig in fnBySigByNumArgsForError:
            for fnSig, fn in fnBySig.items():
                print(f'  {_ppFn(fn.name, fnSig)} in {fn.bmodname} - {fn.fullname}', file=sys.stderr)

    return TypeError(f"Can't find {_ppFn(nameForError, sig)}")


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
