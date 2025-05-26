# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

# ## @coppertop and import semantics
#
# Overloads are not a global concept. They are created locally when two or more functions in a scope share the same
# name. In bones the compiler can add concrete implementations when it encounters a template.
#
# However, in Python we can't hook this so we keep an uber overload that includes the kitchen sink so to speak - e.g. PP
# might be used generically or within a template, and additionally we have to handle cases where the type is unknown
# since Python is a dynamic language. We keep the uber overload in its own module virtually named `_`. E.g.
# `from _ import PP` will import the uber overload of PP. A function implementation may opt out of being added to the
# uber overload for example to allow `verbose.PP` and `terse.PP` to be used to distinguish differences where the
# arguments have the same type or it make code more readable. E.g. dm.linalg.numpyimp and dm.linalg.playimp might be
# used to switch a whole implementation or dm.csv.read and dm.xls.read might read better in context.
#
#
# in modules:
#
# @coppertop updates the function in the:
#   - Python module creating an overload with anything already present - this should make sense for Python programmers
#   - corresponding bones module - so that we have to explicitly share bones and Python functions
#   - the global root unless otherwise stated
#
# import:
#   - normal imports override as per normal Python - thus don't update the shared module (which might be inefficient
#     as it might not be needed)
#   - from _.x.y import z overloads z in the Python (and bones module?)
#   - from _ import x gets the uber overload x  - it doesn't need to do anything else as
#
#
# in functions:
# `from _ import ...` and `from _.x.y import z` are not implemented but might be given further evidence of need
# @coppertop does not update any bones modules and only creates a local overload
#
# module name - __main__ is mapped to scratch and otherwise it is the python module name
# redefinition - except in scratch where it is normal redefinition of a function throws an error - need to add
#                withoutSig function
#
# NOTES:
# - only the uber overload for is mutated
#
# OPEN:
# - overload count the type (including schema variables) and count the function and ideally count the module
# - can bones see the Python uber fns? can a call from Python trigger a new function being built? TBC


import sys

if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

__all__ = [
    'coppertop', 'nullary', 'unary', 'binary', 'ternary', '_', 'sig', 'context', 'typeOf', 'makeFn',
    'fitsWithin', 'type', 'SCRATCH'
]


import inspect, types, builtins
from collections import namedtuple

import coppertop
coppertop.__version__ = "2024.03.08.1"
from bones import jones

from bones.core.context import context
from coppertop._scopes import _CoWProxy, _UNDERSCORE
from bones.core.errors import ProgrammerError, ErrSite, CPTBError, NotYetImplemented
from bones.core.sentinels import Missing, function
from bones.core.utils import raiseLess
from bones.ts.metatypes import BType, fitsWithin as origFitsWithin, BTFn, BTTuple, BTAtom, \
    BTOverload, _BTypeById, _btypeByClass
from bones.lang.types import nullary, unary, binary, ternary
from coppertop._select import _ppType, _selectFunction
from bones.jones import BTypeError


py = BType('py: atom in mem')

class CoppertopError(CPTBError): pass
class CoppertopImportError(ImportError): pass

class BModule(types.ModuleType):
    def __repr__(self):
        return f'BModule({self.__name__})'

    def __getattribute__(self, name):
        try:
            answer = super().__getattribute__(name)
        except AttributeError as ex:
            raise AttributeError(
                f'bones module "{self.__name__}" has no attribute "{name}" - maybe it\'s defined in a python module '
                f'that needs to be imported'
            ) from None
        return answer

# NOTE: bones modules live in sys._bmodules
sys._bmodules = {'': BModule('')}


# for profiling
# hits = 0; misses = 0; hitTime1 = 0; hitTime2 = 0; missTime1 = 0; missTime2 = 0
# searchTime = 0 ;dispatchTime = 0; dispatchCount = 0; returnTime = 0; returnCount = 0

# OPEN: do we still need this?
_unhandledTypes = set()

SelectionResult = namedtuple('SelectionResult', ['d', 'tByT'])

_ = _UNDERSCORE
MANDATORY = inspect._empty      # Python sentinel to indicate an argument has no default (i.e. is not optional)
NO_ANNOTATION = inspect._empty  # Python sentinel to indicate an argument has no annotation
BETTER_ERRORS = False
SCRATCH = 'scratch'

# OPEN: do we still need this?
_SCTracker = []

jonesFnByStyle = {
    nullary: jones._nullary,
    unary: jones._unary,
    binary: jones._binary,
    ternary: jones._ternary,
}



# **********************************************************************************************************************
# DECORATOR
# **********************************************************************************************************************

def coppertop(*args, style=Missing, name=Missing, typeHelper=Missing, dispatchEvenIfAllTypes=False, local=False):

    def registerFn(pyfn):
        # answer a jones fn (i.e. that can be partialed, piped or called) that may contain an overload
        style_ = unary if style is Missing else style
        updateUber = not local
        modname, bmod, umod, fnname, pymodFn, enclosingFnName, argNames, sig, tRet, pass_tByT = _fnContext(pyfn, 'registerFn', name)

        fn = _Function(fnname, modname, style_, pyfn, dispatchEvenIfAllTypes, typeHelper, BTFn(sig, tRet), argNames, pass_tByT)

        # run some checks - establishing that pymodFn is a jones function with the congruent piping style
        if pymodFn:
            if isinstance(pymodFn, jones._fn):
                _checkStyleAndNumArgs(style_, pymodFn, fnname, argNames)
            else:
                if modname == SCRATCH:
                    pymodFn = Missing
                else:
                    raise Exception(f'Replacing "{fnname}", which not a jones fn, with a jones fn is not allowed')
        if (bmodFn := bmod.__dict__.get(fnname, Missing)): _checkStyleAndNumArgs(style_, bmodFn, fnname, argNames)
        if (uberFn := umod.__dict__.get(fnname, Missing)): _checkStyleAndNumArgs(style_, uberFn, fnname, argNames)

        # figure exact what to update
        if enclosingFnName:
            if pymodFn is Missing:
                return jonesFnByStyle[style_](fnname, modname + '.' + enclosingFnName, _Dispatcher(fn), _UNDERSCORE)
            else:
                return jonesFnByStyle[style_](fnname, modname + '.' + enclosingFnName, _Dispatcher(pymodFn.d, fn), _UNDERSCORE)
        else:
            if pymodFn is Missing:
                if bmodFn is Missing:
                    if uberFn is Missing:
                        jf = jonesFnByStyle[style_](fnname, modname, _Dispatcher(fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jf
                        if updateUber: umod.__dict__[fnname] = jonesFnByStyle[style_](fnname, '_', _Dispatcher(fn), _UNDERSCORE)
                        return jf
                    else:
                        jf = jonesFnByStyle[style_](fnname, modname, _Dispatcher(fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jf
                        if updateUber: umod.__dict__[fnname].d = _Dispatcher(uberFn.d, fn)
                        return jf
                else:
                    if uberFn is Missing:
                        jf = jonesFnByStyle[style_](fnname, modname, _Dispatcher(fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jonesFnByStyle[style_](fnname, modname, _Dispatcher(bmodFn.d, fn), _UNDERSCORE)
                        if updateUber: umod.__dict__[fnname] = jonesFnByStyle[style_](fnname, '_', _Dispatcher(fn), _UNDERSCORE)
                        return jf
                    else:
                        jf = jonesFnByStyle[style_](fnname, modname, _Dispatcher(fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jonesFnByStyle[style_](fnname, modname, _Dispatcher(bmodFn.d, fn), _UNDERSCORE)
                        if updateUber: umod.__dict__[fnname].d = _Dispatcher(uberFn.d, fn)
                        return jf
            else:
                if bmodFn is Missing:
                    if uberFn is Missing:
                        jf = jonesFnByStyle[style_](fnname, modname, _Dispatcher(pymodFn.d, fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jf
                        if updateUber: umod.__dict__[fnname] = jonesFnByStyle[style_](fnname, '_', _Dispatcher(pymodFn.d, fn), _UNDERSCORE)
                        return jf
                    else:
                        jf = jonesFnByStyle[style_](fnname, modname, _Dispatcher(pymodFn.d, fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jf
                        if updateUber: umod.__dict__[fnname].d = _Dispatcher(uberFn.d, jf.d)
                        return jf
                else:
                    if uberFn is Missing:
                        jf = jonesFnByStyle[style_](fnname, modname, _Dispatcher(pymodFn.d, fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jonesFnByStyle[style_](fnname, modname, _Dispatcher(bmodFn.d, jf.d), _UNDERSCORE)
                        if updateUber: umod.__dict__[fnname] = jonesFnByStyle[style_](fnname, '_', _Dispatcher(pymodFn.d, fn), _UNDERSCORE)
                        return jf
                    else:
                        jf = jonesFnByStyle[style_](fnname, modname, _Dispatcher(pymodFn.d, fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jonesFnByStyle[style_](fnname, modname, _Dispatcher(bmodFn.d, jf.d), _UNDERSCORE)
                        if updateUber: umod.__dict__[fnname].d = _Dispatcher(uberFn.d, jf.d)
                        return jf


    if len(args) == 1 and isinstance(args[0], (types.FunctionType, types.MethodType, builtins.type)):
        # of form @coppertop so args[0] is the function or callable class being decorated
        return registerFn(args[0])

    else:
        # of form as @coppertop() or @coppertop(overrideLHS=True) etc
        if len(args): raiseLess(TypeError('Only kwargs allowed', ErrSite("#2")))
        return registerFn


def _styleOfFn(fn):
    if isinstance(fn, (jones._nullary, jones._pnullary)): return nullary
    elif isinstance(fn, (jones._unary, jones._punary)): return unary
    elif isinstance(fn, (jones._binary, jones._pbinary)): return binary
    elif isinstance(fn, (jones._pternary, jones._ternary)): return ternary
    else: return Missing

def _checkStyleAndNumArgs(style, fn, fnname, argNames):
    fnStyle = _styleOfFn(fn)
    if fn and fnStyle != style: raise CoppertopError(f'Current {fnname} is a {fnStyle} but the new function is a {style}')
    if len(argNames) < 1 and style == unary: raise CoppertopError(f'{fnname} has style unary but only has {len(argNames)} args ({", ".join(argNames)})')
    if len(argNames) < 2 and style == binary: raise CoppertopError(f'{fnname} has style binary but only has {len(argNames)} args ({", ".join(argNames)})')
    if len(argNames) < 3 and style == ternary: raise CoppertopError(f'{fnname} has style ternary but only has {len(argNames)} arg ({", ".join(argNames)})')

def _getBModuleForName(modname):
    bmodule = sys._bmodules.get(modname, Missing)
    if bmodule is Missing:
        bmodule = BModule(modname)
        sys._bmodules[modname] = bmodule
        splits = modname.split('.')
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
    return bmodule

def _fnContext(pyfn, callerFnName, name):
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
    # if name is given do some checks
    fnname = pyfn.__name__
    if name:
        if name == fnname: raise CoppertopError('In order to reduce accidental errors it is not allowed to name a function as itself')
        fnname = name
    priorX = frame.f_locals.get(fnname, Missing)
    if priorX is Missing: priorX = frame.f_globals.get(fnname, Missing)
    modname = frame.f_globals.get('__name__', Missing)
    if modname is Missing: raise CoppertopError('frame has no __name__')
    if modname == '__main__': modname = SCRATCH
    # fi_debug = inspect.getframeinfo(frame, context=0)
    globals__package__ = frame.f_globals.get('__package__', Missing)
    # '<cell line: ' is what Jupyter displays at this point in the stack - OPEN: make more robust
    enclosingFnName = frame.f_code.co_name if (frame.f_code.co_name != '<module>' and not frame.f_code.co_name.startswith('<cell line: ')) else Missing
    fnSignature = inspect.signature(pyfn)
    tRet = _tArgFromAnnotation(fnSignature.return_annotation, modname, fnname, 'unhandled return type ')
    argNames = []
    sig = []
    pass_tByT = False
    for argName, parameter in fnSignature.parameters.items():
        if argName == 'tByT':
            pass_tByT = True
        else:
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                raiseLess(
                    TypeError(f'{modname}.{fnname} has *%s' % argName),
                    ErrSite("has VAR_POSITIONAL")
                )
            elif parameter.kind == inspect.Parameter.VAR_KEYWORD:
                raiseLess(
                    TypeError(f"Coppertop fns cannot have keyword arguments - {modname}.{fnname} has '%s'" % argName),
                    ErrSite("has VAR_KEYWORD")
                )
            else:
                if parameter.default == MANDATORY:
                    argNames += [argName]
                    tArg = _tArgFromAnnotation(parameter.annotation, modname, fnname, f'parameter {argName} has an unhandled argument type ')
                    sig.append(tArg)
                else:
                    raiseLess(
                        TypeError(
                            f"Coppertop fns cannot have optional arguments - {modname}.{fnname} arg '{argName}' has a default value"),
                        ErrSite("has VAR_KEYWORD")
                    )
    return modname, _getBModuleForName('_.' + modname), _getBModuleForName('_'), fnname, priorX, enclosingFnName, argNames, sig, tRet, pass_tByT

def _tArgFromAnnotation(annotation, modname, fnnameForErr, msgForErr):
    if isinstance(annotation, BType):
        return annotation
    elif annotation == NO_ANNOTATION:
        return py
    elif isinstance(annotation, builtins.type):
        if (tArg := _btypeByClass.get(annotation, Missing)) is Missing:
            name = annotation.__module__ + "." + annotation.__name__
            tArg = BTAtom(name)
            _btypeByClass[annotation] = tArg
        return tArg
    elif annotation in _unhandledTypes:
        raise TypeError(f'{modname}.{fnnameForErr} - {msgForErr}{annotation}, use {_btypeByClass[annotation]} instead', ErrSite("illegal argument type"))
    elif isinstance(annotation, str):
        raise TypeError(
            f'{modname}.{fnnameForErr} - {msgForErr} str - has `from __future__ import annotations` been invoked in the module',
            ErrSite("illegal argument type")
        )
    else:
        raise TypeError(
            f'{modname}.{fnnameForErr} - {msgForErr}{annotation}',
            ErrSite("illegal argument type")
        )



# **********************************************************************************************************************
# Dispatch
# **********************************************************************************************************************

class _Function:

    __slots__ = [
        'style', 'name', '_t', 'modname', 'pyfn', '_argNames', 'sig', 'tArgs', 'tRet',
        'pass_tByT', 'dispatchEvenIfAllTypes', 'typeHelper', '__doc__'
     ]

    def __init__(self, name, modname, style, pyfn, dispatchEvenIfAllTypes, typeHelper, _t, argNames, pass_tByT):
        if not isinstance(_t, BTFn): raise TypeError('_t is not a BTFn')
        self.name = name
        self.modname = modname
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
        return self.modname + '.' + self.name

    @property
    def numargs(self):
        return len(self.sig)

    def _tPartial(self, o_tbc):
        return BTFn(BTTuple(*(self.sig[o] for o in o_tbc)), self.tRet)

    def __repr__(self):
        return self.name


class _Dispatcher:

    __slots__ = ['style', 'name', '_t_', 'fnBySigByNumArgs', 'cacheByNumArgs', '__doc__']

    def __new__(cls, *dispatchers):
        name = dispatchers[0].name
        style = dispatchers[0].style
        ds = []
        maxNumArgs = 0

        for d in dispatchers:
            if isinstance(d, _Dispatcher):
                for fnBySig in d.fnBySigByNumArgs:
                    for d2 in fnBySig.values():
                        if isinstance(d2, _Function):
                            cls._checkDispatcher(d2, name, style)
                            ds.append(d2)
                        else:
                            raiseLess(ProgrammerError("unknown dispatcher class", ErrSite(cls, "#5")))
                if len(d.fnBySigByNumArgs) > maxNumArgs: maxNumArgs = len(d.fnBySigByNumArgs) - 1  # don't forget 0 args
            elif isinstance(d, _Function):
                cls._checkDispatcher(d, name, style)
                if len(d.sig) > maxNumArgs: maxNumArgs = len(d.sig)
                ds.append(d)
            else:
                raiseLess(ProgrammerError("unhandled dispatcher class", ErrSite(cls, "#11")))

        fnBySigByNumArgs = [{} for i in range(maxNumArgs + 1)]
        for d in ds:
            oldD = fnBySigByNumArgs[len(d.sig)].get(d.sig, Missing)
            # if oldD is not Missing and oldD.modname != d.modname:
            #     raise CoppertopError(f'Found definition of {_ppFn(name, d.sig)} in "{d.modname}" and "{oldD.modname}"', ErrSite(cls, "#12"))
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

    @classmethod
    def _checkDispatcher(cls, d, name, style):
        if d.name != name:
            raiseLess(ProgrammerError(
                f'Incompatible name - trying to overload function "{d.name}" with existing function "{name}"',
                ErrSite(cls, "#1")))
        if d.style != style:
            raiseLess(ProgrammerError(
                f'Incompatible style - tyring to overload {d.dtyle} function "{d.name}" with existing {style} function "{name}"',
                ErrSite(cls, "#10")))

    def selectFn(self, args):
        numArgs = len(args)
        if numArgs == 0:
            fn = self.fnBySigByNumArgs[0][()]
            tByT = {}
            hasValue = True
        else:
            # ensure we have a cache
            if numArgs > len(self.cacheByNumArgs) - 1:
                raise TypeError(f"Too many args passed to  {self.name} - max {len(self.cacheByNumArgs) - 1}, passed {numArgs}")
            if (cache := self.cacheByNumArgs[numArgs]) is Missing:
                pSC = jones.sc_new(numArgs, 100)
                cache = self.cacheByNumArgs[numArgs] = (pSC, [])
                _SCTracker.append((self, numArgs, pSC))
            pSC, results = cache

            hasValue = jones.sc_fillQuerySlotWithBTypesOf(pSC, args, _btypeByClass, py, _CoWProxy)

            # t2 = time.perf_counter_ns()
            resultId = jones.sc_getFnId(pSC)
            # t3 = time.perf_counter_ns()

            if resultId == 0:
                # missTime1 += t2 - t1; missTime2 += t3 - t2; misses += 1
                tArgs = jones.sc_tArgsFromQuery(pSC, _BTypeById)
                fn, tByT = _selectFunction(tArgs, self.fnBySigByNumArgs[numArgs], self.name, self.fnBySigByNumArgs)
                results.append((fn, tByT))
                pQuery = jones.sc_queryPtr(pSC)
                iNext = jones.sc_nextFreeArrayIndex(pSC)
                if iNext == 0:
                    raise RuntimeError("Array not big enough")
                jones.sc_atArrayPut(pSC, iNext, pQuery, len(results))
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
                ret = fn.pyfn(*args, tByT=tByT)
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
                        ret = fn.pyfn(*args)
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
                    ret = fn.pyfn(*args)
                    # t5 = time.perf_counter_ns()
            tRet = fn.tRet
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
                        if origFitsWithin(ret._t, tRet):
                            return ret
                        else:
                            raiseLess(BTypeError(f'{fn.fullname} returned a {str(_typeOf(ret))} should have have returned a {tRet} {tByT}',ErrSite("#1")))
                    else:
                        return ret | tRet
                else:
                    # use the coercer rather than impose construction with tv
                    if origFitsWithin(typeOf(ret), tRet):
                        return ret
                    else:
                        return ret | tRet

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
    else:
        t = builtins.type(x)
        if t is _CoWProxy:
            t = builtins.type(x._target)         # return the type of thing being proxied
        return _btypeByClass.get(t, t)       # type python types as their bones equivalent

sys._typeOf = _typeOf               # required by coercion - do not remove

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



# **********************************************************************************************************************
# IMPORT HOOK
# **********************************************************************************************************************

# We wish to allow overloads to be created by importing jones functions into the same module. Normally Python overrides
# prior exisiting names. For example if we do `from a import fred` followed by `from b import fred` the second fred
# would replace the first `fred`. Instead we want to create an overload of the two `fred`s.
#
# To make our method standout in Python code we introduce the _ module, e.g. `from a import fred` followed by
# `from _.b import fred` alerts us that something unusual is happening. In the list follow the `import` token we check
# that each name refers to a JonesFn. We then create the overloads and return them in a new temporary module to the
# caller.

def _importFromBonesModule(frombmodName, frombmod, tobmodname, tobmod, importersGlobals, namesToImport):
    # we rely on the @coppertop decorator to have already handled the uberFn
    thingsToImport = {}
    for n in namesToImport:
        pymodJf = importersGlobals.get(n, Missing)
        current = tobmod.__dict__.get(n, Missing)
        if (addition := frombmod.__dict__.get(n, Missing)) is Missing:
            raise CoppertopImportError(f'"{n}" does not exisit in bones module "{frombmodName}"')
        if frombmodName == '_':
            # importing an uberFn implies we want everything
            thingsToImport[n] = addition
        elif pymodJf is Missing:
            if not isinstance(addition, (jones._fn, jones._pfn)) and not isinstance(addition, BType):
                raise CoppertopImportError(f'Trying to import "{n}" which is a {type(addition)}')
            if current is Missing:
                tobmod.__dict__[n] = addition.__class__(n, tobmodname, _Dispatcher(addition.d), _UNDERSCORE)
            else:
                tobmod.__dict__[n] = current.__class__(n, tobmodname, _Dispatcher(current.d, addition.d), _UNDERSCORE)
            thingsToImport[n] = addition
        elif isinstance(pymodJf, (jones._fn, jones._pfn)):
            if isinstance(addition, (jones._fn, jones._pfn)):
                # overload current and addition
                if current is Missing:
                    tobmod.__dict__[n] = addition.__class__(n, tobmodname, _Dispatcher(addition.d), _UNDERSCORE)
                    thingsToImport[n] = addition.__class__(n, tobmodname, _Dispatcher(pymodJf.d, addition.d), _UNDERSCORE)
                else:
                    if _styleOfFn(current) != _styleOfFn(addition):
                        raise CoppertopImportError(f'"{n} is a {_styleOfFn(current)} in {tobmodname} but a {_styleOfFn(addition)} in {frombmodName}')
                    tobmod.__dict__[n] = current.__class__(n, tobmodname, _Dispatcher(current.d, addition.d), _UNDERSCORE)
                    thingsToImport[n] = current.__class__(current.name, tobmodname, _Dispatcher(pymodJf.d, addition.d), _UNDERSCORE)
            elif isinstance(addition, BType):
                raise NotYetImplemented("overloading type and jonesFn")
            else:
                raise CoppertopImportError(f'Trying to import "{n}", which is a {type(addition)} to overwrite a {type(current)}!!!')
        elif isinstance(current, BType):
            if isinstance(addition, (jones._fn, jones._pfn)):
                raise NotYetImplemented("overloading type and jonesFn")
            elif isinstance(addition, BType):
                # no need to import anything but just check they are the same
                if current._id != addition._id: raise CoppertopImportError(f"Type {n} is different in {frombmodName}")
            else:
                raise CoppertopImportError(f'Trying to import "{n}", which is a {type(addition)} to overwrite a {type(current)}!!!')
        else:
            raise CoppertopImportError(f'"{n}" is not a jones function nor a jones type')

    newMod = BModule(name="_importFromBonesModule")
    newMod.__dict__.update(thingsToImport)
    return newMod


def _coppertopImportFn(name, globals=None, locals=None, fromlist=(), level=0):
    if (splits := name.split('.', maxsplit=1))[0] == '_':
        # print(f"{globals['__name__'].ljust(40)}: name: {name}, len(locals): {len(locals) if locals else 0}, fromList: {fromlist}, level: {level}")
        if not fromlist:
            raise CoppertopImportError("_ is a virtual package that cannot be imported and has no importable submodules - usage is 'from _.x.y import z'")
        if (frombmod := sys._bmodules.get(name, Missing)) is Missing:
            sys._preCoppertopImportFn(splits[1], globals, locals, fromlist, level)
            frombmod = sys._bmodules.get(name, Missing)
        namesToImport = fromlist
        if namesToImport[0] == '*':
            namesToImport = []
            for k, fn in frombmod.__dict__.items():
                if isinstance(fn, (jones._nullary, jones._unary, jones._binary, jones._ternary)):
                    namesToImport.append(k)
        if globals['__name__'] == '__main__':
            tobmodname = SCRATCH
            tobmod = sys._bmodules.get(SCRATCH, Missing)
        else:
            tobmodname = '_.' + globals['__name__']
            tobmod = sys._bmodules.get(tobmodname, Missing)
        return _importFromBonesModule(name, frombmod, tobmodname, tobmod, globals, namesToImport)
    else:
        mod = sys._preCoppertopImportFn(name, globals, locals, fromlist, level)
        return mod

sys._coppertopImportFn = _coppertopImportFn

if not hasattr(sys, '_coppertopImportFnHolder'):
    def _coppertopImportFnHolder(name, globals=None, locals=None, fromlist=(), level=0):
        return sys._coppertopImportFn(name, globals, locals, fromlist, level)
    sys._preCoppertopImportFn = builtins.__import__
    builtins.__import__ = _coppertopImportFnHolder



# **********************************************************************************************************************
# essential public functions - put into bones.core?
# **********************************************************************************************************************

@coppertop(style=binary, dispatchEvenIfAllTypes=True)
def fitsWithin(a, b):
    return origFitsWithin(a, b)

def makeFn(*args):
    if len(args) == 1:
        name, _t, pyfn = Missing, Missing, args[0]
    elif len(args) == 2:
        name, _t, pyfn = Missing, args[0], args[1]
    elif len(args) == 3:
        name, _t, pyfn = args[0], args[1], args[2]
    else:
        raise TypeError('Wrong number of args passed to partial', ErrSite("#1"))
    modname, bmod, umod, fnname, priorPy, enclosingFnName, argNames, sig, tRet, pass_tByT = _fnContext(pyfn, 'anon', name)
    if _t is Missing:
        _t = BTFn(BTTuple(*[py] * len(argNames)), py)
    fn = _Function(
        name=fnname, modname=modname,
        style=unary, pyfn=pyfn, dispatchEvenIfAllTypes=False, typeHelper=Missing, _t=_t, argNames=argNames, pass_tByT=False
    )
    d = _Dispatcher(fn)
    return jones._unary(fnname, modname, d, _UNDERSCORE)

@coppertop
def sig(x):
    return _sig(x)

@coppertop(dispatchEvenIfAllTypes=True)
def type(x):
    return builtins.type(x)

@coppertop(dispatchEvenIfAllTypes=True)
def typeOf(x):
    return _typeOf(x)



if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__ + ' - done')
