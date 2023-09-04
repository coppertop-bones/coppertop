# **********************************************************************************************************************
#
#                             Copyright (c) 2019-2022 David Briant. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
#
# **********************************************************************************************************************

import sys

if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

__all__ = [
    'coppertop', 'nullary', 'unary', 'binary', 'ternary', '_', 'sig', 'context', 'typeOf', 'makeFn', 'GROOT',
    'fitsWithin', 'type', 'fitsWithin_', 'SCRATCH'
]


import inspect, types, datetime, builtins, time
from collections import namedtuple

import coppertop._groot
coppertop.__version__ = "2023.03.21.1"
from bones import jones

# note: bones modules live in sys._bmodules which is created by coppertop/__init__.py

from bones.core.context import context
from coppertop._groot import BModule
from coppertop._scopes import _CoWProxy, _UNDERSCORE
from bones.core.errors import ProgrammerError, ErrSite, CPTBError
from bones.core.sentinels import Missing, function
from bones.core.utils import firstKey, raiseLess
from bones.lang.metatypes import BType, fitsWithin as origFitsWithin, cacheAndUpdate, BTFn, BTTuple, BTAtom, BTOverload, _BTypeById, _aliases
from bones.lang.types import nullary, unary, binary, ternary, void, obj
from bones.lang.select import _ppType, _selectFunction


py = BTAtom.ensure("py").setOrthogonal(obj)

if not hasattr(sys, '_CoppertopError'):
    class CoppertopError(CPTBError): pass
    sys._CoppertopError = CoppertopError
CoppertopError = sys._CoppertopError


hits = 0; misses = 0; hitTime1 = 0; hitTime2 = 0; missTime1 = 0; missTime2 = 0
searchTime = 0 ;dispatchTime = 0; dispatchCount = 0; returnTime = 0; returnCount = 0


_unhandledTypes = set()



SelectionResult = namedtuple('SelectionResult', ['d', 'tByT'])

_ = _UNDERSCORE
MANDATORY = inspect._empty    # this is the sentinel python uses to indicate that an argument has no default (i.e. is optional)
NO_ANNOTATION = inspect._empty    # this is the sentinel python uses to indicate that an argument has no annotation
BETTER_ERRORS = False
SCRATCH = 'scratch'
GROOT = ''
ANON_NAME = '<lambda>'

_SCTracker = []


jonesFnByStyle = {
    nullary: jones._nullary,
    unary: jones._unary,
    binary: jones._binary,
    ternary: jones._ternary,
}



def makeFn(*args):
    if len(args) == 1:
        name, _t, pyfn = ANON_NAME, Missing, args[0]
    elif len(args) == 2:
        name, _t, pyfn = ANON_NAME, args[0], args[1]
    elif len(args) == 3:
        name, _t, pyfn = args[0], args[1], args[2]
    else:
        raise TypeError('Wrong number of args passed to partial', ErrSite("#1"))
    bmodname, pymodname, fnname, priorMF, definedInFunction, argNames, sig, tRet, pass_tByT = _fnContext(pyfn, 'anon', name)
    if _t is Missing:
        _t = BTFn(BTTuple(*[py] * len(argNames)), py)
    bmodname = SCRATCH if bmodname is Missing else bmodname
    fn = _Function(
        name=fnname, bmodname=bmodname, pymodname=pymodname,
        style=unary, pyfn=pyfn, dispatchEvenIfAllTypes=False, typeHelper=Missing, _t=_t, argNames=argNames, pass_tByT=False
    )
    d = _Dispatcher(fn)
    return jones._unary(fnname, bmodname, d, _UNDERSCORE)



# the @coppertop decorator
def coppertop(*args, style=Missing, name=Missing, typeHelper=Missing, dispatchEvenIfAllTypes=False, module=Missing):

    def registerFn(pyfn):
        # answers a multifunction
        style_ = unary if style is Missing else style
        bmodname, pymodname, fnname, priorMF, definedInFunction, argNames, sig, tRet, pass_tByT = _fnContext(pyfn, 'registerFn', name)
        if len(argNames) < 1 and style_ == unary: raise CoppertopError(f'{fnname} has style unary but only has {len(argNames)} args : {argNames}')
        if len(argNames) < 2 and style_ == binary: raise CoppertopError(f'{fnname} has style binary but only has {len(argNames)} args: {argNames}')
        if len(argNames) < 3 and style_ == ternary: raise CoppertopError(f'{fnname} has style ternary but only has {len(argNames)} args: {argNames}')
        if module is not Missing:
            bmodname = module
        elif bmodname is Missing:
            if priorMF:
                # if we have imported a function and are extending it then use its bmodname
                if isinstance(priorMF.d, _Dispatcher):
                    for fnBySig in priorMF.d.fnBySigByNumArgs:
                        if fnBySig:
                            bmodname = firstKey(fnBySig.values()).bmodname
                            break
                else:
                    bmodname = priorMF.d.bmodname
            else:
                bmodname = SCRATCH

        # create dispatcher
        fn = _Function(fnname, bmodname, pymodname, style_, pyfn, dispatchEvenIfAllTypes, typeHelper, BTFn(sig, tRet), argNames, pass_tByT)

        # add it to the relevant jones function
        if definedInFunction:
            # create a new multifunction for use in this function
            # do not inherit any jones function not defined or imported into this module
            if module is not Missing:
                raiseLess(CoppertopError('Patching another module is disallowed within a function', ErrSite("#1")))
            if priorMF:
                d = _Dispatcher(priorMF.d, fn)
            else:
                d = _Dispatcher(fn)
            mf = jonesFnByStyle[style_](fnname, bmodname, d, _UNDERSCORE)
        else:
            if module is Missing and priorMF and isinstance(priorMF, jones._fn):
                d = _Dispatcher(priorMF.d, fn)
                mf = priorMF
            else:
                bmodule = sys._bmodules.get(bmodname, Missing)
                if bmodule is Missing:
                    bmodule = BModule(bmodname)
                    sys._bmodules[bmodname] = bmodule
                    if bmodname != GROOT:
                        splits = bmodname.split('.')
                        parentname = ''
                        for subname in splits:
                            if (parentmod := sys._bmodules.get(parentname, Missing)) is Missing:
                                parentmod = BModule(parentname)
                                sys._bmodules[parentname] = parentmod
                            modname = parentname + ('.' if parentname else '') + subname
                            if (mod := sys._bmodules.get(modname, Missing)) is Missing:
                                mod = BModule(modname)
                                sys._bmodules[modname] = mod
                            if subname not in parentmod.__dict__:
                                parentmod.__dict__[subname] = mod
                            else:
                                if not isinstance(parentmod.__dict__[subname], BModule): raise Exception("conflict")
                            parentname = modname
                mf = bmodule.__dict__.get(fnname, Missing)
                if mf is Missing:
                    d = _Dispatcher(fn)
                    mf = jonesFnByStyle[style_](fnname, bmodname, d, _UNDERSCORE)
                    bmodule.__dict__[fnname] = mf
                else:
                    d = _Dispatcher(mf.d, fn)
        mf.d = d
        return mf

    if len(args) == 1 and isinstance(args[0], (types.FunctionType, types.MethodType, builtins.type)):
        # of form @coppertop so args[0] is the function or callable class being decorated
        return registerFn(args[0])

    else:
        # of form as @coppertop() or @coppertop(overrideLHS=True) etc
        if len(args): raiseLess(TypeError('Only kwargs allowed', ErrSite("#2")))
        return registerFn


def _fnContext(pyfn, callerFnName, name=Missing):
    fnname = pyfn.__name__ if name is Missing else name
    # go up the stack to the frame where @coppertop is used to find any prior definition (e.g. import) of the function
    frame = inspect.currentframe()  # do not use `frameInfos = inspect.stack(0)` as it is much much slower
    # discard the frames for registerFn and coppertop
    if frame.f_code.co_name == '_fnContext':
        frame = frame.f_back
    if frame.f_code.co_name == callerFnName:
        frame = frame.f_back
    if frame.f_code.co_name == 'coppertop':  # depending on how coppertop was called this may or may not exist
        frame = frame.f_back
    if frame.f_code.co_name == '__ror__':  # e.g. (lambda...) | (T1^T2)
        frame = frame.f_back
    priorMF = frame.f_locals.get(fnname, Missing)
    if priorMF is Missing:
        priorMF = frame.f_globals.get(fnname, Missing)
    if not isinstance(priorMF, jones._fn):
        priorMF = Missing
    bmodname = frame.f_locals.get('MODULE_NS', Missing)
    if bmodname is Missing:
        bmodname = frame.f_globals.get('MODULE_NS', Missing)
    # fi_debug = inspect.getframeinfo(frame, context=0)
    pymodname = frame.f_globals.get('__name__', Missing)
    globals__package__ = frame.f_globals.get('__package__', Missing)
    # '<cell line: ' is what Jupyter displays at this point in the stack - OPEN: make more robust
    definedInFunction = frame.f_code.co_name != '<module>' and not frame.f_code.co_name.startswith('<cell line: ')
    fnSignature = inspect.signature(pyfn)
    tRet = _tArgFromAnnotation(fnSignature.return_annotation, bmodname, fnname, 'unhandled return type ')
    argNames = []
    sig = []
    pass_tByT = False
    for argName, parameter in fnSignature.parameters.items():
        if argName == 'tByT':
            pass_tByT = True
        else:
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                raiseLess(
                    TypeError(f'{pymodname}.{fnname} has *%s' % argName),
                    ErrSite("has VAR_POSITIONAL")
                )
            elif parameter.kind == inspect.Parameter.VAR_KEYWORD:
                raiseLess(
                    TypeError(f"Coppertop fns cannot have keyword arguments - {pymodname}.{fnname} has '%s'" % argName),
                    ErrSite("has VAR_KEYWORD")
                )
            else:
                if parameter.default == MANDATORY:
                    argNames += [argName]
                    tArg = _tArgFromAnnotation(parameter.annotation, pymodname, fnname, f'parameter {argName} has an unhandled argument type ')
                    sig.append(tArg)
                else:
                    raiseLess(
                        TypeError(
                            f"Coppertop fns cannot have optional arguments - {pymodname}.{fnname} arg '{argName}' has a default value"),
                        ErrSite("has VAR_KEYWORD")
                    )
    return bmodname, pymodname, fnname, priorMF, definedInFunction, argNames, sig, tRet, pass_tByT


def _tArgFromAnnotation(annotation, bmodname, fnname, msg):
    if isinstance(annotation, BType):
        return annotation
    elif annotation == NO_ANNOTATION:
        return py
    elif isinstance(annotation, builtins.type):
        if (tArg := _aliases.get(annotation, Missing)) is Missing:
            name = annotation.__module__ + "." + annotation.__name__
            tArg = BTAtom.ensure(name)
            _aliases[annotation] = tArg
        return tArg
    elif annotation in _unhandledTypes:
        raise TypeError(f'{bmodname}.{fnname} - {msg}{annotation}, use {_aliases[annotation]} instead', ErrSite("illegal argument type"))
    elif isinstance(annotation, str):
        raise TypeError(
            f'{bmodname}.{fnname} - {msg} str - has `from __future__ import annotations` been invoked in the module',
            ErrSite("illegal argument type")
        )
    else:
        raise TypeError(
            f'{bmodname}.{fnname} - {msg}{annotation}',
            ErrSite("illegal argument type")
        )



class _Function(object):

    __slots__ = [
        'style', 'name', '_t', 'bmodname', 'pymodname', 'pyfn', '_argNames', 'sig', 'tArgs', 'tRet',
        'pass_tByT', 'dispatchEvenIfAllTypes', 'typeHelper', '__doc__'
     ]

    def __init__(self, name, bmodname, pymodname, style, pyfn, dispatchEvenIfAllTypes, typeHelper, _t, argNames, pass_tByT):
        if not isinstance(_t, BTFn):
            0/1
        self.name = name
        self.bmodname = bmodname
        self.pymodname = pymodname
        self.style = style
        self.pyfn = pyfn
        self._argNames = argNames
        self._t = _t
        self.tArgs = _t.tArgs
        self.tRet = _t.tRet
        self.sig = _t.tArgs.types
        self.pass_tByT = pass_tByT
        self.dispatchEvenIfAllTypes = dispatchEvenIfAllTypes          # calls the function rather than returns the dispatch when all args are types
        self.typeHelper = typeHelper
        self.__doc__ = pyfn.__doc__ if hasattr(pyfn, '__doc__') else None

    @property
    def fullname(self):
        return self.bmodname + '.' + self.name

    @property
    def numargs(self):
        return len(self.sig)

    def _tPartial(self, o_tbc):
        return BTFn(BTTuple(*(self.sig[o] for o in o_tbc)), self.tRet)

    def __repr__(self):
        return self.name



class _Dispatcher(object):

    __slots__ = ['style', 'name', '_t_', 'fnBySigByNumArgs', 'cacheByNumArgs', '__doc__']

    def __new__(cls, *dispatchers):
        name = dispatchers[0].name
        style = dispatchers[0].style
        ds = []
        maxNumArgs = 0
        for d in dispatchers:
            if isinstance(d, _Dispatcher):
                if len(d.fnBySigByNumArgs) > maxNumArgs: maxNumArgs = len(d.fnBySigByNumArgs) - 1  # don't forget 0 args
            elif isinstance(d, _Function):
                if len(d.sig) > maxNumArgs: maxNumArgs = len(d.sig)
        fnBySigByNumArgs = [{} for i in range(maxNumArgs + 1)]
        for d in dispatchers:
            if isinstance(d, _Dispatcher):
                for fnBySig in d.fnBySigByNumArgs:
                    for d in fnBySig.values():
                        if isinstance(d, _Function):
                            if d.style != style:
                                raiseLess(TypeError(f'Expected {style} got {d.style}', ErrSite(cls, "#4")))
                            ds.append(d)
                        else:
                            raiseLess(ValueError("unknown dispatcher type", ErrSite(cls, "#5")))
            elif isinstance(d, _Function):
                if d.name != name:
                    raise ProgrammerError(ErrSite(cls, "#9"))
                if d.style != style:
                    raiseLess(TypeError(f'When processing @coppertop for function {name} - expected style={style} got {d.style}', ErrSite(cls, "#10")))
                ds.append(d)
            else:
                raiseLess(ProgrammerError("unhandled dispatcher class", ErrSite(cls, "#11")))
        for d in ds:
            oldD = fnBySigByNumArgs[len(d.sig)].get(d.sig, Missing)
            # if oldD is not Missing and oldD.bmodname != d.bmodname:
            #     raise CoppertopError(f'Found definition of {_ppFn(name, d.sig)} in "{d.bmodname}" and "{oldD.bmodname}"', ErrSite(cls, "#12"))
            # if oldD is not Missing and oldD.pymodname != d.pymodname:
            #     raise CoppertopError(f'Found definition of {_ppFn(name, d.sig)} in "{d.pymodname}" and "{oldD.pymodname}"', ErrSite(cls, "#12"))
            fnBySigByNumArgs[len(d.sig)][d.sig] = d
        # if len(fnBySigByNumArgs) == 1 and len(fnBySigByNumArgs[0]) == 1:
        #     # this can occur in a REPL where a function is being redefined
        #     # SHOULDDO think this through as potentially we could overload functions in the repl accidentally which
        #     #  would be profoundly confusing
        #     return d
        instance = super().__new__(cls)
        instance.name = name
        instance.style = style
        instance.fnBySigByNumArgs = fnBySigByNumArgs
        instance.cacheByNumArgs = [Missing] * (maxNumArgs + 1)
        instance._t_ = Missing
        instance.__doc__ = None
        return instance

    def selectFn(self, args):
        numArgs = len(args)
        if numArgs == 0:
            fn = self.fnBySigByNumArgs[0][()]
            tByT = {}
            hasValue = True
        else:
            # ensure we have a cache
            if (cache := self.cacheByNumArgs[numArgs]) is Missing:
                pSC = jones.sc_new(numArgs, 100)
                cache = self.cacheByNumArgs[numArgs] = (pSC, [])
                _SCTracker.append((self, numArgs, pSC))
            pSC, results = cache

            hasValue = jones.sc_fillQuerySlotWithBTypesOf(pSC, args, _aliases, py, _CoWProxy)

            # t2 = time.perf_counter_ns()
            resultId = jones.sc_getFnId(pSC)
            # t3 = time.perf_counter_ns()

            if resultId == 0:
                # missTime1 += t2 - t1; missTime2 += t3 - t2; misses += 1
                tArgs = jones.sc_tArgsFromQuery(pSC, _BTypeById)
                fn, tByT = _selectFunction(tArgs, self.fnBySigByNumArgs[numArgs], self.name, self.fnBySigByNumArgs)
                results.append((fn, tByT))
                pQuery = jones.scQueryPtr(pSC)
                iNext = jones.scNextFreeArrayIndex(pSC)
                if iNext == 0:
                    raise RuntimeError("Array not big enough")
                jones.scAtArrayPut(pSC, iNext, pQuery, len(results))
                # searchTime += time.perf_counter_ns() - t3; dispatchTime += t3 - t1
            else:
                # hitTime1 += t2 - t1; hitTime2 += t3 - t2; hits += 1; dispatchTime += t3 - t1
                fn, tByT = results[resultId - 1]
        return fn, tByT, hasValue

    def __call__(self, *args):
        # global hits, misses, hitTime1, hitTime2, missTime1, missTime2, searchTime, dispatchTime, dispatchCount, returnTime, returnCount
        # t1 = time.perf_counter_ns()

        fn, tByT, hasValue = self.selectFn(args)

        # t4 = time.perf_counter_ns()

        if hasValue or fn.dispatchEvenIfAllTypes:
            if fn.pass_tByT:
                if fn.typeHelper:
                    tByT = fn.typeHelper(*args, tByT=tByT)
                # dispatchTime += time.perf_counter_ns() - t4; dispatchCount += 1
                answer = fn.pyfn(*args, tByT=tByT)
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
                        answer = fn.pyfn(*args)
                        # t5 = time.perf_counter_ns()
                    except TypeError as ex:
                        if ex.args and ' required positional argument' in ex.args[0]:
                            print(_sig(fn), file=sys.stderr)
                            print(ex.args[0], file=sys.stderr)
                        raiseLess(ex, True)
                        # argTs = [_ppType(argT) for argT in args]
                        # retT = _ppType(x.tRet)
                        # return f'({",".join(argTs)})->{retT} <{x.style.name}>  :   in {x.fullname}'
                else:
                    # dispatchTime += time.perf_counter_ns() - t4; dispatchCount += 1
                    answer = fn.pyfn(*args)
                    # t5 = time.perf_counter_ns()
            tRet = fn.tRet
            if tRet == py or isinstance(answer, SelectionResult):
                # returnTime += time.perf_counter_ns() - t5; returnCount += 1
                return answer
            else:
                # MUSTDO
                # BTTuples are products whereas pytuples are exponentials therefore we can reliably type check an answered
                # sequence if the return type is BTTuple (and possibly BTStruct) - also BTTuple can be coerced by default to
                # a dseq (or similar - may should add a new tuple subclass to prevent it being treated like an exponential)
                # add a note in bones that one of our basic ideas / building blocks is things and exponentials of things
                doesFit, tByT, distances = cacheAndUpdate(origFitsWithin(_typeOf(answer), tRet), tByT)
                if doesFit:
                    # returnTime += time.perf_counter_ns() - t5; returnCount += 1
                    return answer
                else:                    raiseLess(TypeError(
                        f'{fn.fullname} returned a {str(_typeOf(answer))} should have have returned a {fn.tRet} {tByT}',
                        ErrSite("#1")))
        else:
            # dispatchTime += time.perf_counter_ns() - t4; dispatchCount += 1
            return SelectionResult(fn, tByT)


    def _tPartial(self, num_args, o_tbc):
        # if this is a bottle neck can be cached
        ts = []
        for fn in self.fnBySigByNumArgs[num_args].values():
            ts.append(fn._tPartial(o_tbc))
        return BTOverload(*ts)

    @property
    def _t(self):
        if self._t_ is Missing:
            ts = []
            for fnBySig in self.fnBySigByNumArgs:
                for fn in fnBySig.values():
                    ts.append(fn._t)
            self._t_ = BTOverload(*ts)
        return self._t_

    def __repr__(self):
        return self.name


def _typeOf(x):
    if hasattr(x, '_t'):
        return x._t                     # it's a tv of some sort so return the t
    elif isinstance(x, jones._fn):
        return x.d._t
    elif isinstance(x, jones._pfn):
        return x.d._tPartial(x.num_args, x.o_tbc)
    else:
        t = builtins.type(x)
        if t is _CoWProxy:
            t = builtins.type(x._target)         # return the type of thing being proxied
        return _aliases.get(t, t)       # type python types as their bones equivalent


def _sig(x):
    if isinstance(x, function):
        return f'{x.__name__} is a Python function'
    x = x.d
    if isinstance(x, _Dispatcher):
        answer = []
        for fnBySig in x.fnBySigByNumArgs:
            for sig, d in fnBySig.items():
                argTs = [_ppType(argT) for argT in sig]
                retT = _ppType(d.tRet)
                answer.append(f'({",".join(argTs)})->{retT} <{d.style.name}>  :   in {d.fullname}')
        return answer
    else:
        argTs = [_ppType(argT) for argT in x.sig]
        retT = _ppType(x.tRet)
        return f'({",".join(argTs)})->{retT} <{x.style.name}>  :   in {x.fullname}'


def _fitsWithin(a, b):
    doesFit, tByT, distances = cacheAndUpdate(origFitsWithin(a, b), {})
    return doesFit

def _fitsWithin_(a, b):
    x = origFitsWithin(a, b)
    cacheAndUpdate(x, {})
    return x

def _type(x):
    return builtins.type(x)

# public functions
typeOf = coppertop(name='typeOf', dispatchEvenIfAllTypes=True, module=GROOT)(_typeOf)
sig = coppertop(name='sig', module=GROOT)(_sig)
fitsWithin = coppertop(name='fitsWithin', style=binary, dispatchEvenIfAllTypes=True, module=GROOT)(_fitsWithin)
fitsWithin_ = coppertop(name='fitsWithin_', style=binary, dispatchEvenIfAllTypes=True, module=GROOT)(_fitsWithin_)
type = coppertop(name='type', dispatchEvenIfAllTypes=True, module=GROOT)(_type)



if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__ + ' - done')
