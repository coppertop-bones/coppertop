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

# BY DESIGN
# 1) we allow aType['name'] as shorthand for aType[BTAtom('_name')].nameAs('name')  - albeit at the slightly increased
#    chance of misspelling errors
#
# SPEED OPTIONS - SoA style on the list of types, etc - this may also make translation to C easier
# classes with __slots__ seem to be the fastest
# if accessing globals becomes an issue could make the whole module a class


import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)


__all__ = ['BType', 'S']

import itertools, builtins

from bones.lang._type_lang.jones_type_manager import JonesTypeManager, BType, BTAtom, BTIntersection, BTUnion, \
    BTTuple, BTStruct, BTSeq, BTMap, BTFn, BTSchemaVariable, BTOverload, BTypeError, ppT
from bones.lang._type_lang.jones_type_manager import _btypeByClass, _BTypeById     # used by coppertop.pipe - do not remove
from bones.lang.type_lang import TypeLangInterpreter

from bones.lang.core import bmtnul, bmtatm, bmtint, bmtuni, bmttup, bmtstr, bmtrec, bmtseq, bmtmap, bmtfnc, bmtsvr, bmtnameById

from bones.core.errors import ProgrammerError, NotYetImplemented, PathNotTested
from bones.core.sentinels import Missing, Void, generator


_verboseNames = False

_idSeed = itertools.count(start=1)   # reserve id 0 as a terminator of a type set

REPL_OVERRIDE_MODE = False

_BTypeByName = {}





def raiseCantNameBTypeError(this, name, other):
    raise BTypeError(
        f"Can't name new type ({type(this)}) as '{name}' as another BType({type(other)}) already has that name"
    )


class BTReserved(BType):
    def __new__(cls, name=Missing, explicit=Missing, space=Missing, implicitly=Missing):
        kwargs = {}
        if name: kwargs['name'] = name
        if explicit: kwargs['explicit'] = explicit
        if space: kwargs['space'] = space
        if implicitly: kwargs['implicitly'] = implicitly
        bt = sys._gtm.reserve(**kwargs)
        return cls._new(bt)



class _Flags:
    __slots__ = ['hasActualT', 'hasT', 'explicit', 'orthogonal']
    def __init__(self):
        self.hasActualT = False
        self.hasT = False
        self.explicit = False
        self.orthogonal = False

def _sortedIntersectionTypes(types, singleSV):
    flags = _Flags()
    if len(types) < 2: raise ProgrammerError("Needs 2 or more types")
    collated = []
    for t in types:
        if isinstance(t, BTIntersection):            # BTIntersection is a subclass of BType so this must come first
            collated.extend(t.types)
            [_updateFlagsForIntersection(e, flags, singleSV) for e in t.types]
        elif isinstance(t, type):
            t = getBTypeForClass(t)
            collated.append(t)
            _updateFlagsForIntersection(t, flags, singleSV)
        elif isinstance(t, BType):
            collated.append(t)
            _updateFlagsForIntersection(t, flags, singleSV)
        else:
            1/0 # when is this case used?
            for e in t:
                if isinstance(e, BTIntersection):    # BTIntersection is a subclass of BType so this must come first
                    collated.extend(e.types)
                    [_updateFlagsForIntersection(e, flags, singleSV) for r in t.types]
                elif isinstance(e, type):
                    e = getBTypeForClass(e)
                    collated.append(e)
                    _updateFlagsForIntersection(t, flags, singleSV)
                elif isinstance(e, BType):
                    collated.append(e)
                    _updateFlagsForIntersection(t, flags, singleSV)
                else:
                    raise BTypeError("OPEN: Needs description")
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
                raise BTypeError('Can only have one actual T in an intersection')
            flags.hasActualT = True
            flags.hasT = True
        elif t.hasT:
            flags.hasT = True
        if t.orthogonal:
            if (flags.orthogonal and flags.orthogonal is not t) and singleSV:
                raise BTypeError('Can only have one orthogonal type in an intersection')
            flags.orthogonal = t
    else:
        # all python types are orthogonal
        if (flags.orthogonal and flags.orthogonal is not t) and singleSV:
            raise BTypeError('Can only have one orthogonal in an intersection')
        flags.orthogonal = t


class _AddStuff:
    def __init__(self, t):
        self.t = t
    def __ror__(self, instance):    # instance | type
        return instance | BTIntersection(instance._t if hasattr(instance, '_t') else builtins.type(instance), self.t)

class _SubtractStuff:
    def __init__(self, t):
        self.t = t
    def __ror__(self, instance):  # instance | type
        if not isinstance(t := instance._t if hasattr(instance, '_t') else builtins.type(instance), BTIntersection):
            raise BTypeError(f'Can only subtract a type from an intersection but LHS type is {t}')
        a_, ab, b_, weakenings = _partitionIntersectionTLs(
            t.types,
            self.t.types if isinstance(self.t, BTIntersection) else (self.t, )
        )
        if b_:
            raise BTypeError(f"RHS is trying to subtract {b_} which isn't in the LHS")
        if not ab:
            raise ProgrammerError(f"Can't end up subtracting nothing")
        if not a_:
            raise BTypeError("Left with null set")
        return instance | (a_[0] if len(a_) == 1 else BTIntersection(*a_))



S = BTStruct




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


def ensurePyBType(xOrBt):
    if type(xOrBt).__name__ == 'BType':
        bmtid = sys._gtm.bmtid(xOrBt)
        if bmtid == bmtmap: return sys._gtm.replaceWith(xOrBt, BTMap._new(xOrBt))
        else: raise NotYetImplemented(f'bmtid={bmtnameById[bmtid]}')
    else:
        return xOrBt



def fitsWithin(a, b, TRACE=False, fittingSigs=False):
    # answers a tuple {cacheID, doesFit, tByT, distance}
    a = ensurePyBType(a)
    b = ensurePyBType(b)
    # a must be a concrete type
    # if hasattr(a, 'hasT') and a.hasT:
    if a.hasT:
        if isinstance(a, BTFn) and isinstance(b, BTFn):
            fittingSigs = True
        if not fittingSigs:
            raise BTypeError(f'LHS type ({a}) is polymorphic and thus cannot match RHS type {b}')

    distance = 0

    if isinstance(b, type):
        if a.__class__ == BTIntersection:
            # (txt & ISIN) fitsWithin (txt) etc
            cacheId = (a.id, b)
        else:
            # buildins.str fitsWithin buildins.str
            return (Missing, a == b, Missing, distance)
    else:
        if isinstance(a, BType):
            if a.id == b.id:
                # num fitsWithin num
                return (Missing, True, Missing, distance)
            cacheId = (a.id, b.id)
        else:
            if not isinstance(a, type):
                raise BTypeError(f"a is type {a.__class__} b is {repr(b)}")
            cacheId = (a, b.id)


    # check the cache - get prior tByT as well as the result
    cached = _fitsCache.get(cacheId, Missing)
    if cached is not Missing:
        doesFit, tByT, distance = cached
        return (Missing, doesFit, tByT, distance)

    tByT = {}

    if isinstance(b, BTSchemaVariable):
        # anything (except explicits) fitsWithin a wildcard
        if (hasattr(a, 'explicit') and a.explicit) or (a.__class__ == BTIntersection and _anyExplicit(a.types)):
            return (cacheId, False, Missing, Missing)
        else:
            return (cacheId, True, {b:a}, distance + SCHEMA_PENALTY)  # exact match must beat wildcard
        # if b.base is T:
        #     # anything (except explicits) fitsWithin a wildcard
        #     if (hasattr(a, 'explicit') and a.explicit) or (a.__class__ == BTIntersection and _anyExplicit(a.types)):
        #         return (cacheId, False, Missing, Missing)
        #     else:
        #         return (cacheId, True, {b:a}, distance + SCHEMA_PENALTY)  # exact match must beat wildcard
        # elif isinstance(a, BTSchemaVariable):
        #     if a.base.id == b.base.id:
        #         # N1 fitsWithin Na
        #         return (cacheId, True, tByT, distance)
        #     else:
        #         return (cacheId, False, Missing, Missing)
        # else:
        #     return (cacheId, False, Missing, Missing)


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
            return (cacheId, False, Missing, Missing)
        elif a.__class__ == BTIntersection: # I I
            # (matrix & square & dtup) fitsWithin (matrix & dtup & aliased)
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
                if not doesFit: return (cacheId, False, Missing, Missing)
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
            if not doesFit: return (cacheId, False, Missing, Missing)
        return (cacheId, True, tByT, distance)

    elif case == O_U:
        # a just needs to fit any in b
        for t in b.types:
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(a, t, TRACE, fittingSigs), tByT, distance)
            if doesFit: return (cacheId, True, tByT, distance)
        return (cacheId, False, Missing, distance)

    elif case == I_U:
        # two cases
        # 1 - intersection is a union member - (num&fred)  fitsWithin  (num&fred) + (str&joe)
        for t in b.types:
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(a, t, TRACE, fittingSigs), tByT, distance)
            if doesFit: return (cacheId, True, tByT, distance)
        # 2 - intersecting the union with another type - (num+str) & fred  fitsWithin  (num+str)
        a_, ab, b_, weakenings = _partitionIntersectionTLs(a.types, (b,))
        if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
            return (cacheId, False, Missing, Missing)  # i.e. there is something missing in a that is required by b
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

                a_, ab, b_ = _partitionIntersectionTLsWithTInRhs(a.types, bTypes, TRACE, fittingSigs)
                if b_:
                    if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
                        return (cacheId, False, Missing, Missing)  # i.e. there is something missing in a that is required by b
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
                                    return (cacheId, False, Missing, Missing)   # conflict found
                        else:
                            tByT[TNew] = tNew
                if len(a_) == 0:  # exact match is always fine
                    if len(Ts) ==1:
                        return (cacheId, False, Missing, Missing)
                    return (cacheId, True, tByT, distance)
                else:
                    if len(Ts) == 0:
                        # a match but a simple type from the intersection is dropped and we'd prefer that it was caught
                        distance += 1
                    else: # len(Ts) == 1:
                        # add the match to tByT - distance is the usual SCHEMA_PENALTY for a T match
                        matchedT = a_[0] if len(a_) == 1 else BTIntersection.noSpaceCheck(a_)
                        tByT[Ts[0]] = matchedT
                        distance += SCHEMA_PENALTY
                    return _processA_(a_, cacheId, tByT, distance + len(a_))

            else: # len(Ts) == 1:
                # (str & ISIN) >> check >> fitsWithin >> (str & T1)
                a_, ab, b_, weakenings = _partitionIntersectionTLs(a.types, bTypes)
                if b_:
                    if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
                        return (cacheId, False, Missing, Missing)  # i.e. there is something missing in a that is required by b
                if len(a_) == 0:
                    # (str & ISIN) >> check >> fitsWithin >> (str & ISIN & T) - T is nullset - not fine
                    return (cacheId, False, Missing, Missing)  # i.e. there is something missing in a that is required by b
                else:
                    # wildcard match is fine, metric is SCHEMA_PENALTY to loose against exact match
                    matchedT = a_[0] if len(a_) == 1 else BTIntersection.noSpaceCheck(a_)
                    return (cacheId, True, {Ts[0]: matchedT}, SCHEMA_PENALTY + len(weakenings) + len(a_))
        else:
            a_, ab, b_, weakenings = _partitionIntersectionTLs(a.types, b.types)
            if _anyNotImplicit(b_):         # check for (matrix) fitsWithin (matrix & aliased) etc
                return (cacheId, False, Missing, Missing)   # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return (cacheId, True, tByT, 0 + len(weakenings))
            else:
                return _processA_(a_, cacheId, tByT, len(weakenings) + len(a_))

    elif case == I_O:
        # isT(b) has already been handled above in the BTSchemaVariable check
        # (num & col) fitsWithin (num)
        a_, ab, b_, weakenings = _partitionIntersectionTLs(a.types, (b,))
        if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
            return (cacheId, False, Missing, Missing)  # i.e. there is something missing in a that is required by b
        if len(a_) == 0:                          # exact match is always fine
            return (cacheId, True, tByT, 0 + len(weakenings))
        else:
            return _processA_(a_, cacheId, tByT, len(weakenings) + len(a_))

    elif case == O_I:
        # str fitsWithin (str&aliased)    (remember aliased is implicit)
        if b.hasT:
            # MUSTDO handle wildcards properly
            a_, ab, b_, weakenings = _partitionIntersectionTLs((a,), b.types)
            if b_:
                if len(b_) == 1 and isT(b_[0]) and len(a_) > 0:
                    # wildcard match is always fine, metric is SCHEMA_PENALTY to loose against exact match
                    matchedT = a_[0] if len(a_) == 1 else BTIntersection.noSpaceCheck(a_)
                    return (cacheId, True, {b_[0]: matchedT}, SCHEMA_PENALTY + len(weakenings) + len(a_))
                if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
                    return (cacheId, False, Missing, Missing)  # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return (cacheId, True, tByT, 0 + len(weakenings))
            else:
                return _processA_(a_, cacheId, tByT, len(weakenings) + len(a_))
        else:
            a_, ab, b_, weakenings = _partitionIntersectionTLs((a,), b.types)
            if _anyNotImplicit(b_):  # check for (matrix) fitsWithin (matrix & aliased) etc
                return (cacheId, False, Missing, Missing)  # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return (cacheId, True, tByT, 0 + len(weakenings))
            else:
                return _processA_(a_, cacheId, tByT, len(weakenings) + len(a_))

    else:
        raise ProgrammerError()


    if isinstance(a, BTFn):
        if isinstance(b, BTFn):
            if a.numargs != b.numargs:
                return (cacheId, False, Missing, Missing)

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
                return (cacheId, False, Missing, Missing)

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
                    return (cacheId, False, Missing, Missing)

            # there may be additional checks here
            # print(f'{a} <: {b} is true')
            return (cacheId, True, tByT, distance)

        elif isinstance(a, BTOverload):
            # we don't do soft typing in coppertop
            return (cacheId, False, Missing, Missing)

        else:
            return (cacheId, False, Missing, Missing)

    elif isinstance(a, BTOverload):
        if isinstance(b, BTFn):
            # must be a fit for one of a with b
            for aT in a.types:
                doesFit, local_tByT, distance = cacheAndUpdate(fitsWithin(aT, b, TRACE, fittingSigs), dict(tByT), distance)
                if doesFit: break
            if doesFit:
                return (cacheId, True, tByT, distance)
            else:
                return (cacheId, False, Missing, Missing)

        elif isinstance(b, BTOverload):
            # a must fit with every one of b
            for bT in b.types:
                doesFit, local_tByT, distance = cacheAndUpdate(fitsWithin(a, bT, TRACE, fittingSigs), dict(tByT), distance)
                if not doesFit: return (cacheId, False, Missing, Missing)
            return (cacheId, True, tByT, distance)

        else:
            return (cacheId, False, Missing, Missing)

    elif type(a) is not type(b):
        # the two types are not the same so they cannot fit (we don't allow inheritance - except in case of Ordinals)
        if a in BType._arrayOrdinalTypes and b in BType._arrayOrdinalTypes:
            return (cacheId, True, tByT, distance)
        else:
            return (cacheId, False, Missing, Missing)

    elif isinstance(b, BTAtom):
        # already a.id != b.id so must be False
        return (cacheId, False, Missing, Missing)

    elif isinstance(b, BTTuple):
        aTs, bTs = a.types, b.types
        if len(aTs) != len(bTs): return (cacheId, False, Missing, Missing)
        for i, aT in enumerate(aTs):
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(aT, bTs[i], TRACE, fittingSigs), tByT, distance)
            if not doesFit: return (cacheId, False, Missing, Missing)
        return (cacheId, True, tByT, distance)

    elif isinstance(b, BTStruct):
        # b defines what is required, a defines what is available
        aTypes, bTypes = a.types, b.types
        if len(aTypes) < len(bTypes): return (cacheId, False, Missing, Missing)
        for nA, tA, nB, tB in zip(a.names, aTypes, b.names, bTypes):
            if nA != nB: return (cacheId, False, Missing, Missing)
            doesFit, tByT, distance = cacheAndUpdate(fitsWithin(tA, tB, TRACE, fittingSigs), tByT, distance)
            if not doesFit: return (cacheId, False, Missing, Missing)
        return (cacheId, True, tByT, distance)

    # elif isinstance(b, BTRec):
    #     # b defines what is required, a defines what is available
    #     # iterate through b's names and check if they are available in a
    #     aF2T, bF2T = a.typeByName, b.typeByName
    #     if len(aF2T) < len(bF2T): return (cacheId, False, Missing, Missing)
    #     for bf, bT in bF2T.items():
    #         aT = aF2T.get(bf, Missing)
    #         if aT is Missing: return (cacheId, False, Missing, Missing)
    #         doesFit, tByT, distance = cacheAndUpdate(fitsWithin(aT, bT, TRACE, fittingSigs), tByT, distance)
    #         if not doesFit: return (cacheId, False, Missing, Missing)
    #     return (cacheId, True, tByT, distance)

    elif isinstance(b, BTSeq):
        doesFit2, tByT, distance = cacheAndUpdate(fitsWithin(a.mappedType, b.mappedType, TRACE, fittingSigs), tByT, distance)
        if not doesFit2: return (cacheId, False, Missing, Missing)
        return (cacheId, True, tByT, distance)

    elif isinstance(b, BTMap):
        doesFit1, tByT, distance = cacheAndUpdate(fitsWithin(a.indexType, b.indexType, TRACE, fittingSigs), tByT, distance)
        if not doesFit1: return (cacheId, False, Missing, Missing)
        doesFit2, tByT, distance = cacheAndUpdate(fitsWithin(a.mappedType, b.mappedType, TRACE, fittingSigs), tByT, distance)
        if not doesFit2: return (cacheId, False, Missing, Missing)
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
    spaceCount = 0
    for ta in a_:
        if isinstance(ta, BType):
            if ta.explicit:
                return (cacheId, False, Missing, Missing)
            elif (root := ta.rootSpace):
                # OPEN: needs doing properly
                spaceCount += 1
        else:
            spaceCount += 1
    if spaceCount > 1:
        try:
            tlid = sys._gtm.intersectionTlidFor(a_)
        except:
            print("ponder some more")
            # raise BTypeError("OPEN: Needs description")
    return (cacheId, True, tByT, len(a_) + lenWeakenings)

# def _processA_(a_, cacheId, tByT, lenWeakenings):
#     exclusiveCount = 0
#     for ta in a_:
#         if isinstance(ta, BType):
#             if ta.familial:
#                 implicitWeakenings = [tw for tw in _weakenings.get(ta, ()) if tw in _implicitTypes]
#                 if not implicitWeakenings:
#                     return (cacheId, False, Missing, Missing)
#             elif ta.explicit:
#                 return (cacheId, False, Missing, Missing)
#             elif ta.space:
#                 # OPEN: needs doing properly
#                 exclusiveCount += 1
#         else:
#             exclusiveCount += 1
#     if exclusiveCount > 1:
#         raise BTypeError("OPEN: Needs description")
#     return (cacheId, True, tByT, len(a_) + lenWeakenings)

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


def _partitionIntersectionTLs(A:tuple, B:tuple):
    # A and B are the types of two intersections, answer the types in A but not B, in both and in B but not A
    # handles weakenings
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


def _partitionIntersectionTLsWithTInRhs(a:tuple, b:tuple, TRACE=False, fittingSigs=False):
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


def hasT(t):
    if isinstance(t, BType):
        return t.hasT
    elif isinstance(t, type):
        return False
    else:
        raise ProgrammerError()


T = BTSchemaVariable("T")

_schemaVariablesByOrd = [Missing]
def schemaVariableForOrd(ord):
    global _schemaVariablesByOrd
    if ord > (i1 := len(_schemaVariablesByOrd)) - 1:
        i2 = i1 + 20 - 1
        _schemaVariablesByOrd += [Missing] * 20   # allocate 20 extra each time
        for i in range(i1, i2 + 1):
            _schemaVariablesByOrd[i] = BTSchemaVariable(f'T{i}')
    return _schemaVariablesByOrd[ord]


def isT(x):
    return isinstance(x, BTSchemaVariable) and x.hasT  # mildly faster than x.base is T


for i in range(1, 10):
    Ti = schemaVariableForOrd(i)
    locals()[Ti.name] = Ti


N = BTAtom('N')
_ordinalTypes = [N]

for i in range(1, 10):
    Ni = BTAtom(f'N{i}')
    _ordinalTypes.append(Ni)
    locals()[Ni.name] = Ni


BType._arrayOrdinalTypes = tuple(_ordinalTypes)


_implicitTypes = ()

def _find(needle, haystack):
    try:
        return haystack.index(needle)
    except:
        return -1

def determineRetType(md, tByT, sigCaller):
    raise NotYetImplemented()

