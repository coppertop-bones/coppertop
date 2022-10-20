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

# BY DESIGN
# 1) we allow aType['name'] as shorthand for aType[BTAtom('_name')].nameAs('name')  - albeit at the slightly increased
#    chance of misspelling errors
#
# SPEED OPTIONS - SoA style on the list of types, etc - this may also make translation to C easier
# classes with __slots__ seem to be the fastest
# if accessing globals becomes an issue could make the whole module a class

# BType
#   |--- BTAtom
#   |        \--- BTSchemaVariable
#   |--- _BTSetOp
#   |        |--- BTUnion
#   |        |--- BTIntersection
#   |        \--- BTOverload
#   |--- BTTuple
#   |--- BTStruct
#   |--- BTSeq
#   |--- BTMap
#   \--- BTFn


import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)


__all__ = ['BType', 'S']

import itertools, builtins
from bones.core.utils import raiseLess
from bones.core.errors import ErrSite
from bones.core.errors import ProgrammerError, NotYetImplemented, PathNotTested
from bones.core.sentinels import Missing, Void
from bones.core.context import context
from bones.lang.utils import Constructors

_verboseNames = False

_idSeed = itertools.count(start=1)   # reserve id 0 as a terminator of a type set

iterType = type((x for x in []))



_BTypeByName = {}
_BTAtomByName = {}
_BTypeById = [Missing] * 1000


from bones.jones import BType as BTypeRoot



class BType(BTypeRoot):
    
    _arrayOrdinalTypes = ()

    __slots__ = ['id', 'name', 'hasT', 'familial', 'explicit', 'orthogonal', '_constructor', '_coercer', '_pp']

    # TYPE CONSTRUCTION & NAMING

    @classmethod
    def _define(cls):
        assert cls is not BType
        id = next(_idSeed)
        instance = super().__new__(cls)
        instance.TN1 = id
        instance.id = id
        instance.name = Missing
        instance.hasT = False
        instance.familial = False
        instance.explicit = False
        instance.orthogonal = False     # can set to a group whose members when intersected return an uninhabited set
        instance._constructor = Missing
        instance._coercer = Missing
        instance._pp = Missing
        if len(_BTypeById) <= instance.id: _BTypeById.extend([Missing] * 1000)
        _BTypeById[instance.id] = instance
        return instance
    
    @classmethod
    def _new(cls):
        return super().__new__(cls)

    def __new__(cls, name):
        # gets a type throwing an error if it has not already been defined
        # super().__new__(cls)
        if (instance := _BTypeByName.get(name, Missing)) is Missing:
            raise TypeError(f'Unknown type "{name}"')
        return instance

    def __init__(self, *args, **kwargs):
        # just here to prevent the superclasses init being called
        pass

    def __instancecheck__(self, x):
        if hasattr(x, '_t'):
            return x._t in self
        return type(x) in self

    def nameAs(self, name):
        other = _BTypeByName.get(name, Missing)
        if other is Missing:
            if self.name is not Missing:
                raise TypeError(f"t{self.id} has already been named as '{self.name}'")
            self.name = name
            _BTypeByName[name] = self
        else:
            if other is not self: raise TypeError(
                f"Can't name new type ({type(self)}) as '{name}' as another BType({type(other)}) already has that name"
            )
        return self

    @property
    def setFamilial(self):
        self.familial = True
        return self

    @property
    def setExplicit(self):
        self.explicit = True
        return self

    def setOrthogonal(self, group):
        if self.orthogonal and group is not self.orthogonal:
            raise ProgrammerError(f'{self} has orthogonal already set to {self.orthogonal}')
        self.orthogonal = group
        return self

    @property
    def setImplicit(self):
        global _implicitTypes
        if self not in _implicitTypes:
            _implicitTypes += (self,)
        return self


    # TYPE COERCION OF INSTANCES

    def setCoercer(self, fnTV):
        if self.hasT:
            raise TypeError(f'{self} has a T so cannot be an instance type')
        if self._coercer is Missing:
            self._coercer = fnTV
        else:
            if self._coercer is not fnTV:
                # this helps protect from bugs however it's a pain in Jupyter as cells need to be recalculated
                # and my windows machine is noticably slower than my M1 macbook
                raise ProgrammerError('coercer already set')
        return self

    def __ror__(self, instance):        # instance | type   the case of type | type should be caught first below
        if self.hasT:
            raise TypeError(f'{self} has a T so cannot be an instance type')
        elif hasattr(instance, '_asT'):
            # the instance has a coercion method
            return instance._asT(self)
        elif self._coercer:
            # type has a coercer
            return self._coercer(self, instance)
        else:
            msg = f'{instance} can\'t be coerced to <:{self}> - instance has no _asT, type has no _coercer'
            raiseLess(TypeError(msg, ErrSite(self.__class__)))


    # INSTANCE CONSTRUCTION

    def setConstructor(self, fnTV):
        # COULDDO check that first arg of fnTV is t - I accidentally tried to use a bones type
        # as a constructor and it was hard to diagnose the cause of the bug I was seeing
        if self.hasT:
            raise TypeError(f'{self} has a T so cannot be an instance type')
        if self._constructor is Missing:
            self._constructor = fnTV
        else:
            if self._constructor is not fnTV:
                # ditto - see setCoercer
                raise ProgrammerError('constructor already set')
        return self

    def __call__(self, *args, **kwargs):    # type(*args, **kwargs)
        # create a new instance using the constructor
        if self.hasT:
            raise TypeError(f'{self} has a T so cannot be an instance type')
        if self._constructor:
            if args and isinstance(args[0], Constructors):
                cs = args[0]
                cs.append(self)
                return self._constructor(cs, *args[1:], **kwargs)
            else:
                cs = Constructors()
                cs.append(self)
                return self._constructor(cs, *args, **kwargs)
        else:
            raise ProgrammerError(f'No constructor defined for type "{self}"')


    # SET OPERATION BASED CONSTRUCTION OF TYPES

    # unions - +
    def __add__(self, rhs):         # type + rhs
        if not isinstance(rhs, (BType, type)):
            raise TypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        return BTUnion(self, rhs)

    def __radd__(self, lhs):        # lhs + type
        if not isinstance(lhs, (BType, type)):
            raise TypeError(f'lhs should be a BType or type - got {repr(lhs)}')
        return BTUnion(lhs, self)

    # products - tuples - *
    def __mul__(self, rhs):         # type * rhs
        if not isinstance(rhs, (BType, type)):
            raise TypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        types = \
            (self.types if isinstance(self, BTTuple) else (self,)) + \
            (rhs.types if isinstance(rhs, BTTuple) else (rhs,))
        return BTTuple(*types)

    def __rmul__(self, lhs):        # lhs * type
        if not isinstance(lhs, (BType, type)):
            raise TypeError(f'lhs should be a BType or type - got {repr(lhs)}')
        types = \
            (lhs.types if isinstance(lhs, BTTuple) else (lhs,)) + \
            (self.types if isinstance(self, BTTuple) else (self,))
        return BTTuple(*types)

    # finite size exponentials - lists and maps - **
    def __pow__(self, rhs):         # type ** rhs
        if not isinstance(rhs, (BType, type)):
            raise TypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        if self in BType._arrayOrdinalTypes:
            return BTSeq(self, rhs)
        else:
            return BTMap(self, rhs)

    def __rpow__(self, lhs):        # lhs ** type
        if not isinstance(lhs, (BType, type)):
            raise TypeError(f'lhs should be a BType or type - got {repr(lhs)} - has a type been overridden?')
        if lhs in BType._arrayOrdinalTypes:
            return BTSeq(lhs, self)
        else:
            return BTMap(lhs, self)

    # general exponentials - functions - ^
    def __xor__(self, rhs):         # type ^ rhs
        if not isinstance(rhs, (BType, type)):
            raise TypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        return BTFn(self if isinstance(self, BTTuple) else BTTuple(self), rhs)

    def __rxor__(self, lhs):        # lhs ^ type
        if isinstance(lhs, BTTuple):
            tArgs = lhs
        elif isinstance(lhs, (BType, type)):
            tArgs = (lhs,)
        elif isinstance(lhs, (list, tuple)):
            tArgs = lhs
        elif isinstance(lhs, iterType):
            tArgs = tuple(lhs)
        else:
            raise TypeError(f'lhs should be a BType, type, list or tuple - got {repr(lhs)}')
        return BTFn(tArgs, self)

    # intersections - &
    def __and__(self, rhs):         # type & rhs
        if not isinstance(rhs, (BType, type)):
            raise TypeError(f'rhs should be a BType or type - got {repr(rhs)}')
        if self.__class__ is BTFn:
            return BTOverload(self, rhs)
        else:
            return BTIntersection(self, rhs)

    def __rand__(self, lhs):        # lhs & type
        if not isinstance(lhs, (BType, type)):
            raise TypeError(f'lhs should be a BType or type - got {repr(lhs)}')
        if self.__class__ is BTFn:
            return BTOverload(lhs, self)
        else:
            return BTIntersection(lhs, self)

    # intersection - []
    def __getitem__(self, rhs):     # type[rhs]
        if isinstance(rhs, int):
            # get's called by dict_keys | btype
            raise TypeError('perhaps dict_keys | btype?')
        if isinstance(rhs, tuple):
            return BTIntersection(self, *rhs)
        elif isinstance(rhs, str):
            name = rhs
            tag = BTAtom.ensure(f'_{name}')         # checks that there is no name conflict
            instance = BTIntersection(self, tag)
            if instance.name is Missing:
                instance.nameAs(name)
            else:
                if instance.name != name:
                    ProgrammerError()
            return instance
        else:
            if self.__class__ is BTFn:
                return BTOverload(self, rhs)
            else:
                return BTIntersection(self, rhs)

    # intersection - +, -
    def __pos__(self):              # +type
        return _AddStuff(self)

    def __neg__(self):              # -type
        return _SubtractStuff(self)


    # QUERYING

    def __len__(self):
        return 1            # all non-union types are a union of length 1

    def __contains__(self, item):
        return item == self

    def __hash__(self):
        return self.id

    def __eq__(self, rhs):
        return isinstance(rhs, self.__class__) and self.id == rhs.id


    # DISPLAY

    def setPP(self, pp):
        self._pp = pp
        return self

    def __str__(self):
        return self.__repr__()

    def ppName(self):
        if not context.showFullType:
            if a := self._pp:
                return a, False, False
            elif a := self.name:
                return a, False, False
        return Missing

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

    def __new__(cls, name):
        # gets a type throwing an error if it has not already been defined
        if (instance := _BTAtomByName.get(name, Missing)) is Missing:
            raise TypeError(f'Unknown type "{name}"')
        return instance

    @classmethod
    def define(cls, name):
        if name in _BTAtomByName:
            raise TypeError(f'{name} is already defined')
        instance = cls._define().nameAs(name)
        _BTAtomByName[name] = instance
        return instance

    @classmethod
    def ensure(cls, name):
        # creates a new type if one does not already exists with the provided name
        if (instance := _BTAtomByName.get(name, Missing)) is Missing:
            if name in _BTypeByName: raise TypeError(f'{name} is already defined')
            instance = cls._define().nameAs(name)
            _BTAtomByName[name] = instance
        return instance

    def ppName(self):
        return self.name, False, False



class BTSchemaVariable(BTAtom):
    # T1, T2, etc - NB: the term schema means a model / schematic whereas the term scheme means a plan of action

    __slots__ = ['subscript', 'base']

    @classmethod
    def define(cls, name):
        if name in _BTAtomByName or name in _BTypeByName:
            raise TypeError(f'{name} is already defined')
        instance = cls._define().nameAs(name)
        instance.subscript = Missing
        instance.base = instance
        _BTAtomByName[name] = instance
        return instance

    @classmethod
    def ensure(cls, name):
        raise NotImplementedError('ensure is not allowed')

    def ensure(self, subscript):
        name = self.name + subscript.name
        if (instance := _BTAtomByName.get(name, Missing)) is Missing:
            assert isinstance(subscript, BTAtom)
            assert self.subscript is Missing
            instance = BTSchemaVariable.define(name)
            instance.subscript = subscript
            instance.base = self
            instance.hasT = self.hasT
        return instance



class _BTSetOp(BType):

    __slots__ = ['types']
    def __eq__(self, rhs):
        return isinstance(rhs, self.__class__) and ((self.id == rhs.id) or (self.types == rhs.types))
    def __hash__(self):
        return self.id  # see https://stackoverflow.com/questions/53518981/inheritance-hash-sets-to-none-in-a-subclass



class BTUnion(_BTSetOp):
    # union of two or more types
    _typeByTypes = {}

    def __new__(cls, *types):
        if len(types) == 0:
            raise ProgrammerError('No types provided')
        if len(types) == 1: return types[0]
        types, flags = _sortedUnionTypes(types)
        if len(types) == 1:
            return types[0]
        if (instance := cls._typeByTypes.get(types, Missing)) is Missing:
            instance = super()._define()
            instance.types = types
            instance.hasT = flags.hasT
            instance.familial = flags.familial
            instance.explicit = flags.explicit
            instance.orthogonal = flags.orthogonal
            cls._typeByTypes[types] = instance
        return instance

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



class BTIntersection(_BTSetOp):
    # intersection of two or more types
    _typeByTypes = {}

    def __new__(cls, *types):
        if len(types) == 0:
            raise ProgrammerError('No types provided')
        if len(types) == 1:
            return types[0]
        types, flags = _sortedIntersectionTypes(types, cls is BTIntersection)
        if len(types) == 1:
            return types[0]
        if (instance := cls._typeByTypes.get(types, Missing)) is Missing:
            if isinstance(types[0], BTFn):
                for t in types:
                    if not isinstance(types[0], BTFn):
                        raise TypeError("Only BTFns allow in an overload")
            instance = super()._define()
            instance.types = types
            instance.hasT = flags.hasT
            instance.orthogonal = flags.orthogonal
            cls._typeByTypes[types] = instance
        return instance

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
            pp, compound, childCompound = ppT(t)
            ts.append(f'({pp})' if compound else pp)
            hasCompound = hasCompound or compound
        return (' & ' if hasCompound else '&').join(ts), True, hasCompound



class BTOverload(BTIntersection):

    def ppT(self):
        if a := self.ppName(): return a
        ts = []
        hasCompound = False
        for t in self.types:
            pp, compound, childCompound = ppT(t)
            ts.append(f'({pp})' if compound and childCompound else pp)
            hasCompound = hasCompound or compound
        return ' & '.join(ts), True, hasCompound



class _Flags(object):
    def __init__(self):
        self.hasActualT = False
        self.hasT = False
        self.familial = False
        self.explicit = False
        self.orthogonal = False


def _sortedUnionTypes(types):
    flags = _Flags()
    if len(types) == 1:
        _updateFlagsForUnion(types[0], flags)
        return types
    collated = []
    for t in types:
        if isinstance(t, BTUnion):            # BTUnion is a subclass of BType so this must come before BType
            collated.extend(t.types)
            [_updateFlagsForUnion(e, flags) for e in t.types]
        elif isinstance(t, (BType, type)):
            collated.append(t)
            _updateFlagsForUnion(t, flags)
        else:
            for e in t:
                if isinstance(e, BTUnion):    # BTUnion is a subclass of BType so this must come before BType
                    collated.extend(e.types)
                    [_updateFlagsForUnion(e, flags) for r in t.types]
                elif isinstance(e, (BType, type)):
                    collated.append(e)
                    _updateFlagsForUnion(t, flags)
                else:
                    raise TypeError()
    collated.sort(key=_typeId)
    compacted = [collated[0]]                  # add the first
    for i in range(1, len(collated)):       # from the second to the last, if each is different to the prior add it
        if collated[i] != collated[i-1]:
            compacted.append(collated[i])
    return tuple(compacted), flags

def _updateFlagsForUnion(t, flags):
    if isinstance(t, BType):
        if t.hasT:
            flags.hasT = True


def _sortedIntersectionTypes(types, singleSV):
    flags = _Flags()
    if len(types) == 1:
        _updateFlagsForIntersection(types[0], flags, singleSV)
        return types, flags
    collated = []
    for t in types:
        if isinstance(t, BTIntersection):            # BTIntersection is a subclass of BType so this must come first
            collated.extend(t.types)
            [_updateFlagsForIntersection(e, flags, singleSV) for e in t.types]
        elif isinstance(t, (BType, type)):
            collated.append(t)
            _updateFlagsForIntersection(t, flags, singleSV)
        else:
            for e in t:
                if isinstance(e, BTIntersection):    # BTIntersection is a subclass of BType so this must come first
                    collated.extend(e.types)
                    [_updateFlagsForIntersection(e, flags, singleSV) for r in t.types]
                elif isinstance(e, (BType, type)):
                    collated.append(e)
                    _updateFlagsForIntersection(t, flags, singleSV)
                else:
                    raise TypeError()
    collated.sort(key=lambda t: t.id if isinstance(t, BType) else hash(t))
    compacted = [collated[0]]  # add the first
    for i in range(1, len(collated)):  # from the second to the last, if each is different to the prior add it
        if collated[i] != collated[i - 1]:
            compacted.append(collated[i])
    return tuple(compacted), flags

def _updateFlagsForIntersection(t, flags, singleSV):
    if isinstance(t, BType):
        if isT(t):
            if flags.hasActualT and singleSV:
                raise TypeError('Can only have one actual T in an intersection')
            flags.hasActualT = True
            flags.hasT = True
        elif t.hasT:
            flags.hasT = True
        if t.orthogonal:
            if (flags.orthogonal and flags.orthogonal is not t) and singleSV:
                raise TypeError('Can only have one orthogonal type in an intersection')
            flags.orthogonal = t
    else:
        # all python types are orthogonal
        if (flags.orthogonal and flags.orthogonal is not t) and singleSV:
            raise TypeError('Can only have one orthogonal in an intersection')
        flags.orthogonal = t


class _AddStuff(object):
    def __init__(self, t):
        self.t = t
    def __ror__(self, instance):    # instance | type
        return instance | BTIntersection(instance._t if hasattr(instance, '_t') else builtins.type(instance), self.t)

class _SubtractStuff(object):
    def __init__(self, t):
        self.t = t
    def __ror__(self, instance):  # instance | type
        if not isinstance(t := instance._t if hasattr(instance, '_t') else builtins.type(instance), BTIntersection):
            raise TypeError(f'Can only subtract a type from an intersection but LHS type is {t}')
        a_, ab, b_, weakenings = _partition(
            t.types,
            self.t.types if isinstance(self.t, BTIntersection) else (self.t, )
        )
        if b_:
            raise TypeError(f"RHS is trying to subtract {b_} which isn't in the LHS")
        if not ab:
            raise ProgrammerError(f"Can't end up subtracting nothing")
        if not a_:
            raise TypeError("Left with null set")
        return instance | (a_[0] if len(a_) == 1 else BTIntersection(*a_))



class BTTuple(BType):
    # product type accessed by ordinal
    _BTTupleByTypes = {}

    def __new__(cls, *types):
        # allow empty tuple and tuple of one
        if (instance := cls._BTTupleByTypes.get(types, Missing)) is Missing:
            instance = super()._define()
            instance.types = types
            instance.hasT = _anyHasT(*types)
            cls._BTTupleByTypes[types] = instance
        return instance

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
    _BTStructByTypes = {}

    def __new__(cls, *args, **kwargs):
        if args:
            if len(args) == 1 and isinstance(args[0], dict):
                names = tuple(args[0].keys())
                types = tuple(args[0].values())
                typeByName = dict(zip(names, types))
            elif len(args) == 2 and isinstance(args[0], (tuple, list)) and isinstance(args[1], (tuple, list)):
                names = tuple(args[0])
                types = tuple(args[1])
                typeByName = dict(zip(names, types))
            else:
                raise TypeError('Unhandled case')
        else:
            names = tuple(kwargs.keys())
            types = tuple(kwargs.values())
            typeByName = kwargs
        if len(names) != len(types):
            raise TypeError('names and tyoes must be of same length')
        if (instance := cls._BTStructByTypes.get((names, types), Missing)) is Missing:
            instance = super()._define()
            instance.typeByName = typeByName
            instance.hasT = _anyHasT(*types)
            cls._BTStructByTypes[(names, types)] = instance
        return instance

    @property
    def names(self):
        return self.typeByName.keys()

    def ppT(self):
        if a := self.ppName(): return a
        ts = []
        hasCompound = False
        for i, (name, t) in enumerate(self.typeByName.items()):
            pp, compound, childCompound = ppT(t)
            ts.append(f'{name}:{pp}')
            hasCompound = hasCompound or compound
        return f'{{{", ".join(ts)}}}', False, hasCompound

S = BTStruct



class BTSeq(BType):
    # homogenous discrete / finite map (exponential) type accessed by ordinal - i.e. N**T, 3**T etc
    _BTSeqByTypes = {}

    def __new__(cls, ordinalType, mappedType):
        if not ordinalType in cls._arrayOrdinalTypes:
            raise TypeError(f'First arg must be an ordinal type placeholder, got {ordinalType}')
        types = (ordinalType, mappedType)
        if (instance := cls._BTSeqByTypes.get(types, Missing)) is Missing:
            instance = super()._define()
            instance.indexType = ordinalType
            instance.mappedType = mappedType
            instance.hasT = _anyHasT(*types)
            cls._BTSeqByTypes[types] = instance
        return instance

    def ppT(self):
        if a := self.ppName(): return a
        pp1, compound1, childCompound1 = ppT(self.indexType)
        pp2, compound2, childCompound2 = ppT(self.mappedType)
        if compound1 and childCompound1: pp1 = f'({pp1})'
        if compound2 and childCompound2: pp2 = f'({pp2})'
        return f'{pp1}**{pp2}', True, False



class BTMap(BType):
    # homogenous discrete / finite map (exponential) type accessed by key - e.g. T2**T1 T1->T2
    _BTMapByTypes = {}

    def __new__(cls, indexType, mappedType):
        types = (indexType, mappedType)
        if (instance := cls._BTMapByTypes.get(types, Missing)) is Missing:
            instance = super()._define()
            instance.indexType = indexType
            instance.mappedType = mappedType
            instance.hasT = _anyHasT(*types)
            cls._BTMapByTypes[types] = instance
        return instance

    def ppT(self):
        if a := self.ppName(): return a
        pp1, compound1, childCompound1 = ppT(self.indexType)
        pp2, compound2, childCompound2 = ppT(self.mappedType)
        if compound1: pp1 = f'({pp1})'
        if compound2: pp2 = f'({pp2})'
        return f'{pp1}**{pp2}', True, False



class BTFn(BType):
    # homogenous, generalised and potentially infinite exponential type - aka function
    BTFnByTypes = {}

    def __new__(cls, tArgs, tRet):
        if not isinstance(tArgs, BTTuple):
            tArgs = BTTuple(*tArgs)
        types = (tArgs, tRet)
        if (instance := cls.BTFnByTypes.get(types, Missing)) is Missing:
            instance = super()._define()
            instance.tArgs = tArgs
            instance.tRet = tRet
            instance.hasT = _anyHasT(tArgs, tRet)  # either a BTTuple or a single type
            cls.BTFnByTypes[types] = instance
        return instance

    def ppT(self):
        if a := self.ppName(): return a
        pp1, compound1, childCompound1 = ppT(self.tArgs)
        pp2, compound2, childCompound2 = ppT(self.tRet)
        if compound1 and childCompound1: pp1 = f'({pp1})'
        if compound2 and childCompound2: pp2 = f'({pp2})'
        return f'{pp1}{" ^ " if (compound1 or compound2) else "^"}{pp2}', True, compound1 or compound2

    @property
    def numargs(self):
        return len(self.tArgs.types)



def ppT(t):
    return (t.__name__, False, False) if isinstance(t, type) else t.ppT()

def _anyHasT(*types):
    for t in types:
        if hasattr(t, 'hasT') and t.hasT:
            return True
    return False

def _typeId(t):
    # potentially with a lot of types we could get a clash between the BType id and hash - ignore for the moment!!!
    return t.id if isinstance(t, BType) else hash(t)

_weakenings = {}

def weaken(srcTs, targetTs):
    if not isinstance(srcTs, tuple): srcTs = [srcTs]
    if not isinstance(targetTs, tuple): targetTs = [targetTs]
    for srcT in srcTs:
        current = _weakenings.get(srcT, ())
        for targetT in targetTs:
            if targetT not in current:
                current += (targetT,)
        _weakenings[srcT] = current

_ = Missing

_fitsCache = {}

U_U = 1
I_U = 2
O_U = 3
I_I = 4
U_I = 5
O_I = 6
U_O = 7
I_O = 8
O_O = 9

SCHEMA_PENALTY = 0.5

def fitsWithin(a, b, TRACE=False, fittingSigs=False):
    # answers a tuple {cacheID, doesFit, tByT, distance}

    # a must be a concrete type
    if hasattr(a, 'hasT') and a.hasT:
        if isinstance(a, BTFn) and isinstance(b, BTFn):
            fittingSigs = True
        if not fittingSigs:
            raise TypeError(f'LHS type ({a}) is polymorphic and thus cannot match RHS type {b}')

    distance = 0

    if isinstance(b, type):
        if a.__class__ == BTIntersection:
            # (txt & ISIN) fitsWithin (txt) etc
            cacheId = (a.id, b)


        else:
            # buildins.str fitsWithin buildins.str
            return (_, a == b, _, distance)
    else:
        if isinstance(a, BType):
            if a.id == b.id:
                # num fitsWithin num
                return (_, True, _, distance)
            cacheId = (a.id, b.id)
        else:
            if not isinstance(a, type):
                raise TypeError(f"a is type {a.__class__}")
            cacheId = (a, b.id)


    # check the cache - get prior tByT as well as the result
    cached = _fitsCache.get(cacheId, Missing)
    if cached is not Missing:
        doesFit, tByT, distance = cached
        return (_, doesFit, tByT, distance)

    tByT = {}

    if isinstance(b, BTSchemaVariable):
        if b.base is T:
            # anything (except explicits) fitsWithin a wildcard
            if (hasattr(a, 'explicit') and a.explicit) or (a.__class__ == BTIntersection and _anyExplicit(a.types)):
                return (cacheId, False, _, _)
            else:
                return (cacheId, True, {b:a}, distance + SCHEMA_PENALTY)  # exact match must beat wildcard
        elif isinstance(a, BTSchemaVariable):
            if a.base.id == b.base.id:
                # N1 fitsWithin Na
                return (cacheId, True, tByT, distance)
            else:
                return (cacheId, False, _, _)
        else:
            return (cacheId, False, _, _)


    # check the coercions
    if (o:=_find(b, _weakenings.get(a, ()))) >= 0:
        return (cacheId, True, tByT, distance + o + 1)

    # NB for locality it would be nice to be able to define behaviour and reuse it rather than repeating
    # the code but in a light touch way than writing a function that needs comprehending elsewhere (kinda
    # like a named gosub), e.g.
    # fred
    #     ifTrue: { } :blockA
    #     ifFalse: {xyz. blockA[]}
    # maybe...


    if isinstance(b, BTUnion):
        if isinstance(a, BTUnion):          # U U
            # (str+num) fitsWithin (str+num+int)
            case = U_U      # every a must fit in b
        elif a.__class__ == BTIntersection: # I U
            # (num+str) & fred  fitsWithin  (num+str)
            # (num&fred) fitsWithin (num&fred) + (str&joe)
            case = I_U
        else:                               # O U
            case = O_U      # a just needs to fit any in b

    elif b.__class__ == BTIntersection:
        if isinstance(a, BTUnion):          # U I
            # if an element in a is b we have a partial fit
            # (num&fred) + (str&joe)  fitsWithin  (num&fred)
            return (cacheId, False, _, _)
        elif a.__class__ == BTIntersection: # I I
            # (matrix & square & btup) fitsWithin (matrix & btup & aliased)
            case = I_I
        else:                               # O I
            # str fitsWithin (str&aliased)    (remember aliased is implicit)
            case = O_I

    else:
        if isinstance(a, BTUnion):          # U O
            # if an element in a is b we have a partial fit (num + err) fitsWithin (num)
            # also   (index ^ index) + (str ^ str)  fitsWithin  (T1 ^ T2)
            # and    (index & square) + (index & circle)  fitsWithin  (index)
            for t in a.types:
                doesFit, local_tByT, distance = cacheAndUpdate(fitsWithin(t, b, TRACE, fittingSigs), dict(tByT), distance)
                if not doesFit: return (cacheId, False, _, _)
            return (cacheId, True, tByT, distance)
        elif a.__class__ == BTIntersection: # I O
            case = I_O
        else:                               # O O
            case = O_O


    if case == O_O:
        pass

    elif case == U_U:
        # every a must fit in b
        for t in a.types:
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(t, b, TRACE, fittingSigs), tByT, distance)
            if not doesFit: return (cacheId, False, _, _)
        return (cacheId, True, tByT, distance)

    elif case == O_U:
        # a just needs to fit any in b
        for t in b.types:
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(a, t, TRACE, fittingSigs), tByT, distance)
            if doesFit: return (cacheId, True, tByT, distance)
        return (cacheId, False, _, distance)

    elif case == I_U:
        # two cases
        # 1 - intersection is a union member - (num&fred) nfitsWithin  (num&fred) + (str&joe)
        for t in b.types:
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(a, t, TRACE, fittingSigs), tByT, distance)
            if doesFit: return (cacheId, True, tByT, distance)
        # 2 - intersecting the union with another type - (num+str) & fred  fitsWithin  (num+str)
        a_, ab, b_, weakenings = _partition(a.types, (b,))
        if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
            return (cacheId, False, _, _)  # i.e. there is something missing in a that is required by b
        if len(a_) == 0:                          # exact match is always fine
            raise PathNotTested()
            return (cacheId, True, tByT, 0 + len(weakenings))
        else:
            raise PathNotTested()
            return _processA_(a_, cacheId, tByT, len(weakenings))

    elif case == I_I:
        if b.hasT:
            Ts, bTypes, bTypesHasT = _inject(b.types, {'Ts':[], 'other':[], 'otherHasT': False}, _THasTOther)
            if len(Ts) > 1:
                raise ProgrammerError('Intersection has more than one T - should not even be possible to construct that')
            if len(Ts) == 0 or bTypesHasT:
                # potentially out of order - e.g. ((N ** ccy) & list) fitsWithIn (T2 & (N ** T1))
                # N log N process? as cross matching is required and need to choose shortest distance for T1, T2 etc

                a_, ab, b_ = _partitionWithT(a.types, bTypes, TRACE, fittingSigs)
                if b_:
                    if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
                        return (cacheId, False, _, _)  # i.e. there is something missing in a that is required by b
                    raise PathNotTested()
                # check no conflicts for any T
                for ta, tb, tByT_, distance_ in ab:
                    distance += distance_
                    for TNew, tNew in tByT_.items():
                        t = tByT.get(TNew, Missing)
                        if t is not Missing:
                            if tNew is not t and t not in _weakenings.get(tNew, ()):
                                if tNew in _weakenings.get(t, ()):
                                    raise PathNotTested()
                                    tByT[TNew] = tNew
                                else:
                                    raise PathNotTested()
                                    return (cacheId, False, _, _)   # conflict found
                        else:
                            tByT[TNew] = tNew
                if len(a_) == 0:  # exact match is always fine
                    if len(Ts) ==1:
                        return (cacheId, False, _, _)
                    return (cacheId, True, tByT, distance)
                else:
                    if len(Ts) == 0:
                        # a match but a simple type from the intersection is dropped and we'd prefer that it was caught
                        distance += 1
                    else: # len(Ts) == 1:
                        # add the match to tByT - distance is the usual SCHEMA_PENALTY for a T match
                        matchedT = a_[0] if len(a_) == 1 else BTIntersection(*a_)
                        tByT[Ts[0]] = matchedT
                        distance += SCHEMA_PENALTY
                    return _processA_(a_, cacheId, tByT, distance + len(a_))

            else: # len(Ts) == 1:
                # (str & ISIN) >> check >> fitsWithin >> (str & T1)
                a_, ab, b_, weakenings = _partition(a.types, bTypes)
                if b_:
                    if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
                        return (cacheId, False, _, _)  # i.e. there is something missing in a that is required by b
                if len(a_) == 0:
                    # (str & ISIN) >> check >> fitsWithin >> (str & ISIN & T) - T is nullset - not fine
                    return (cacheId, False, _, _)  # i.e. there is something missing in a that is required by b
                else:
                    # wildcard match is fine, metric is SCHEMA_PENALTY to loose against exact match
                    matchedT = a_[0] if len(a_) == 1 else BTIntersection(*a_)
                    return (cacheId, True, {Ts[0]: matchedT}, SCHEMA_PENALTY + len(weakenings) + len(a_))
        else:
            a_, ab, b_, weakenings = _partition(a.types, b.types)
            if _anyNotImplicit(b_):         # check for (matrix) fitsWithin (matrix & aliased) etc
                return (cacheId, False, _, _)   # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return (cacheId, True, tByT, 0 + len(weakenings))
            else:
                return _processA_(a_, cacheId, tByT, len(weakenings) + len(a_))

    elif case == I_O:
        # isT(b) has already been handled above in the BTSchemaVariable check
        # (num & col) fitsWithin (num)
        a_, ab, b_, weakenings = _partition(a.types, (b,))
        if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
            return (cacheId, False, _, _)  # i.e. there is something missing in a that is required by b
        if len(a_) == 0:                          # exact match is always fine
            return (cacheId, True, tByT, 0 + len(weakenings))
        else:
            return _processA_(a_, cacheId, tByT, len(weakenings) + len(a_))

    elif case == O_I:
        # str fitsWithin (str&aliased)    (remember aliased is implicit)
        if b.hasT:
            # MUSTDO handle wildcards properly
            a_, ab, b_, weakenings = _partition((a,), b.types)
            if b_:
                if len(b_) == 1 and isT(b_[0]) and len(a_) > 0:
                    # wildcard match is always fine, metric is SCHEMA_PENALTY to loose against exact match
                    matchedT = a_[0] if len(a_) == 1 else BTIntersection(*a_)
                    return (cacheId, True, {b_[0]: matchedT}, SCHEMA_PENALTY + len(weakenings) + len(a_))
                if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
                    return (cacheId, False, _, _)  # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return (cacheId, True, tByT, 0 + len(weakenings))
            else:
                return _processA_(a_, cacheId, tByT, len(weakenings) + len(a_))
        else:
            a_, ab, b_, weakenings = _partition((a,), b.types)
            if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
                return (cacheId, False, _, _)  # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return (cacheId, True, tByT, 0 + len(weakenings))
            else:
                return _processA_(a_, cacheId, tByT, len(weakenings) + len(a_))

    else:
        raise ProgrammerError()


    if isinstance(a, BTFn):
        if isinstance(b, BTFn):
            if a.numargs != b.numargs:
                return (cacheId, False, _, _)

            # we have agreed to handle b and we are checking if a is up to the task of being substitutable with b
            # i.e. is a <: b
            # consider  b : (i+t,    t)   -> b+n         b can take i+t in arg1 and t in arg2 and won't output more than b+n
            #                 /\     /\       \/
            #           a : (i+t+s,  t+s) ->  n          a can take in more in arg1, and arg2 and will output less - therefore it fits

            if isinstance(b.tRet, BTSchemaVariable):
                doesFit, tByT, distance = cacheAndUpdate((cacheId, True, {b.tRet:a.tRet}, SCHEMA_PENALTY), tByT, distance)
            elif isinstance(a.tRet, BTSchemaVariable):
                # e.g. T1 < txt or T1 < T1 - discard the info as it really needs some deeper analysis
                doesFit, tByT, distance = cacheAndUpdate((cacheId, True, {}, 0), tByT, distance)
            else:
                doesFit, tByT, distance = cacheAndUpdate(fitsWithin(a.tRet, b.tRet, TRACE, fittingSigs), tByT, distance)
            if not doesFit:
                # print(f'{a} <: {b} is false')
                return (cacheId, False, _, _)

            for aT, bT in zip(a.tArgs, b.tArgs):
                if isinstance(bT, BTSchemaVariable):
                    doesFit, tByT, distance = cacheAndUpdate((cacheId, True, {bT: aT}, SCHEMA_PENALTY), tByT, distance)
                elif isinstance(aT, BTSchemaVariable):
                    # e.g. T1 < txt or T1 < T1 - discard the info as it really needs some deeper analysis
                    doesFit, tByT, distance = cacheAndUpdate((cacheId, True, {}, 0), tByT, distance)
                else:
                    doesFit, tByT, distance = cacheAndUpdate(fitsWithin(bT, aT, TRACE, fittingSigs), tByT, distance)
                if not doesFit:
                    # print(f'{a} <: {b} is false')
                    return (cacheId, False, _, _)

            # there may be additional checks here
            # print(f'{a} <: {b} is true')
            return (cacheId, True, tByT, distance)

        elif isinstance(a, BTOverload):
            # we don't do soft typing in coppertop
            return (cacheId, False, _, _)

        else:
            return (cacheId, False, _, _)

    elif isinstance(a, BTOverload):
        if isinstance(b, BTFn):
            # must be a fit for one of a with b
            for aT in a.types:
                doesFit, local_tByT, distance = cacheAndUpdate(fitsWithin(aT, b, TRACE, fittingSigs), dict(tByT), distance)
                if doesFit: break
            if doesFit:
                return (cacheId, True, tByT, distance)
            else:
                return (cacheId, False, _, _)

        elif isinstance(b, BTOverload):
            # a must fit with every one of b
            for bT in b.types:
                doesFit, local_tByT, distance = cacheAndUpdate(fitsWithin(a, bT, TRACE, fittingSigs), dict(tByT), distance)
                if not doesFit: return (cacheId, False, _, _)
            return (cacheId, True, tByT, distance)

        else:
            return (cacheId, False, _, _)

    elif type(a) is not type(b):
        # the two types are not the same so they cannot fit (we don't allow inheritance - except in case of Ordinals)
        if a in BType._arrayOrdinalTypes and b in BType._arrayOrdinalTypes:
            return (cacheId, True, tByT, distance)
        else:
            return (cacheId, False, _, _)

    elif isinstance(b, BTAtom):
        # already a.id != b.id so must be False
        return (cacheId, False, _, _)

    elif isinstance(b, BTTuple):
        aTs, bTs = a.types, b.types
        if len(aTs) != len(bTs): return (cacheId, False, _, _)
        for i, aT in enumerate(aTs):
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(aT, bTs[i], TRACE, fittingSigs), tByT, distance)
            if not doesFit: return (cacheId, False, _, _)
        return (cacheId, True, tByT, distance)

    elif isinstance(b, BTStruct):
        # b defines what is required, a defines what is available
        # iterate through b's names and check if they are available in a
        aF2T, bF2T = a.typeByName, b.typeByName
        if len(aF2T) < len(bF2T): return (cacheId, False, _, _)
        for bf, bT in bF2T.items():
            aT = aF2T.get(bf, Missing)
            if aT is Missing: return (cacheId, False, _, _)
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(aT, bT, TRACE, fittingSigs), tByT, distance)
            if not doesFit: return (cacheId, False, _, _)
        return (cacheId, True, tByT, distance)

    elif isinstance(b, (BTSeq, BTMap)):
        doesFit1, tByT, distance = cacheAndUpdate(fitsWithin(a.indexType, b.indexType, TRACE, fittingSigs), tByT, distance)
        if not doesFit1: return (cacheId, False, _, _)
        doesFit2, tByT, distance = cacheAndUpdate(fitsWithin(a.mappedType, b.mappedType, TRACE, fittingSigs), tByT, distance)
        if not doesFit2: return (cacheId, False, _, _)
        return (cacheId, True, tByT, distance)

    else:
        raise ProgrammerError(f'Unhandled case {a} <: {b}')


def _inject(xs, acc, fn):
    for x in xs:
        acc = fn(x, acc)
    return acc.values()

def _THasTOther(t, acc):
    if isT(t):
        acc['Ts'].append(t)
    else:
        acc['other'].append(t)
        acc['otherHasT'] = acc['otherHasT'] or hasT(t)
    return acc

def _anyNotImplicit(ts):
    for t in ts:
        if t not in _implicitTypes:
            return True
    return False

def _anyExplicit(ts):
    for t in ts:
        if isinstance(t, BType) and t.explicit:
            return True
    return False

def _processA_(a_, cacheId, tByT, lenWeakenings):
    exclusiveCount = 0
    for ta in a_:
        if isinstance(ta, BType):
            if ta.familial:
                implicitWeakenings = [tw for tw in _weakenings.get(ta, ()) if tw in _implicitTypes]
                if not implicitWeakenings:
                    return (cacheId, False, _, _)
            elif ta.explicit:
                return (cacheId, False, _, _)
            elif ta.orthogonal:
                exclusiveCount += 1
        else:
            exclusiveCount += 1
    if exclusiveCount > 1:
        raise TypeError()
    return (cacheId, True, tByT, len(a_) + lenWeakenings)


def cacheAndUpdate(result, tByT, distance=Missing):
    cacheId, doesFit, tByTNew, distance_ = result
    if doesFit:
        if distance is Missing:
            distance = distance_
        elif distance_ is Missing:
            # MUSTDO get to bottom of this
            distance = distance
        else:
            distance = distance + distance_
    if cacheId:
        _fitsCache[cacheId] = doesFit, tByTNew, distance
    if doesFit and tByTNew:
        updates = {}
        for TNew, tNew in tByTNew.items():
            if TNew is not T:
                t = tByT.get(TNew, Missing)
                if t is not Missing:
                    if tNew is not t and t not in _weakenings.get(tNew, ()):
                        if tNew in _weakenings.get(t, ()):
                            updates[TNew] = tNew
                        else:
                            doesFit = False
                            break
                else:
                    updates[TNew] = tNew
        if doesFit and updates:
            tByT = dict(tByT)
            tByT.update(updates)
    return doesFit, tByT, distance

def _partitionWithT(a:tuple, b:tuple, TRACE=False, fittingSigs=False):
    ab = []
    potentialsByA, potentialsByB = {}, {}
    remainingATypes = list(a)
    remainingBTypes = list(b)
    for ai, ta in enumerate(remainingATypes):
        for bi, tb in enumerate(remainingBTypes):
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(ta, tb, TRACE, fittingSigs), {}, 0)  # handles weakenings
            if doesFit:
                if distance == 0:
                    ab.append((ta, tb, tByT, 0))
                    remainingATypes[ai] = Missing
                    del remainingBTypes[bi]
                    break
                else:
                    potentialsByA.setdefault(ta, []).append((tb, tByT, distance))
                    potentialsByB.setdefault(tb, []).append((ta, tByT, distance))
    # if any bt fits more than one a we might have a problem
    # but for the moment just check that each potential A and B has length 1
    a_ = {at:at for at in remainingATypes if at is not Missing}
    b_ = {bt:bt for bt in remainingBTypes}
    for ta, potentials in potentialsByA.items():
        if len(potentials) > 1:
            raise NotYetImplemented()
        else:
            tb, tByT, distance = potentials[0]
            ab.append((ta, tb, tByT, distance))
            del a_[ta]
    for tb, potentials in potentialsByB.items():
        if len(potentials) > 1:
            raise NotYetImplemented()
        else:
            del b_[tb]
    return tuple(a_.values()), tuple(ab), tuple(b_.values())


def _partition(A:tuple, B:tuple):
    # B intersect A' - stuff in B but not in A - anything here then it's not a fit
    # B intersect A - common stuff, if we only have common stuff then it's an exact fit
    # B' intersect A - stuff in A but not in B - we term this the residual
    iA, iB = 0, 0
    nA, nB = len(A), len(B)
    nAB = min(nA, nB)
    outA, outAB, outB = [Missing] * nA, [Missing] * nAB, [Missing] * nB
    oA, oAB, oB = 0, 0, 0
    while True:
        tA, tB = A[iA], B[iB]
        idA , idB = _typeId(tA), _typeId(tB)       # if this turns out to be slow we can always just use BTypes
        if idA == idB:
            outAB[oAB] = tA
            oAB += 1
            iA += 1
            iB += 1
            if oAB == nAB or iA == nA or iB == nB: break
        elif idA < idB:
            outA[oA] = tA
            oA += 1
            iA += 1
            if oA == nA or iA == nA: break
        else:
            outB[oB] = tB
            oB += 1
            iB += 1
            if oB == nB or iB == nB: break
    if (iA + 1) <= nA:
        for iA in range(iA, nA):
            outA[oA] = A[iA]
            oA += 1
    if (iB + 1) <= nB:
        for iB in range(iB, nB):
            outB[oB] = B[iB]
            oB += 1
    # check if any weakenings of types in AB' match A'B
    weakenings = {}
    anyFound = False
    if oAB < nAB:
        for iA, tA in enumerate(outA):
            if not tA: break
            found = False
            for ctA in _weakenings.get(tA, ()):
                for iB, tB in enumerate(outB):
                    if ctA == tB:
                        found = True
                        break
                if found: break
            if found:
                anyFound = True
                weakenings[tA] = tB
                outA[iA] = Missing
                outB[iB] = Missing
                outAB[oAB] = tA
                oAB += 1
            if oAB == nAB: break
    if anyFound:
        # compact (i.e. remove any Missing elements)
        outA = tuple([A for A in outA[0:oA] if A])
        outAB = tuple(outAB[0:oAB])
        outB = tuple([B for B in outB[0:oB] if B])
    else:
        outA = tuple(outA[0:oA])
        outAB = tuple(outAB[0:oAB])
        outB = tuple(outB[0:oB])

    # answer  AB', AB, A'B
    return outA, outAB, outB, weakenings


def hasT(t):
    if isinstance(t, BType):
        return t.hasT
    elif isinstance(t, type):
        return False
    else:
        raise ProgrammerError()


T = BTSchemaVariable.define("T")
T.hasT = True

_schemaVariablesByOrd = [Missing]
def schemaVariableForOrd(ord):
    global _schemaVariablesByOrd
    if ord > (i1 := len(_schemaVariablesByOrd)) - 1:
        i2 = i1 + 20 - 1
        _schemaVariablesByOrd += [Missing] * 20   # allocate 20 extra each time
        for i in range(i1, i2 + 1):
            _schemaVariablesByOrd[i] = T.ensure(BTAtom.ensure(f'{i}'))
    return _schemaVariablesByOrd[ord]


def isT(x):
    return isinstance(x, BTSchemaVariable) and x.hasT  # mildly faster than x.base is T


for i in range(1, 21):
    Ti = schemaVariableForOrd(i)
    locals()[Ti.name] = Ti

for o in range(26):
    To = T.ensure(BTAtom.ensure(chr(ord('a')+o)))
    locals()[To.name] = To


N = BTSchemaVariable.define('N')
_ordinalTypes = [N]

for i in range(1, 11):
    Ni = N.ensure(BTAtom.ensure(f'{i}'))
    _ordinalTypes.append(Ni)
    locals()[Ni.name] = Ni

for o in range(26):
    No = N.ensure(BTAtom.ensure(chr(ord('a')+o)))
    _ordinalTypes.append(No)
    locals()[No.name] = No

BType._arrayOrdinalTypes = tuple(_ordinalTypes)   # COULDDO use parent relationship to detect ordinals


_implicitTypes = ()

def _find(needle, haystack):
    try:
        return haystack.index(needle)
    except:
        return -1

def determineRetType(md, tByT, sigCaller):
    raise NotYetImplemented()

