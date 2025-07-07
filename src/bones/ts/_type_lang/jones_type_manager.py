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

import builtins

from bones.core.errors import NotYetImplemented
from bones.core.sentinels import Missing
from bones import jones
from bones.jones import BTypeError, BType as BTypeRoot
from bones.ts.core import bmtnul, bmtatm, bmtint, bmtuni, bmttup, bmtstr, bmtrec, bmtseq, bmtmap, bmtfnc, bmtsvr, \
    Constructors, TLError
from bones.ts._type_lang.utils import OnErrorRollback
from bones.ts._type_lang.fits import fitsWithin
from bones.core.errors import ProgrammerError, NotYetImplemented, PathNotTested
from bones.core.utils import raiseLess, firstValue
from bones.core.errors import ErrSite
from bones.core.context import context
from bones.ts.type_lang import TypeLangInterpreter


NaT = 0
_btcls_by_bmtid = {}
_btypeByClass = {}                   # mappings from python classes to bones types
_BTypeById = [Missing] * 10000
REPL_OVERRIDE_MODE = False



def getBTypeForClass(cls):
    if (t := _btypeByClass.get(cls, Missing)) is Missing:
        name = cls.__module__ + "." + cls.__name__
        t = BTAtom(name, space=BType('mem'))
        _btypeByClass[cls] = t
    return t

def _ensurePyBType(x):
    if not isinstance(x, BType) and not isinstance(x, type):
        bmtid = sys._gtm.bmtid(x)
        cls = _btcls_by_bmtid[bmtid]
        return sys._gtm.replaceWith(x, cls._new(x))
    else:
        return x


# **********************************************************************************************************************
# Python layer of Jones' BType
# **********************************************************************************************************************

class BType(BTypeRoot):
    _arrayOrdinalTypes = ()

    __slots__ = ['_constructor', '_coercer', '_pp']

    # TYPE CONSTRUCTION & NAMING

    @classmethod
    def _new(cls, bt=Missing):
        assert cls is not BType
        if bt:
            if bt.id == NaT: raise BTypeError('bt.id == NaT')
            instance = super().__new__(cls)
            instance.id = bt.id
            instance._constructor = Missing
            instance._coercer = Missing
            instance._pp = Missing
            _BTypeById[bt.id] = instance
            return instance
        else:
            return super().__new__(cls)

    def __new__(cls, tlOrInt):
        if isinstance(tlOrInt, int):
            bt = sys._gtm.fromId(tlOrInt)
        elif isinstance(tlOrInt, str):
            bt = sys._gtli.eval(tlOrInt)
        else:
            raise TypeError(f'Expected int or str, got {type(tlOrInt)}')
        cls = _btcls_by_bmtid[sys._gtm.bmtid(bt)]
        return bt if isinstance(bt, cls) else sys._gtm.replaceWith(bt, cls._new(bt))

    def __init__(*args, **kwargs):
        pass

    def __instancecheck__(cls, x):
        if hasattr(x, '_t'):
            return x._t in cls
        return type(x) in cls

    @property
    def hasT(self):
        return sys._gtm.hasT(self)

    @property
    def explicit(self):
        return sys._gtm.isExplicit(self)

    @property
    def name(self):
        return sys._gtm.name(self)

    def nameAs(self, name):
        sys._gtm.bind(name, self)
        return self

    @property
    def space(self):
        return sys._gtm.space(self) or Missing

    @property
    def rootSpace(self):
        return sys._gtm.rootSpace(self) or Missing

    # TYPE COERCION OF INSTANCES

    def setCoercer(self, fnTV):
        if self.hasT:
            raise BTypeError(f'{self} has a T so cannot be an instance type')
        if self._coercer is Missing:
            self._coercer = fnTV
        else:
            if self._coercer is not fnTV:
                # this helps protect from bugs however it's a pain in Jupyter as cells need to be recalculated
                # and my windows machine is noticably slower than my M1 macbook
                raise ProgrammerError('coercer already set')
        return self

    def __ror__(self, instance):  # instance | type   the case of type | type should be caught first below
        if self.hasT:
            if not sys._fitsWithin(sys._typeOf(instance), self):
                raise BTypeError(f'{self} has a T so cannot be an instance type')
        if hasattr(instance, '_asT'):
            # the instance has a coercion method
            return instance._asT(self)
        else:
            if (coercer := self._coercer) is Missing:
                if isinstance(self, BTIntersection):
                    # if we are an intersection type then check if one is in the intersection's types
                    coercers = {t:t._coercer for t in self.types if hasattr(t, '_coercer') and t._coercer is not Missing}
                    if len(coercers) == 0:
                        pass
                    elif len(coercers) == 1:
                        coercer = firstValue(coercers)
                    else:
                        for t in list(coercers.keys()):
                            if isinstance(t, BTIntersection):
                                for tChild in t.types:
                                    if tChild != t:
                                        coercers.pop(tChild, None)
                        if len(coercers) == 1:
                            coercer = firstValue(coercers)
                        else:
                            msg = f'`{repr(instance)}` can\'t be coerced to <:{self}> - instance has no _asT, type (or intersection\'s types) has more than one _coercer'
                            raiseLess(BTypeError(msg, ErrSite(self.__class__)))
            if coercer:
                return coercer(self, instance)
            else:
                msg = f'`{repr(instance)}` can\'t be coerced to <:{self}> - instance has no _asT, type (or intersection\'s types) has no _coercer'
                raiseLess(BTypeError(msg, ErrSite(self.__class__)))

    # INSTANCE CONSTRUCTION

    def setConstructor(self, fnTV):
        # COULDDO check that first arg of fnTV is t - I accidentally tried to use a bones type
        # as a constructor and it was hard to diagnose the cause of the bug I was seeing
        if (self.rootSpace is not BTAtom('mem')):
            raise BTypeError(f'{self} is not a memory type')
        if self.hasT:
            raise BTypeError(f'{self} has a T so cannot be an instance type')
        if self._constructor is not Missing and fnTV is not self._constructor and not REPL_OVERRIDE_MODE:
            raise ProgrammerError('constructor already set')
        self._constructor = fnTV
        return self

    def __call__(self, *args, **kwargs):  # type(*args, **kwargs)
        # create a new instance using the constructor
        if self.hasT:
            raise BTypeError(f'{self} has a T so cannot be an instance type')
        # a constructor should only really be for recursive intersection or atom in mem
        if (constructor := self._constructor) is Missing:
            if isinstance(self, BTIntersection):
                for t in self.types:
                    if (constructor := t._constructor) is not Missing:
                        break
        if not constructor:
            raise ProgrammerError(f'No constructor defined for type "{self}"')
        if args and isinstance(args[0], Constructors):
            cs = Constructors(args[0])
            cs.append(self)
            return constructor(cs, *args[1:], **kwargs)
        else:
            cs = Constructors()
            cs.append(self)
            return constructor(cs, *args, **kwargs)

    # SET OPERATION BASED CONSTRUCTION OF TYPES

    # unions - +
    def __add__(self, rhs):  # type + rhs
        if isinstance(rhs, type):
            rhs = getBTypeForClass(rhs)
        elif not isinstance(rhs, BType):
            raise BTypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        return BTUnion(self, rhs)

    def __radd__(self, lhs):  # lhs + type
        if isinstance(lhs, type):
            lhs = getBTypeForClass(lhs)
        elif not isinstance(lhs, BType):
            raise BTypeError(f'lhs should be a BType or type - got {repr(lhs)}')
        return BTUnion(lhs, self)

    # products - tuples - *
    def __mul__(self, rhs):  # type * rhs
        if isinstance(rhs, type):
            rhs = getBTypeForClass(rhs)
        elif not isinstance(rhs, BType):
            raise BTypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        types = \
            (self.types if isinstance(self, BTTuple) else (self,)) + \
            (rhs.types if isinstance(rhs, BTTuple) else (rhs,))
        return BTTuple(*types)

    def __rmul__(self, lhs):  # lhs * type
        if isinstance(lhs, type):
            lhs = getBTypeForClass(lhs)
        elif not isinstance(lhs, BType):
            raise BTypeError(f'lhs should be a BType or type - got {repr(lhs)}')
        types = \
            (lhs.types if isinstance(lhs, BTTuple) else (lhs,)) + \
            (self.types if isinstance(self, BTTuple) else (self,))
        return BTTuple(*types)

    # finite size exponentials - lists and maps - **
    def __pow__(self, rhs):  # type ** rhs
        if isinstance(rhs, type):
            rhs = getBTypeForClass(rhs)
        elif not isinstance(rhs, BType):
            raise BTypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        if rhs in BType._arrayOrdinalTypes: raise BTypeError(f'rhs must not be an ordinal type')
        if self in BType._arrayOrdinalTypes:
            return BTSeq(rhs)
        else:
            return BTMap(self, rhs)

    def __rpow__(self, lhs):  # lhs ** type
        if isinstance(lhs, type):
            lhs = getBTypeForClass(lhs)
        elif not isinstance(lhs, BType):
            raise BTypeError(f'lhs should be a BType or type - got {repr(lhs)} - has a type been overridden?')
        if self in BType._arrayOrdinalTypes: raise BTypeError(f'rhs must not be an ordinal type')
        if lhs in BType._arrayOrdinalTypes:
            return BTSeq(self)
        else:
            return BTMap(lhs, self)

    # general exponentials - functions - ^
    def __xor__(self, rhs):  # type ^ rhs
        if isinstance(rhs, type):
            rhs = getBTypeForClass(rhs)
        elif not isinstance(rhs, BType):
            raise BTypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        return BTFn(self if isinstance(self, BTTuple) else BTTuple(self), rhs)

    def __rxor__(self, lhs):  # lhs ^ type
        if isinstance(lhs, BTTuple):
            tArgs = lhs
        elif isinstance(lhs, type):
            lhs = getBTypeForClass(lhs)
            tArgs = (lhs,)
        elif isinstance(lhs, BType):
            tArgs = (lhs,)
        elif isinstance(lhs, (list, tuple)):
            tArgs = lhs
        elif isinstance(lhs, generator):
            tArgs = tuple(lhs)
        else:
            raise BTypeError(f'lhs should be a BType, type, list or tuple - got {repr(lhs)}')
        return BTFn(tArgs, self)

    # intersections - &
    def __and__(self, rhs):  # type & rhs
        if isinstance(rhs, type):
            rhs = getBTypeForClass(rhs)
        elif not isinstance(rhs, BType):
            raise BTypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        if self.__class__ is BTFn:
            return BTFamily(self, rhs)
        else:
            return BTIntersection(self, rhs)

    def __rand__(self, lhs):  # lhs & type
        if isinstance(lhs, type):
            lhs = getBTypeForClass(lhs)
        elif not isinstance(lhs, BType):
            raise BTypeError(f'lhs should be a BType or type - got {repr(lhs)}')
        if self.__class__ is BTFn:
            return BTFamily(lhs, self)
        else:
            return BTIntersection(lhs, self)

    # intersection - []
    def __getitem__(self, rhs):  # type[rhs]
        if isinstance(rhs, int):
            # gets called by dict_keys | btype, also numpy float64 | btype
            raise TypeError(f'__getitem__ - perhaps coming from `dict_keys | btype` or `np.float64 | btype`? self = {self}, rhs = {rhs}')
        elif isinstance(rhs, tuple):
            return BTIntersection(*(self, ) + rhs)
        elif isinstance(rhs, str):
            raise TypeError()
        else:
            if self.__class__ is BTFn:
                return BTFamily(self, rhs)
            else:
                return BTIntersection(self, rhs)

    # intersection - +, -
    def __pos__(self):  # +type
        return _AddStuff(self)

    def __neg__(self):  # -type
        return _SubtractStuff(self)

    # QUERYING

    def __len__(self):
        return 1  # all non-union types are a union of length 1

    def __contains__(self, item):
        return item == self

    def __hash__(self):
        return self.id

    def __eq__(self, rhs):
        return isinstance(rhs, BType) and self.id == rhs.id

    # DISPLAY

    def setPP(self, pp):
        self._pp = pp
        return self

    def __str__(self):
        return self.__repr__()

    def ppName(self):
        if context.showFullType:
            return Missing
        else:
            if a := self._pp:
                return a, False, False
            elif a := self.name:
                return a, False, False

    def ppT(self):
        if a := self.ppName(): return a
        return f'bt{self.id}', False, False

    def __repr__(self):
        pp, compound, hasCompound = self.ppT()
        return pp

    # # instance creation unwind
    # def _killType(self, id):
    #     _BTypeById[id] = Missing



class BTAtom(BType):

    def __new__(cls, name, explicit=Missing, space=Missing, implicitly=Missing, btype=Missing):
        tm = sys._gtm
        options = {}
        if explicit: options['explicit'] = explicit
        if space: options['space'] = space
        if implicitly: options['implicitly'] = implicitly
        if btype is not Missing and space is not Missing:
            assert explicit is Missing and implicitly is Missing, "when calling atom with space, explicit and implicitly must be set in btype"
            bt = tm.atom(name, btype=btype, space=space)
            _BTypeById[bt.id] = Missing        # removed the BTReserved type
        elif options:
            if (current := tm[name]).id:
                bt = tm._tm.checkAtom(current, explicit=explicit or False, space=space or None, implicitly=implicitly or None)
            else:
                reserved = tm.reserve(space=space)
                bt = tm.atom(name, btype=reserved, **options)
        else:
            if btype is not Missing:
                bt = tm.atom(name, btype=btype)
            else:
                bt = tm.atom(name)
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    def ppName(self):
        return sys._gtm.name(self), False, False



class BTIntersection(BType):

    def __new__(cls, *types, space=Missing):
        if len(types) == 0: raise ProgrammerError('No types provided')
        if len(types) == 1: return types[0]
        tm = sys._gtm
        bt = tm.intersection([getBTypeForClass(t) if isinstance(t, type) else _ensurePyBType(t) for t in types], space=space)
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    @classmethod
    def noSpaceCheck(cls, types):
        if len(types) == 0: raise ProgrammerError('No types provided')
        if len(types) == 1: return types[0]
        tm = sys._gtm
        bt = tm.intersectionNoCheck(types)
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    @property
    def types(self):
        return sys._gtm.intersectionTl(self)

    def __hash__(self):
        # since we have defined __eq__ we need to define __hash__ as well
        return self.id  # see https://stackoverflow.com/questions/53518981/inheritance-hash-sets-to-none-in-a-subclass

    def __eq__(self, rhs):
        # we can be subclassed and we want parent == child if type list is the same
        if isinstance(rhs, BTIntersection):
            if self.id == rhs.id: return True
            lhsTypes = self.types
            rhsTypes = rhs.types
            if len(lhsTypes) != len(rhsTypes): return False
            for tL, tR in zip(lhsTypes, rhsTypes):
                if tL.id != tR.id: return False
            return True
        else:
            return False

    def __sub__(self, rhs):     # self - other
        raise NotYetImplemented()

    def __len__(self):
        return len(self.types)

    def __contains__(self, item):
        return item in self.types

    def ppT(self):
        if a := self.ppName(): return a
        ts = []
        hasCompound = False
        for t in self.types:
            if t.id == self.id:
                pp, compound, childCompound = self.name, False, False
            elif isinstance(t, BType):
                pp, compound, childCompound = ppT(t)
            else:
                pp, compound, childCompound = f't{t.id}', False, False
            ts.append(f'({pp})' if compound else pp)
            hasCompound = hasCompound or compound
        return (' & ' if hasCompound else '&').join(ts), True, hasCompound



class BTFamily(BTIntersection):

    def ppT(self):
        if a := self.ppName(): return a
        ts = []
        hasCompound = False
        for t in self.types:
            pp, compound, childCompound = ppT(t)
            ts.append(f'({pp})' if compound and childCompound else pp)
            hasCompound = hasCompound or compound
        return ' & '.join(ts), True, hasCompound



class BTUnion(BType):

    def __new__(cls, *types):
        if len(types) == 0: raise ProgrammerError('No types provided')
        if len(types) == 1: return types[0]
        tm = sys._gtm
        bt = tm.union([getBTypeForClass(t) if isinstance(t, type) else _ensurePyBType(t) for t in types])
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    @property
    def types(self):
        return sys._gtm.unionTl(self)

    def __hash__(self):
        # since we have defined __eq__ we need to define __hash__ as well
        return self.id  # see https://stackoverflow.com/questions/53518981/inheritance-hash-sets-to-none-in-a-subclass

    def __eq__(self, rhs):
        # we can be subclassed and we want parent == child if type list is the same
        if isinstance(rhs, BTUnion):
            if self.id == rhs.id: return True
            lhsTypes = self.types
            rhsTypes = rhs.types
            if len(lhsTypes) != len(rhsTypes): return False
            for tL, tR in zip((lhsTypes, rhsTypes)):
                if tL.id != tR.id: return False
            return True
        else:
            return False

    def __len__(self):
        return len(self.types)

    def __contains__(self, item):
        return item in self.types

    def ppT(self):
        if a := self.ppName(): return a
        ts = []
        hasCompound = False
        for t in self.types:
            pp, compound, childCompound = ppT(t)
            ts.append(f'({pp})' if compound and childCompound else pp)
            hasCompound = hasCompound or compound
        return (' + ' if hasCompound else '+').join(ts), True, hasCompound



class BTTuple(BType):
    # product type accessed by ordinal

    def __new__(cls, *types):
        tm = sys._gtm
        bt = tm.tuple(types)
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    @property
    def types(self):
        return sys._gtm.tupleTl(self)

    def ppT(self):
        if a := self.ppName(): return a
        ts = []
        hasCompound = False
        for t in self.types:
            pp, compound, childCompound = ppT(t)
            ts.append(f'({pp})' if compound and childCompound else pp)
            hasCompound = hasCompound or compound
        if ts:
            return (' * ' if hasCompound else '*').join(ts), len(ts) > 1, hasCompound
        else:
            # the null tuple
            return '()', False, False

    def __iter__(self):
        # required so tuple can be used in zip here - `for tArg, tSig in zip(tArgs[0:len(sd.sig)], sd.sig):`
        return iter(self.types)



class BTStruct(BType):
    # product type accessed by name

    def __new__(cls, *args, btype=Missing, **kwargs):
        # OPEN: for moment convert suymbols to strings
        if args:
            if len(args) == 1 and isinstance(args[0], dict):
                names = tuple((str(a) for a in args[0].keys()))
                types = tuple(args[0].values())
            elif len(args) == 2 and isinstance(args[0], (tuple, list)) and isinstance(args[1], (tuple, list)):
                names = tuple((str(a) for a in args[0]))
                types = tuple(args[1])
            else:
                raise BTypeError('Unhandled case')
        else:
            names = tuple((str(a) for a in kwargs.keys()))
            types = tuple(kwargs.values())
        if len(names) != len(types):
            raise BTypeError('names and types must be of same length')
        tm = sys._gtm
        bt = tm.struct(names, types, btype=btype)
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    @property
    def names(self):
        return sys._gtm.structNames(self)

    @property
    def types(self):
        return sys._gtm.structTl(self)

    def ppT(self):
        if a := self.ppName(): return a
        ts = []
        hasCompound = False
        for i, (name, t) in enumerate(zip(self.names, self.types)):
            pp, compound, childCompound = ppT(t)
            ts.append(f'{name}:{pp}')
            hasCompound = hasCompound or compound
        return f'{{{", ".join(ts)}}}', False, hasCompound



class BTSeq(BType):
    # homogenous discrete / finite map (exponential) type accessed by ordinal - i.e. N**T, 3**T etc

    def __new__(cls, mappedType):
        tm = sys._gtm
        mappedType = getBTypeForClass(mappedType) if isinstance(mappedType, type) else _ensurePyBType(mappedType)
        bt = tm.seq(mappedType)
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    @property
    def mappedType(self):
        return sys._gtm.seqT(self)

    def ppT(self):
        if a := self.ppName(): return a
        pp2, compound2, childCompound2 = ppT(sys._gtm.seqT(self))
        if compound2 and childCompound2: pp2 = f'({pp2})'
        return f'N**{pp2}', True, False



class BTMap(BType):
    # homogenous discrete / finite map (exponential) type accessed by key - e.g. T2**T1 T1->T2
    # tK tR key, result rather than key value

    def __new__(cls, indexType, mappedType):
        tm = sys._gtm
        bt = tm.map(indexType, mappedType)
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    @property
    def indexType(self):
        return sys._gtm.mapTK(self)

    @property
    def mappedType(self):
        return sys._gtm.mapTV(self)

    def ppT(self):
        if a := self.ppName(): return a
        pp1, compound1, childCompound1 = ppT(self.indexType)
        pp2, compound2, childCompound2 = ppT(self.mappedType)
        if compound1: pp1 = f'({pp1})'
        if compound2: pp2 = f'({pp2})'
        return f'{pp1}**{pp2}', True, False



class BTFn(BType):
    # homogenous, generalised and potentially infinite exponential type - aka function

    def __new__(cls, tArgs, tRet):
        if not isinstance(tArgs, BTTuple):
            tArgs = BTTuple(*tArgs)
        tm = sys._gtm
        bt = tm.fn(tArgs, tRet)
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))

    def ppT(self):
        if a := self.ppName(): return a
        pp1, compound1, childCompound1 = ppT(self.tArgs)
        pp2, compound2, childCompound2 = ppT(self.tRet)
        if compound1 and childCompound1: pp1 = f'({pp1})'
        if compound2 and childCompound2: pp2 = f'({pp2})'
        return f'{pp1}{" ^ " if (compound1 or compound2) else "^"}{pp2}', True, compound1 or compound2

    @property
    def tArgs(self):
        return sys._gtm.fnTArgs(self)

    @property
    def tRet(self):
        return sys._gtm.fnTRet(self)

    @property
    def numargs(self):
        return len(sys._gtm.tupleTl((sys._gtm.fnTArgs(self))))


class BTSchemaVariable(BTAtom):
    # T1, T2, etc - NB: the term schema means a model / schematic whereas the term scheme means a plan of action

    def __new__(cls, name, space=Missing):
        # do we allow matching on space or explicit?
        tm = sys._gtm
        if (bt := tm.lookup(name)).id:
            if tm.bmtid(bt) != bmtsvr:
                raise BTypeError(f'"{name}" is already in use and not a schema variable')
        else:
            if space:
                raise NotYetImplemented()
            else:
                bt = tm.bind(name, tm.schemavar())
        return bt if isinstance(bt, cls) else tm.replaceWith(bt, cls._new(bt))


class _AddStuff:
    def __init__(self, t):
        self.t = t
    def __ror__(self, instance):    # instance | type
        if hasattr(instance, '_t'):
            return instance | BTIntersection(instance._t, self.t)
        else:
            return instance | BTIntersection(builtins.type(instance), self.t)


class _SubtractStuff:
    def __init__(self, t):
        self.t = t
    def __ror__(self, instance):  # instance | type
        if not isinstance(t := instance._t if hasattr(instance, '_t') else builtins.type(instance), BTIntersection):
            raise BTypeError(f'Can only subtract a type from an intersection but LHS type is {t}')
        tlLhs = t.types
        tlRhs = self.t.types if isinstance(self.t, BTIntersection) else (self.t, )
        a_, ab, b_, weakenings = _partitionIntersectionTLs(tlLhs, tlRhs)
        if b_:
            raise BTypeError(f'RHS is trying to subtract {b_} which isn\'t in the LHS {t} - {self.t}')
        if not ab:
            raise ProgrammerError(f'Can\'t end up subtracting nothing')
        if not a_:
            raise BTypeError('Left with null set')
        if len(a_) == 1:
            return instance | a_[0]
        else:
            new_t = sys._gtm.intersectionNoCheck(a_)
            return instance | _ensurePyBType(new_t)




_btcls_by_bmtid[bmtatm] = BTAtom
_btcls_by_bmtid[bmtint] = BTIntersection
_btcls_by_bmtid[bmtuni] = BTUnion
_btcls_by_bmtid[bmttup] = BTTuple
_btcls_by_bmtid[bmtstr] = BTStruct
_btcls_by_bmtid[bmtrec] = Missing
_btcls_by_bmtid[bmtseq] = BTSeq
_btcls_by_bmtid[bmtmap] = BTMap
_btcls_by_bmtid[bmtfnc] = BTFn
_btcls_by_bmtid[bmtsvr] = BTSchemaVariable


def ppT(t):
    return (t.__name__, False, False) if isinstance(t, type) else t.ppT()


def extractConstructors(args_, kwargs_):
    if args_ and isinstance(args_[0], Constructors):
        constr, args = args_[0][0], args_[1:]
    else:
        constr, args = Missing, args_
    return constr, args, kwargs_



# **********************************************************************************************************************
# Python interface to Jone TypeManager
# **********************************************************************************************************************

class JonesTypeManager:
    __slots__ = ['_k', '_tm', '_implicitRecursive', '_tbcByVarname', '_fitsCache']

    def __init__(self):
        self._k = jones.Kernel()
        self._tm = self._k.tm
        self._implicitRecursive = Missing
        self._tbcByVarname = {}
        self._fitsCache = {}


    # parsing process

    def checkImplicitRecursiveAssigned(self):
        if (btype := self._implicitRecursive) is not Missing:
            raise TLError(f'Implicit recursive type "{self._tm.nameOf(btype)}" has not been confirmed')
        return Missing

    def checkpoint(self):
        pass

    def commit(self):
        pass

    def done(self):
        if self._implicitRecursive: raise ValueError(f'Implicit recursive variables not assigned: {self._implicitRecursive}')
        if self._tbcByVarname: raise ValueError(f'Declared recursive variables not assigned: {", ".join(self._tbcByVarname)}')
        return None

    def onErrRollback(self):
        return OnErrorRollback(self)

    def rollback(self):
        pass


    # BType creation and accessing

    def __getitem__(self, name):
        if isinstance(name, str):
            return self._tm.lookup(name)
        else:
            return [self._tm.lookup(n) for n in name]

    def atom(self, name, *, explicit=Missing, space=Missing, implicitly=Missing, btype=Missing):
        if (current := self._tm.lookup(name)).id and self._tm.bmetatypeid(current) != bmtnul:
            if btype and btype.id != current.id:
                raise BTypeError(f'"{name}" is already bound to {bmtnameById[self._tm.bmetatypeid(current)]}{current.id}')
            btype = self._tm.checkAtom(current, explicit=explicit or False, space=space or None, implicitly=implicitly or None)
        else:
            btype = self._tm.initAtom(btype=btype or None, explicit=explicit or False, space=space or None, implicitly=implicitly or None)
        return self.bind(name, btype)

    def bind(self, name, btype):
        try:
            btype = self._tm.bind(name, btype)
        except BTypeError as ex:
            if 'already bound' in ex.args[0]:
                current = self._tm.lookup(name)
                if current.id != btype.id:
                    bmtid = self._tm.bmetatypeid(current)
                    raise BTypeError(f'"{name}" is already bound to {bmtnameById[bmtid]}{current.id}')
                else:
                    pass
            else:
                raise
        if self._tm.isRecursive(btype) and self._tm.bmetatypeid(btype) != bmtnul:
            # reserving sets recursive !! bother so defend against it here
            self._tbcByVarname.pop(name, None)
            if self._implicitRecursive and self._implicitRecursive.id == btype.id: self._implicitRecursive = Missing

        return btype

    def bmtid(self, t):
        return self._tm.bmetatypeid(t)

    def check(self, A, B):
        if A.id == B.id: return True
        bmtidA = self.bmtid(A)
        if self.bmtid(A) != self.bmtid(B): raise BTypeError()
        if bmtidA == bmtatm: return True
        # OPEN: implement properly
        raise BTypeError()

    def fn(self, tArgs, tRet, *, btype=Missing):
        return self._tm.fn(tArgs, tRet, btype=btype or None)

    def fnTArgs(self, btype):
        return self._tm.fnTArgs(btype)

    def fnTRet(self, btype):
        return self._tm.fnTRet(btype)

    def fromId(self, id):
        return self._tm.fromId(id)

    def hasT(self, btype):
        return self._tm.hasT(btype)

    def initAtom(self, *, explicit=Missing, space=Missing, implicitly=Missing, btype=Missing):
        return self._tm.initAtom(btype=btype or None, explicit=explicit or False, space=space or None, implicitly=implicitly or None)

    def intersection(self, types, *, space=Missing, btype=Missing):
        return self._tm.intersection(*types, space=space or None, btype=btype or None)

    def intersectionNoCheck(self, types):
        types = [getBTypeForClass(t) if isinstance(t, type) else _ensurePyBType(t) for t in types]
        return self._tm.intersectionNoCheck(*types)

    def intersectionTl(self, t):
        return self._tm.intersectionTl(t)

    def intersectionTlidFor(self, types):
        return self._tm.intersectionTlidFor(*types)

    def isExplicit(self, t):
        return self._tm.isExplicit(t)

    def isRecursive(self, t):
        return self._tm.isRecursive(t)

    def lookup(self, name):
        return self._tm.lookup(name) or Missing

    def lookupOrImplicitTbc(self, name):
        # gets the type for the name creating up to one implicit recursive type if it doesn't exist
        if (btype := self._tm.lookup(name)).id == 0:
            # do the implicit recursive check
            if (currentOne := self._implicitRecursive) is not Missing and self._tm.nameOf(currentOne) != name:
                raise TLError(
                    f'Only one implicit recursive type can be defined simutaneously. "{name}" encountered but "{self._tm.nameOf(currentOne)}" is already the currently defined implicit recursive type.')
            btype = self._tm.reserve()
            self._tm.bind(name, btype)
            self._implicitRecursive = self._tbcByVarname[name] = btype
        return btype

    def map(self, tK, tV, *, btype=Missing):
        return self._tm.map(tK, tV, btype=btype or None)

    def mapTK(self, btype):
        return self._tm.mapTK(btype)

    def mapTV(self, btype):
        return self._tm.mapTV(btype)

    def minus(self, A, B):
        return self._tm.minus(A, B)

    def name(self, t):
        return self._tm.nameOf(t)

    def reserve(self, space=Missing, btype=Missing):
        return self._tm.reserve(space=space or None, btype=btype or None)

    def replaceWith(self, btype, pybtype):
        return self._tm.replaceWith(btype, pybtype)

    def rootSpace(self, t):
        return self._tm.rootSpace(t)

    def schemavar(self, btype=Missing):
        return self._tm.schemavar(btype=btype or None)

    def seq(self, contained, *, btype=Missing):
        return _ensurePyBType(self._tm.seq(contained, btype=btype or None))

    def seqT(self, btype):
        return self._tm.seqT(btype)

    def space(self, btype):
        return self._tm.space(btype)

    def struct(self, names, types, *, btype=Missing):
        return self._tm.struct(names, types, btype=btype or None)

    def structNames(self, t):
        return self._tm.structNames(t)

    def structTl(self, t):
        return self._tm.structTl(t)

    def tuple(self, types, btype=Missing):
        return self._tm.tuple(*types, btype=btype or None)

    def tupleTl(self, t):
        return self._tm.tupleTl(t)

    def union(self, types, *, btype=Missing):
        return self._tm.union(*types, btype=btype or None)

    def union_tlid_for(self, btypes):
        return self._tm.union_tlid_for(btypes)

    def unionTl(self, btype):
        return self._tm.unionTl(btype)



JonesTypeManager.fitsWithin = fitsWithin



if not hasattr(sys, '_gtm'):
    sys._gtm = JonesTypeManager()
    sys._gtli = TypeLangInterpreter(sys._gtm)

