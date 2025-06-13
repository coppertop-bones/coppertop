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

from bones import jones
from bones.core.context import context
from bones.core.sentinels import Missing, function
from bones.core.errors import ProgrammerError, ErrSite, NotYetImplemented
from bones.ts.metatypes import updateSchemaVarsWith, fitsWithin, BTFamily, BType, _btypeByClass, _BTypeById, BTUnion, \
    BTFn, BTAtom, BTTuple, btype, TBI
from bones.ts.core import SchemaError, BTypeError
from bones.core.utils import raiseLess, firstValue

from coppertop._scopes import _CoWProxy


py = BType('py: atom in mem')

DISABLE_RETURN_CHECK = False
DISABLE_ARG_CHECK_FOR_SOLE_FN = False

SelectionResult = collections.namedtuple('SelectionResult', ['tvfunc', 'tByT'])



# **********************************************************************************************************************
# function struct
# **********************************************************************************************************************

class _tvfunc:

    __slots__ = [
        'style', 'name', '_t', 'modname', '_v', '_argNames', 'sig', 'tArgs', 'tRet',
        'pass_tByT', 'dispatchEvenIfAllTypes', 'typeHelper', '__doc__'
     ]

    def __init__(self, *, name, modname, style, _v, dispatchEvenIfAllTypes, typeHelper, _t, argNames, pass_tByT):
        if not isinstance(_t, BTFn): raise TypeError('_t is not a BTFn')
        self.name = name
        self.modname = modname
        self.style = style
        self._v = _v
        self._argNames = argNames
        self._t = _t
        self.tArgs = _t.tArgs
        self.tRet = _t.tRet
        self.sig = _t.tArgs.types
        self.pass_tByT = pass_tByT
        self.dispatchEvenIfAllTypes = dispatchEvenIfAllTypes          # calls the function rather returning a SelectionResult when all args are types
        self.typeHelper = typeHelper
        self.__doc__ = _v.__doc__ if hasattr(_v, '__doc__') else None

    def __call__(self, *args, schemaVars=Missing):
        try:
            if self.pass_tByT:
                if schemaVars is Missing:
                    match, fallback, schemaVars, argDistances = _distancesEtAl([_typeOf(arg) for arg in args], self.sig)
                if self.typeHelper:
                    tByT = self.typeHelper(*args, tByT=schemaVars)
                ret = self._v(*args, tByT=schemaVars)
            else:
                ret = self._v(*args)
        except TypeError as ex:
            # instead of TypeError: createBag() missing 1 required positional argument: 'otherHandSizesById'
            # print out the signature and provided args
            if ex.args and ' required positional argument' in ex.args[0]:
                print(ppSig(self), file=sys.stderr)
                print(ex.args[0], file=sys.stderr)
            raiseLess(ex, True)

        if DISABLE_RETURN_CHECK:
            return ret
        else:
            tRet = self.tRet
            if tRet == py or isinstance(ret, SelectionResult):
                return ret
            else:
                # OPEN: BTTuples are products whereas pytuples are exponentials therefore we can reliably type check
                # an answered sequence if the return type is BTTuple (and possibly BTStruct) - also BTTuple can be
                # coerced by default to a dseq
                if hasattr(ret, '_t'):
                    if ret._t:
                        # check the actual return type fits the declared return type
                        if fitsWithin(ret._t, tRet):
                            return ret
                        else:
                            raiseLess(BTypeError(f'{self.fullname} returned a {str(_typeOf(ret))} should have have returned a {tRet} {tByT}',ErrSite("#1")))
                    else:
                        return ret | tRet
                else:
                    if fitsWithin(_typeOf(ret), tRet):
                        return ret
                    else:
                        # use the coercer rather than impose construction with tv
                        return ret | tRet

    @property
    def fullname(self):
        return self.modname + '.' + self.name

    @property
    def numargs(self):
        return len(self.sig)

    def _tPartial(self, o_tbc):
        return BTFn(BTTuple(*(self.sig[o] for o in o_tbc)), self.tRet)

    def __repr__(self):
        return self.name



# **********************************************************************************************************************
# Overload
# **********************************************************************************************************************

class Overload:
    # limited dictionary style interface object that stores tvfunc by sig for a given name and number of args

    __slots__ = ['name', 'numargs', '_fnsTBI', '_t_', '_tUpperBounds_', '_tvfuncBySig', 'cache']

    @classmethod
    def newForMutation(cls, name, numargs):
        instance = super().__new__(cls)
        instance.name = name
        instance.numargs = numargs
        instance._fnsTBI = _TBIQueue()
        instance._t_ = Missing
        instance._tUpperBounds_ = Missing           # set else where
        instance._tvfuncBySig = {}
        instance.cache = Missing
        return instance

    def __new__(self):
        # OPEN: maybe provide a constructor that takes two or more tvfuncs
        raise ProgrammerError("Overload cannot be constructed directly - use Overload.newForMutation(...)")

    @property
    def _t(self):
        if self._t_ is Missing:
            self._t_ = BTFamily(*[fn._t for fn in self._tvfuncBySig.values()])      # OPEN: do we need BTOverload?
        return self._t_

    def __setitem__(self, sig, tvfunc):
        if tvfunc.numargs != self.numargs: raise ProgrammerError()
        self._t_ = Missing
        self._tUpperBounds_ = Missing
        needsInferring = False
        for tArg in tvfunc.tArgs:
            if tArg == TBI:
                needsInferring = True
                break
        if tvfunc.tRet == TBI:
            needsInferring = True
        if needsInferring:
            # if any arg needs to be inferred then it cannot be added to the overload yet and that can only be done
            # post inference so let's try queuing it?
            self._fnsTBI << tvfunc
        else:
            if tvfunc in self._fnsTBI:
                self._fnsTBI.remove(tvfunc)
            self._tvfuncBySig[sig] = tvfunc

    def __getitem__(self, sig):
        return self._tvfuncBySig[sig]

    def items(self):
        return self._tvfuncBySig.items()

    def __len__(self):
        return len(self._tvfuncBySig)

    def __repr__(self):
        answer = f'{self.name}_{self.numargs}'
        ppT = ''
        try:
            ppT = repr(self._t)
        except:
            1/0
            try:
                tArgs = []
                tRets = []
                # collate the types for each arg
                for i in range(self.numargs):
                    tArgsN = []
                    for tvfunc in self._fnsTBI:
                        tArgsN.append(tvfunc.tArgs.types[i])
                    tArgs.append(BTUnion(*tArgsN) if len(tArgsN) != 1 else tArgsN[0])
                # collate the tRets
                for tvfunc in self._fnsTBI:
                    tRets.append(tvfunc.tRet)
                tRet = BTUnion(*tRets) if len(tRets) > 1 else tRets[0]
                ppT = repr(BTFn(tArgs, tRet))
            except:
                ppT = 'Error calc _tUpper'

        return f'{answer} ({ppT})'

    def __call__(self, *args):
        if DISABLE_ARG_CHECK_FOR_SOLE_FN and len(self._tvfuncBySig) == 1:
            return firstValue(self._tvfuncBySig)(*args)
        tvfunc, schemaVars, hasValue = self.selectFunction(*args)
        if hasValue or tvfunc.dispatchEvenIfAllTypes:
            return tvfunc(*args, schemaVars=schemaVars)
        else:
            return SelectionResult(tvfunc, schemaVars)

    def selectFunction(self, *args):
        if self.numargs == 0:
            tvfunc = self._tvfuncBySig[()]
            tByT = {}
            hasValue = True
        else:
            # ensure we have a cache
            if DISABLE_ARG_CHECK_FOR_SOLE_FN and len(fns := self._tvfuncBySig) == 1:
                return firstValue(fns), {}, True

            if self.cache is Missing:
                pSC = jones.sc_new(self.numargs, 100)
                self.cache = (pSC, [])
            pSC, results = self.cache

            hasValue = jones.sc_fillQuerySlotWithBTypesOf(pSC, args, _btypeByClass, py, _CoWProxy)

            resultId = jones.sc_getFnId(pSC)

            if resultId == 0:
                tArgs = jones.sc_tArgsFromQuery(pSC, _BTypeById)
                tvfunc, tByT, distance, argDistances = self._selectFunction(tArgs)
                results.append((tvfunc, tByT))
                pQuery = jones.sc_queryPtr(pSC)
                iNext = jones.sc_nextFreeArrayIndex(pSC)
                if iNext == 0:
                    raise RuntimeError("Array not big enough")
                jones.sc_atArrayPut(pSC, iNext, pQuery, len(results))
            else:
                tvfunc, tByT = results[resultId - 1]
        return tvfunc, tByT, hasValue

    def _selectFunction(self, callerSig):
        fallbacks, matches = [], []
        # search though each function in _tvfuncBySig recording catchAll matches separately from actual matches
        distance = 10000
        for fnSig, fn in self._tvfuncBySig.items():
            distance = 10000
            match, fallback, schemaVars, argDistances = _distancesEtAl(callerSig, fnSig)
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
                # DOES_NOT_UNDERSTAND - too many matches at the smallest distance
                with context(showFullType=True):
                    caller = _ppFn(self.name, callerSig)
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
                # DOES_NOT_UNDERSTAND - too many fallbacks at the smallest distance
                with context(showFullType=True):
                    caller = _ppFn(self.name, callerSig)
                    context.EE(f'2. {caller} fitsWithin:')
                    for fn, tByT, distance, argDistances in matches:
                        callee = f'{_ppFn(fn.name, fn.sig)}) (argDistances: {argDistances}) - {fn.fullname} defined in {fn.modname}'
                        context.EE(f'  {callee}')
                raiseLess(TypeError(f'Found {len(matches)} matches and {len(fallbacks)} fallbacks for {caller}', ErrSite("#3")))
        else:
            # DOES_NOT_UNDERSTAND - no matches or fallbacks
            with context(showFullType=True):
                caller = _ppFn(self.name, callerSig)
                context.EE(f'No matches for {caller} in:')
                for sig, fn in self._tvfuncBySig.items():
                    callee = f'{_ppFn(fn.name, sig)}) - {fn.fullname} defined in {fn.modname}'
                    context.EE(f'  {callee}')
            raiseLess(BTypeError(f'No matches for {caller}'), ErrSite("#1"))


def _distancesEtAl(callerSig, fnSig):
    if len(callerSig) == 2 and len(fnSig) == 2 and callerSig[0].id == 108 and callerSig[1].id == 106 and fnSig[0].id == 108 and fnSig[1].id == 106:
        pass
    fallback = False
    match = True
    argDistances = []
    schemaVars = {}
    for tArg, tFnArg in zip(callerSig, fnSig):
        if tFnArg == py:
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
    return match, fallback, schemaVars, argDistances



# **********************************************************************************************************************
# Family
# **********************************************************************************************************************

class Family:

    __slots__ = ['style', 'name', '_t', '_overloadByNumArgs', '_doc']

    # we provide two construction interfaces - one used by the parser to create a new family for a function that can
    # hold just a single function and the other used coppertop to create which is the intersection of two or more
    # overloads

    @classmethod
    def newForMutation(cls, *, name, style=Missing):
        instance = super().__new__(cls)
        instance.name = name
        instance.style = style
        instance._t = Missing
        instance._overloadByNumArgs = []
        instance._doc = Missing
        return instance

    def __new__(cls, *args, name=Missing):

        name, style, tvfuncs, maxNumArgs = Missing, Missing, [], 0

        for arg in args:
            if not arg: continue
            if name is Missing: name, style = arg.name, arg.style
            if isinstance(arg, Family):
                for overload in arg._overloadByNumArgs:
                    for _, tvfunc in overload.items():
                        if isinstance(tvfunc, _tvfunc):
                            cls._checkTvfunc(tvfunc, name, style)
                            tvfuncs.append(tvfunc)
                        else:
                            raiseLess(ProgrammerError("unknown dispatcher class", ErrSite(cls, "#5")))
                if len(arg._overloadByNumArgs) > maxNumArgs: maxNumArgs = len(arg._overloadByNumArgs) - 1  # don't forget 0 args
            elif isinstance(arg, _tvfunc):
                cls._checkTvfunc(arg, name, style)
                if len(arg.sig) > maxNumArgs: maxNumArgs = len(arg.sig)
                tvfuncs.append(arg)
            else:
                raiseLess(ProgrammerError("unhandled dispatcher class", ErrSite(cls, "#11")))

        _overloadByNumArgs = [Overload.newForMutation(name, numargs) for numargs in range(maxNumArgs + 1)]
        for tvfunc in tvfuncs:
            # oldD = _overloadByNumArgs[len(tvfunc.sig)].get(tvfunc.sig, Missing)
            # if oldD is not Missing and oldD.modname != tvfunc.modname:
            #     raise CoppertopError(f'Found definition of {_ppFn(name, tvfunc.sig)} in "{tvfunc.modname}" and "{oldD.modname}"', ErrSite(cls, "#12"))
            _overloadByNumArgs[len(tvfunc.sig)][tvfunc.sig] = tvfunc
        # if len(_overloadByNumArgs) == 1 and len(_overloadByNumArgs[0]) == 1:
        #     # this can occur in a REPL where a function is being redefined
        #     # SHOULDDO think this through as potentially we could overload functions in the repl accidentally which
        #     #  would be profoundly confusing
        #     return tvfunc
        instance = super().__new__(cls)
        instance.name = name
        instance.style = style
        instance._overloadByNumArgs = _overloadByNumArgs
        ts = []
        for overload in _overloadByNumArgs:
            for sig, fn in overload.items():
                ts.append(fn._t)
        if ts:
            instance._t = BTFamily(*ts)
        else:
            instance._t = Missing    # Empty Family is being constructed
        instance._doc = None
        return instance


    def __call__(self, *args):
        if (numArgs := len(args)) > len(self._overloadByNumArgs) - 1:
            raise TypeError(f"Too many args passed to  {self.name} - max {len(self._overloadByNumArgs) - 1}, passed {numArgs}")
        return self._overloadByNumArgs[numArgs](*args)


    def getOverload(self, numargs):
        if numargs >= len(self._overloadByNumArgs):
            self._overloadByNumArgs = self._overloadByNumArgs + [Overload.newForMutation(self.name, numargs) for numargs in range(len(self._overloadByNumArgs), numargs + 1)]
        return self._overloadByNumArgs[numargs]

    def _tPartial(self, num_args, o_tbc):
        # if this is a bottleneck can be cached
        ts = []
        for sig, tvfunc in self._overloadByNumArgs[num_args].items():
            ts.append(tvfunc._tPartial(o_tbc))
        return BTFamily(*ts)

    def __repr__(self):
        return self.name

    @property
    def __doc__(self):
        if self._doc:
            return self._doc
        else:
            return 'NotYetImplemented - this should return a docstring for all the overloads in the family.'

    @classmethod
    def _checkTvfunc(cls, tvfunc, name, style):
        if tvfunc.name != name:
            raiseLess(ProgrammerError(
                f'Incompatible name - trying to add function "{tvfunc.name}" to overload "{name}"',
                ErrSite(cls, "#1")))
        if tvfunc.style != style:
            raiseLess(ProgrammerError(
                f'Incompatible style - trying to overload {tvfunc.dtyle} function "{tvfunc.name}" with existing {style} function "{name}"',
                ErrSite(cls, "#10")))



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
    if isinstance(x, Family):
        answer = []
        for overload in x._overloadByNumArgs:
            for sig, tvfunc in overload.items():
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

class _TBIQueue:
    def __init__(self):
        self._fns = []   # need a queue as potentially the parser could add more than one before types are inferred
    def __lshift__(self, f):   # self << f
        self._fns.append(f)
    def __contains__(self, f):
        return f in self._fns
    def remove(self, f):
        self._fns.remove(f)
    def __repr__(self):
        return f'<{", ".join([repr(e) for e in self._fns])}>'
    def __len__(self):
        return len(self._fns)
    # def first(self):
    #     return self._fns[0]
    def __iter__(self):
        return iter(self._fns)

