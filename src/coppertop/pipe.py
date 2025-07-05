# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

#  changes to import semantics when using coppertop-bones
#
# - experience shows that mutating overloads makes a system hard to reason about as extending an overload can change
#   which function is called on dispatch. I don't know if Julia or Clojure mutate overloads but we do not do this in
#   coppertop-bones (having tried it)
#
# - we have two options for syntax, detect JFuncs in a normal python import or use a special import syntax, i.e.
#   `from x.y import z` or `from _.x.y import z`.
#
# - we've currently implemented the latter to make the fact explicit we are doing something unusual. However:
#   - it is easy to forget to use the underscore,
#   - we want to be able to import a Python function from bones and a bones function from Python the underscore causes
#     us to have to think about import syntax is a clunky way,
#   so we might change this, with the cost that we then are hooking every import and may need to be more careful.
#
# - there is one use case where mutation of an overload is valid - when we have a schema and want to add a concrete
#   implementation. To keep things sane we will only mutate the actual overload that calls the function with the schema,
#   caching the concrete generated implementation in case it is needed again by another overload.
#
#  - the case for uber overloads was to allow an implementation to be changed behind the scenes, e.g. one could do
#    `import coppertop.dm.linalg.numpyimp` or `import coppertop.dm.linalg.bonesimp` and then import using
#    `from _ import coppertop.dm.linalg.orient` or `from _.coppertop.dm.linalg import orient`. There are probably other
#    ways to do this that are easily to reason about.
#
# in modules:
# - @coppertop extend any prior name in the module that is a JFunct, raising an error if the name is not a JFunc
# - import similarly updates any prior name that is a JFunc, BUT will not raise an error is the name is not a JFunc
#   instead overwriting the name as per normal Python semantics.
#
# in functions:
# - @coppertop will extend any prior name (inheriting from parent scope), raising an error if the name is not a JFunc
# - import similarly updates any prior name that is a JFunc (inheriting from parent scope), BUT will not raise an error
#   is the name is not a JFunc
#
# - we raise an error if a non-JFunc is imported that would overwrite a JFunc


# OPEN:
# - remove the idea of uber overloads
# - follow the recommendations in https://docs.python.org/3/library/functions.html#import__ and don't replace
#   builtins.__import__ but instead use importlib.import_module() or similar
# - overload count the type (including schema variables) and count the function and ideally count the module
# - allow a call from Python to trigger building of a new function
# - add a binary `selectFn` that returns the tvfunc but doesn't call it, e.g. to get the details of a call could do
#   `PP >> selectFn >> (cluedoHelper) >> details >> PP` or `cluedoHelper` >> selectFn >> PP >> details >> PP`


import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

__all__ = [
    'coppertop', 'nullary', 'unary', 'binary', 'ternary', '_', 'sig', 'context', 'typeOf', 'makeFn',
    'fitsWithin', 'type'
]


import inspect, types, builtins

import coppertop as coppertopMod
coppertopMod.__version__ = "2025.07.05.1"
from bones import jones

from bones.core.context import context
from coppertop._scopes import _UNDERSCORE
from bones.core.errors import ErrSite, CPTBError, NotYetImplemented
from bones.core.sentinels import Missing
from bones.core.utils import raiseLess
from bones.ts.metatypes import BType, fitsWithin as origFitsWithin, BTFn, BTTuple, BTAtom, _btypeByClass
from bones.lang.types import nullary, unary, binary, ternary, _tvfunc, btype, pytype
from bones.ts.select import Family, ppSig


py = BType('py: atom in mem')
FN_ONLY_NAMES = []

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


sys._bmodules = {'': BModule('')}   # NOTE: bones modules live in sys._bmodules
_unhandledTypes = set()             # OPEN: do we still need this?


_ = _UNDERSCORE
MANDATORY = inspect._empty      # Python sentinel to indicate an argument has no default (i.e. is not optional)
NO_ANNOTATION = inspect._empty  # Python sentinel to indicate an argument has no annotation
SCRATCH = 'scratch'


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
        if name == '*':
            a = 1
        updateUber = not local
        modname, bmod, umod, fnname, pymodFn, enclosingFnName, argNames, sig, tRet, pass_tByT = _fnContext(pyfn, 'registerFn', name)

        fn = _tvfunc(
            name=fnname, modname=modname, style=style_, _v=pyfn, dispatchEvenIfAllTypes=dispatchEvenIfAllTypes,
            typeHelper=typeHelper, _t=BTFn(sig, tRet), argNames=argNames, pass_tByT=pass_tByT
        )

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
        if fnname in FN_ONLY_NAMES and modname == 'scratch':
            bf = jonesFnByStyle[style_](fnname, modname, pyfn, _UNDERSCORE)
            return bf
        if enclosingFnName:
            if pymodFn is Missing:
                return jonesFnByStyle[style_](fnname, modname + '.' + enclosingFnName, Family(fn), _UNDERSCORE)
            else:
                return jonesFnByStyle[style_](fnname, modname + '.' + enclosingFnName, Family(pymodFn.d, fn), _UNDERSCORE)
        else:
            if pymodFn is Missing:
                if bmodFn is Missing:
                    if uberFn is Missing:
                        jf = jonesFnByStyle[style_](fnname, modname, Family(fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jf
                        if updateUber: umod.__dict__[fnname] = jonesFnByStyle[style_](fnname, '_', Family(fn), _UNDERSCORE)
                        return jf
                    else:
                        jf = jonesFnByStyle[style_](fnname, modname, Family(fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jf
                        if updateUber: umod.__dict__[fnname].d = Family(uberFn.d, fn)
                        return jf
                else:
                    if uberFn is Missing:
                        jf = jonesFnByStyle[style_](fnname, modname, Family(fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jonesFnByStyle[style_](fnname, modname, Family(bmodFn.d, fn), _UNDERSCORE)
                        if updateUber: umod.__dict__[fnname] = jonesFnByStyle[style_](fnname, '_', Family(fn), _UNDERSCORE)
                        return jf
                    else:
                        jf = jonesFnByStyle[style_](fnname, modname, Family(fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jonesFnByStyle[style_](fnname, modname, Family(bmodFn.d, fn), _UNDERSCORE)
                        if updateUber: umod.__dict__[fnname].d = Family(uberFn.d, fn)
                        return jf
            else:
                if bmodFn is Missing:
                    if uberFn is Missing:
                        jf = jonesFnByStyle[style_](fnname, modname, Family(pymodFn.d, fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jf
                        if updateUber: umod.__dict__[fnname] = jonesFnByStyle[style_](fnname, '_', Family(pymodFn.d, fn), _UNDERSCORE)
                        return jf
                    else:
                        jf = jonesFnByStyle[style_](fnname, modname, Family(pymodFn.d, fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jf
                        if updateUber: umod.__dict__[fnname].d = Family(uberFn.d, jf.d)
                        return jf
                else:
                    if uberFn is Missing:
                        jf = jonesFnByStyle[style_](fnname, modname, Family(pymodFn.d, fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jonesFnByStyle[style_](fnname, modname, Family(bmodFn.d, jf.d), _UNDERSCORE)
                        if updateUber: umod.__dict__[fnname] = jonesFnByStyle[style_](fnname, '_', Family(pymodFn.d, fn), _UNDERSCORE)
                        return jf
                    else:
                        jf = jonesFnByStyle[style_](fnname, modname, Family(pymodFn.d, fn), _UNDERSCORE)
                        bmod.__dict__[fnname] = jonesFnByStyle[style_](fnname, modname, Family(bmodFn.d, jf.d), _UNDERSCORE)
                        if updateUber: umod.__dict__[fnname].d = Family(uberFn.d, jf.d)
                        return jf


    if len(args) == 1 and isinstance(args[0], (types.FunctionType, types.MethodType, builtins.type)):
        # of form @coppertop so args[0] is the function or callable class being decorated
        return registerFn(args[0])

    else:
        # of form as @coppertop() or @coppertop(overrideLHS=True) etc
        if len(args): raiseLess(TypeError('Only kwargs allowed', ErrSite("#2")))
        return registerFn

# In general don't do this! However, I want to be able to put libraries under the coppertop namespace and not have
# `import coppertop.dm` which defines the local 'coppertop' as the module etc kybosh `from coppertop.pipe import *`
# which defines the local 'coppertop' as the coppertop decorator.
# See https://stackoverflow.com/questions/1060796/callable-modules for a discussion of this trick.
class SpecialCoppertopModule(sys.modules[__name__].__class__):
    def __call__(self, *args, **kwargs):
        return coppertop(*args, **kwargs)
coppertopMod.__class__ = SpecialCoppertopModule


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
    priorX = frame.f_locals.get(fnname, Missing)
    if name:
        if name == fnname: raise CoppertopError('In order to reduce accidental errors it is not allowed to name a function as itself')
        fnname = name
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
# IMPORT HOOK
# **********************************************************************************************************************

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
                raise CoppertopImportError(f'Trying to import "{n}" which is a {builtins.type(addition)}')
            if current is Missing:
                tobmod.__dict__[n] = addition.__class__(n, tobmodname, Family(addition.d), _UNDERSCORE)
            else:
                tobmod.__dict__[n] = current.__class__(n, tobmodname, Family(current.d, addition.d), _UNDERSCORE)
            thingsToImport[n] = addition
        elif isinstance(pymodJf, (jones._fn, jones._pfn)):
            if isinstance(addition, (jones._fn, jones._pfn)):
                # overload current and addition
                if current is Missing:
                    tobmod.__dict__[n] = addition.__class__(n, tobmodname, Family(addition.d), _UNDERSCORE)
                    thingsToImport[n] = addition.__class__(n, tobmodname, Family(pymodJf.d, addition.d), _UNDERSCORE)
                else:
                    if _styleOfFn(current) != _styleOfFn(addition):
                        raise CoppertopImportError(f'"{n} is a {_styleOfFn(current)} in {tobmodname} but a {_styleOfFn(addition)} in {frombmodName}')
                    tobmod.__dict__[n] = current.__class__(n, tobmodname, Family(current.d, addition.d), _UNDERSCORE)
                    thingsToImport[n] = current.__class__(current.name, tobmodname, Family(pymodJf.d, addition.d), _UNDERSCORE)
            elif isinstance(addition, BType):
                raise NotYetImplemented("overloading type and jonesFn")
            else:
                raise CoppertopImportError(f'Trying to import "{n}", which is a {builtins.type(addition)} to overwrite a {builtins.type(current)}!!!')
        elif isinstance(current, BType):
            if isinstance(addition, (jones._fn, jones._pfn)):
                raise NotYetImplemented("overloading type and jonesFn")
            elif isinstance(addition, BType):
                # no need to import anything but just check they are the same
                if current._id != addition._id: raise CoppertopImportError(f"Type {n} is different in {frombmodName}")
            else:
                raise CoppertopImportError(f'Trying to import "{n}", which is a {builtins.type(addition)} to overwrite a {builtins.type(current)}!!!')
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
            # OPEN: check for __all__
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
# essential public functions
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
    tvfunc = _tvfunc(
        name=fnname, modname=modname, style=unary, _v=pyfn, dispatchEvenIfAllTypes=False,
        typeHelper=Missing, _t=_t, argNames=argNames, pass_tByT=False
    )
    return jones._unary(fnname, modname, Family(tvfunc), _UNDERSCORE)

@coppertop
def sig(x):
    return ppSig(x)

@coppertop(dispatchEvenIfAllTypes=True)
def type(x) -> pytype:
    return builtins.type(x)

@coppertop(dispatchEvenIfAllTypes=True)
def typeOf(x) -> btype + pytype:
    return sys._typeOf(x)



if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__ + ' - done')
