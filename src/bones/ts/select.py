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

import collections, builtins
from bones.core.context import context
from bones.core.sentinels import Missing, function
from bones.core.errors import ProgrammerError, ErrSite
from bones.ts.metatypes import updateSchemaVarsWith, fitsWithin, BTFamily, BType, _btypeByClass, _BTypeById
from bones.ts.core import SchemaError, BTypeError
from bones.core.utils import raiseLess, firstValue

from bones.lang.types import _tvfunc, btype
from bones import jones
from coppertop._scopes import _CoWProxy


py = BType('py: atom in mem')
DISABLE_RETURN_CHECK = False
DISABLE_ARG_CHECK_FOR_SOLE_FN = False
BETTER_ERRORS = False

SelectionResult = collections.namedtuple('SelectionResult', ['d', 'tByT'])


# **********************************************************************************************************************
# _Family
# **********************************************************************************************************************

class _Family:

    __slots__ = ['style', 'name', '_t', '_fnBySigByNumArgs', '_cacheByNumArgs', '__doc__']

    def __new__(cls, *tvfuncs):
        name = Missing
        style = Missing
        ds = []
        maxNumArgs = 0

        for tvfunc in tvfuncs:
            if not tvfunc: continue
            if name is Missing: name, style = tvfunc.name, tvfunc.style
            if isinstance(tvfunc, _Family):
                for fnBySig in tvfunc._fnBySigByNumArgs:
                    for d2 in fnBySig.values():
                        if isinstance(d2, _tvfunc):
                            cls._checkDispatcher(d2, name, style)
                            ds.append(d2)
                        else:
                            raiseLess(ProgrammerError("unknown dispatcher class", ErrSite(cls, "#5")))
                if len(tvfunc._fnBySigByNumArgs) > maxNumArgs: maxNumArgs = len(tvfunc._fnBySigByNumArgs) - 1  # don't forget 0 args
            elif isinstance(tvfunc, _tvfunc):
                cls._checkDispatcher(tvfunc, name, style)
                if len(tvfunc.sig) > maxNumArgs: maxNumArgs = len(tvfunc.sig)
                ds.append(tvfunc)
            else:
                raiseLess(ProgrammerError("unhandled dispatcher class", ErrSite(cls, "#11")))

        _fnBySigByNumArgs = [{} for i in range(maxNumArgs + 1)]
        for tvfunc in ds:
            oldD = _fnBySigByNumArgs[len(tvfunc.sig)].get(tvfunc.sig, Missing)
            # if oldD is not Missing and oldD.modname != tvfunc.modname:
            #     raise CoppertopError(f'Found definition of {_ppFn(name, tvfunc.sig)} in "{tvfunc.modname}" and "{oldD.modname}"', ErrSite(cls, "#12"))
            _fnBySigByNumArgs[len(tvfunc.sig)][tvfunc.sig] = tvfunc
        # if len(_fnBySigByNumArgs) == 1 and len(_fnBySigByNumArgs[0]) == 1:
        #     # this can occur in a REPL where a function is being redefined
        #     # SHOULDDO think this through as potentially we could overload functions in the repl accidentally which
        #     #  would be profoundly confusing
        #     return tvfunc
        instance = super().__new__(cls)
        instance.name = name
        instance.style = style
        instance._fnBySigByNumArgs = _fnBySigByNumArgs
        instance._cacheByNumArgs = [Missing] * (maxNumArgs + 1)
        ts = []
        for fnBySig in _fnBySigByNumArgs:
            for fn in fnBySig.values():
                ts.append(fn._t)
        instance._t = BTFamily(*ts)
        instance.__doc__ = None
        return instance

    @classmethod
    def _checkDispatcher(cls, tvfunc, name, style):
        if tvfunc.name != name:
            raiseLess(ProgrammerError(
                f'Incompatible name - trying to overload function "{tvfunc.name}" with existing function "{name}"',
                ErrSite(cls, "#1")))
        if tvfunc.style != style:
            raiseLess(ProgrammerError(
                f'Incompatible style - tyring to overload {tvfunc.dtyle} function "{tvfunc.name}" with existing {style} function "{name}"',
                ErrSite(cls, "#10")))

    def selectFn(self, args):
        numArgs = len(args)
        if numArgs == 0:
            tvfn = self._fnBySigByNumArgs[0][()]
            tByT = {}
            hasValue = True
        else:
            # ensure we have a cache
            if numArgs > len(self._cacheByNumArgs) - 1:
                raise TypeError(f"Too many args passed to  {self.name} - max {len(self._cacheByNumArgs) - 1}, passed {numArgs}")

            if DISABLE_ARG_CHECK_FOR_SOLE_FN and len(fns := self._fnBySigByNumArgs[numArgs]) == 1:
                return firstValue(fns), {}, True

            if (cache := self._cacheByNumArgs[numArgs]) is Missing:
                pSC = jones.sc_new(numArgs, 100)
                cache = self._cacheByNumArgs[numArgs] = (pSC, [])
            pSC, results = cache

            hasValue = jones.sc_fillQuerySlotWithBTypesOf(pSC, args, _btypeByClass, py, _CoWProxy)

            # t2 = time.perf_counter_ns()
            resultId = jones.sc_getFnId(pSC)
            # t3 = time.perf_counter_ns()

            if resultId == 0:
                # missTime1 += t2 - t1; missTime2 += t3 - t2; misses += 1
                tArgs = jones.sc_tArgsFromQuery(pSC, _BTypeById)
                tvfn, tByT, distance, argDistances = selectFunction(tArgs, self._fnBySigByNumArgs[numArgs], py, self.name, self._fnBySigByNumArgs)
                results.append((tvfn, tByT))
                pQuery = jones.sc_queryPtr(pSC)
                iNext = jones.sc_nextFreeArrayIndex(pSC)
                if iNext == 0:
                    raise RuntimeError("Array not big enough")
                jones.sc_atArrayPut(pSC, iNext, pQuery, len(results))
                # searchTime += time.perf_counter_ns() - t3; dispatchTime += t3 - t1
            else:
                # hitTime1 += t2 - t1; hitTime2 += t3 - t2; hits += 1; dispatchTime += t3 - t1
                tvfn, tByT = results[resultId - 1]
        return tvfn, tByT, hasValue

    def __call__(self, *args):
        # global hits, misses, hitTime1, hitTime2, missTime1, missTime2, searchTime, dispatchTime, dispatchCount, returnTime, returnCount
        # t1 = time.perf_counter_ns()

        if DISABLE_ARG_CHECK_FOR_SOLE_FN:
            numArgs = len(args)
            if numArgs <= len(self._fnBySigByNumArgs):
                if len(ov := self._fnBySigByNumArgs[numArgs]) == 1:
                    tvfn = firstValue(ov)
                    if not tvfn.pass_tByT:
                        return tvfn._v(*args)

        tvfn, tByT, hasValue = self.selectFn(args)

        # t4 = time.perf_counter_ns()

        if hasValue or tvfn.dispatchEvenIfAllTypes:
            if tvfn.pass_tByT:
                if tvfn.typeHelper:
                    tByT = tvfn.typeHelper(*args, tByT=tByT)
                # dispatchTime += time.perf_counter_ns() - t4; dispatchCount += 1
                ret = tvfn._v(*args, tByT=tByT)
                if DISABLE_RETURN_CHECK:
                    return ret
                # t5 = time.perf_counter_ns()
            else:
                if BETTER_ERRORS:
                    # better error messages
                    # instead of the Python one:
                    #       TypeError: createBag() missing 1 required positional argument: 'otherHandSizesById'
                    #
                    # TypeError: createBag() does match createBag(handId:any, hand:any, otherHandSizesById:any) -> cluedo_bag
                    # even better say we can't find a match for two arguments
                    try:
                        # dispatchTime += time.perf_counter_ns() - t4; dispatchCount += 1
                        ret = tvfn._v(*args)
                        if DISABLE_RETURN_CHECK:
                            return ret
                        # t5 = time.perf_counter_ns()
                    except TypeError as ex:
                        if ex.args and ' required positional argument' in ex.args[0]:
                            print(ppSig(tvfn), file=sys.stderr)
                            print(ex.args[0], file=sys.stderr)
                        raiseLess(ex, True)
                        # argTs = [_ppType(argT) for argT in args]
                        # retT = _ppType(x.tRet)
                        # return f'({",".join(argTs)})->{retT} <{x.style.name}>  :   in {x.fullname}'
                else:
                    # dispatchTime += time.perf_counter_ns() - t4; dispatchCount += 1
                    ret = tvfn._v(*args)
                    if DISABLE_RETURN_CHECK:
                        return ret
                    # t5 = time.perf_counter_ns()
            tRet = tvfn.tRet

            if tRet == py or isinstance(ret, SelectionResult):
                # returnTime += time.perf_counter_ns() - t5; returnCount += 1
                return ret
            else:
                # MUSTDO
                # BTTuples are products whereas pytuples are exponentials therefore we can reliably type check an answered
                # sequence if the return type is BTTuple (and possibly BTStruct) - also BTTuple can be coerced by default to
                # a dseq (or similar - may should add a new tuple subclass to prevent it being treated like an exponential)
                # add a note in bones that one of our basic ideas / building blocks is things and exponentials of things
                if hasattr(ret, '_t'):
                    if ret._t:
                        # check the actual return type fits the declared return type
                        if fitsWithin(ret._t, tRet):
                            return ret
                        else:
                            raiseLess(BTypeError(f'{tvfn.fullname} returned a {str(_typeOf(ret))} should have have returned a {tRet} {tByT}',ErrSite("#1")))
                    else:
                        return ret | tRet
                else:
                    # use the coercer rather than impose construction with tv
                    if fitsWithin(_typeOf(ret), tRet):
                        return ret
                    else:
                        return ret | tRet

        else:
            # dispatchTime += time.perf_counter_ns() - t4; dispatchCount += 1
            return SelectionResult(tvfn, tByT)


    def _tPartial(self, num_args, o_tbc):
        # if this is a bottle neck can be cached
        ts = []
        for tvfn in self._fnBySigByNumArgs[num_args].values():
            ts.append(tvfn._tPartial(o_tbc))
        return BTFamily(*ts)


    def __repr__(self):
        return self.name



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
            # DOES_NOT_UNDERSTAND - too many matches at the same distance
            with context(showFullType=True):
                caller = _ppFn(fnNameForErr, callerSig)
                context.EE(f'1. {caller} fitsWithin:')
                for fn, tByT, distance, argDistances in matches:
                    callee = f'{_ppFn(fn.name, fn.sig)}) (argDistances: {argDistances}) - {fn.fullname} defined in {fn.modname}'
                    context.EE(f'  {callee}')
            raiseLess(TypeError(f'Found {len(matches)} matches and {len(fallbacks)} fallbacks for {caller}', ErrSite("#2")))
    elif len(fallbacks) == 1:
        return fallbacks[0]
    elif len(fallbacks) > 1:
        fallbacks.sort(key=lambda x: x[2])
        # OPEN: warn of potential conflicts that have not been explicitly noted (i.e. that have the same distance to the signature)
        if fallbacks[0][2] != fallbacks[1][2]:
            return fallbacks[0]
        else:
            # DOES_NOT_UNDERSTAND - too many fallbacks at the same distance
            with context(showFullType=True):
                caller = _ppFn(fnNameForErr, callerSig)
                context.EE(f'2. {caller} fitsWithin:')
                # for nArgs, fnBySig in familyFnForErr().items()
                for fn, tByT, distance, argDistances in matches:
                    callee = f'{_ppFn(fn.name, fn.sig)}) (argDistances: {argDistances}) - {fn.fullname} defined in {fn.modname}'
                    context.EE(f'  {callee}')
            raiseLess(TypeError(f'Found {len(matches)} matches and {len(fallbacks)} fallbacks for {caller}', ErrSite("#3")))
    else:
        # DOES_NOT_UNDERSTAND - no matches or fallbacks
        with context(showFullType=True):
            caller = _ppFn(fnNameForErr, callerSig)
            context.EE(f'No matches for {caller} in:')
            for sig, fn in fnBySig.items():
                callee = f'{_ppFn(fn.name, sig)}) - {fn.fullname} defined in {fn.modname}'
                context.EE(f'  {callee}')
        raiseLess(BTypeError(f'No matches for {caller}'), ErrSite("#1"))



# **********************************************************************************************************************
# Utilities
# **********************************************************************************************************************

def _typeOf(x):
    if hasattr(x, '_t'):
        return x._t                     # it's a tv of some sort so return the t
    elif isinstance(x, jones._fn):
        return x.d._t
    elif isinstance(x, jones._pfn):
        return x.d._tPartial(x.num_args, x.o_tbc)
    elif isinstance(x, BType):
        return btype
    else:
        t = builtins.type(x)
        if t is _CoWProxy:
            t = builtins.type(x._target)         # return the type of thing being proxied
        return _btypeByClass.get(t, t)       # type python types as their bones equivalent

sys._typeOf = _typeOf               # required by coercion - do not remove

def ppSig(x):
    if isinstance(x, function):
        return f'{x.__name__} is a Python function'
    x = x.d
    if isinstance(x, _Family):
        answer = []
        for fnBySig in x._fnBySigByNumArgs:
            for sig, tvfunc in fnBySig.items():
                argTs = [_ppType(argT) for argT in sig]
                retT = _ppType(tvfunc.tRet)
                answer.append(f'({",".join(argTs)})->{retT} <{tvfunc.style.name}>  :   in {tvfunc.fullname}')
        return answer
    else:
        argTs = [_ppType(argT) for argT in x.sig]
        retT = _ppType(x.tRet)
        return f'({",".join(argTs)})->{retT} <{x.style.name}>  :   in {x.fullname}'

def _ppFn(name, sig, argNames=Missing):
    if argNames is Missing:
        return f'{name}({",".join([_ppType(t) for t in sig])})'
    else:
        return f'{name}({",".join([f"{n}:{_ppType(t)}" for t, n in zip(sig, argNames)])})'

def _ppType(t):
    if type(t) is type:
        return t.__name__
    else:
        return repr(t)
