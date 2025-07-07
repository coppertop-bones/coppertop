# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

# BY DESIGN
# 1) we allow aType['name'] as shorthand for aType[BTAtom('_name')].nameAs('name')  - albeit at the slightly increased
#    chance of misspelling errors
#
# SPEED OPTIONS - SoA style on the list of types, etc - this may also make translation to C easier
# classes with __slots__ seem to be the fastest
# if accessing globals becomes an issue could make the whole moedule a class


import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)


__all__ = ['BType', 'BTypeError', 'SchemaError', 'extractConstructors']

import itertools, builtins, collections, statistics

from bones.jones import Fits, SchemaError
import bones.ts._type_lang.jones_type_manager
from bones.ts._type_lang.jones_type_manager import JonesTypeManager, BType, BTAtom, BTIntersection, BTUnion, \
    BTTuple, BTStruct, BTSeq, BTMap, BTFn, BTSchemaVariable, BTFamily, BTypeError, ppT, _btcls_by_bmtid, \
    extractConstructors
from bones.ts.core import bmtnul, bmtatm, bmtint, bmtuni, bmttup, bmtstr, bmtrec, bmtseq, bmtmap, bmtfnc, \
    bmtsvr, bmtnameById
from bones.ts._type_lang.jones_type_manager import _btypeByClass, _BTypeById     # used by coppertop.pipe - do not remove
from bones.ts.type_lang import TypeLangInterpreter

from bones.core.errors import ProgrammerError, NotYetImplemented, PathNotTested
from bones.core.sentinels import Missing


_verboseNames = False

_idSeed = itertools.count(start=1)              # reserve id 0 as a terminator of a type set

_BTypeByName = {}


class Constructors(list): pass


def raiseCantNameBTypeError(this, name, other):
    raise BTypeError(
        f'Can\'t name new type ({type(this)}) as "{name}" as another BType({type(other)}) already has that name'
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
    if len(types) < 2: raise ProgrammerError('Needs 2 or more types')
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
                    raise BTypeError('OPEN: Needs description')
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


# dm should be independent of coppertop so any types needed in coppertop or bone should be created there
# dm depends on coppertop which intern depends on bones which depends on jones
# where do we define py?
# bones has the function selection which uses py


IDENTICAL = Fits(True, {}, 0)
DOES_NOT_FIT = Fits(False, Missing, Missing)    # or Fits(False, {}, 100000)?


def _BTypeToPyBType(bt):
    bmtid = sys._gtm.bmtid(bt)
    cls = _btcls_by_bmtid[bmtid]
    return sys._gtm.replaceWith(bt, cls._new(bt))


def fitsWithin(a, b, *, fittingSigs=False):
    # type clean up
    if not isinstance(a, BType) and not isinstance(a, type): a = _BTypeToPyBType(a)
    if not isinstance(b, BType) and not isinstance(b, type): b = _BTypeToPyBType(b)

    #  rather than create a bones type for every python class let's just make the fitsWithin handle them as an atom,
    #  i.e. opaque

    if isinstance(a, type):
        if isinstance(b, BType):
            # most fitsWithin calls in coppertop will be Python type <: BType so this is the first case
            if b == pytype:
                # any Python type <: pytype
                return (Fits(True, {}, 0))
            else:
                cacheId = (a, b.id)
        elif isinstance(b, type):
            return IDENTICAL if a == b else DOES_NOT_FIT     # can Python's typing stuff be used here?
        else:
            raise TypeError(f'a is Python {a.__class__}, b is {repr(b)}')
    elif isinstance(a, BType):
        if isinstance(b, type):
            if isinstance(a, (BTAtom, BTIntersection)):
                # (txt & ISIN) <: buildins.str, txt <: buildins.str
                cacheId = (a.id, b)
            else:
                # generally `BType <: Python type` cannot be true, however, what about pydict <: dict, a A * B <: tuple
                return DOES_NOT_FIT
        elif isinstance(b, BType):
            if b == btype:
                # any BType <: btype but pydict <: pydict is exact
                return Fits(True, {}, 0.25)
            elif a.id == b.id:
                return IDENTICAL
            else:
                cacheId = (a.id, b.id)
        else:
            raise TypeError('fitsWithin only supports Python types and BTypes')
        if a.hasT:
            if isinstance(a, BTFn) and isinstance(b, BTFn):
                fittingSigs = True
            if not fittingSigs:
                raise BTypeError(f'LHS type ({a}) is polymorphic and thus cannot match RHS type {b}')
    else:
        raise TypeError('fitsWithin only supports Python types and BTypes')

    fits = _fitsCache.get(cacheId, Missing)
    if fits is not Missing: return fits

    try:
        _fitsCache[cacheId] = answer = _fitsWithin(a, b, fittingSigs=fittingSigs)
        return answer
    except SchemaError as ex:
        return DOES_NOT_FIT

sys._fitsWithin = fitsWithin        # for coercion - do not remove

def _fitsWithin(a, b, fittingSigs=False):
    # answers a Fits named tuple

    if isinstance(b, BTSchemaVariable):
        # anything (except explicits) <: a wildcard
        if (hasattr(a, 'explicit') and a.explicit) or (a.__class__ == BTIntersection and _anyExplicit(a.types)):
            return DOES_NOT_FIT
        else:
            return Fits(True, {b:a}, SCHEMA_PENALTY)  # exact match must beat wildcard
        # if b.base is T:
        #     # anything (except explicits) <: a wildcard
        #     if (hasattr(a, 'explicit') and a.explicit) or (a.__class__ == BTIntersection and _anyExplicit(a.types)):
        #         return DOES_NOT_FIT
        #     else:
        #         return Fits(True, {b:a}, distance + SCHEMA_PENALTY)  # exact match must beat wildcard
        # elif isinstance(a, BTSchemaVariable):
        #     if a.base.id == b.base.id:
        #         # N1 <: Na
        #         return Fits(True, schemaVars, distance)
        #     else:
        #         return DOES_NOT_FIT
        # else:
        #     return DOES_NOT_FIT


    # check the coercions
    if (o := _find(b, _weakenings.get(a, ()))) >= 0:
        return Fits(True, {}, o + 1)


    if isinstance(b, BTUnion):
        if isinstance(a, BTUnion):          # U U
            # (str+num) <: (str+num+int)
            case = U_U      # every a must fit in b
        elif a.__class__ == BTIntersection: # I U
            # (num+str) & fred  <:  (num+str)
            # (num&fred) <: (num&fred) + (str&joe)
            case = I_U
        else:                               # O U
            case = O_U      # a just needs to fit any in b

    elif b.__class__ == BTIntersection:
        if isinstance(a, BTUnion):          # U I
            # if an element in a is b we have a partial fit
            # (num&fred) + (str&joe)  <:  (num&fred)
            return DOES_NOT_FIT
        elif a.__class__ == BTIntersection: # I I
            # (matrix & square & dtup) <: (matrix & dtup & aliased)
            case = I_I
        else:                               # O I
            # str <: (str&aliased)    (remember aliased is implicit)
            case = O_I

    else:
        if isinstance(a, BTUnion):          # U O
            # consider the following cases:
            # 1. if (any element in a) <: b we have a partial fit, e.g. (num + err) <: (num)
            # 2. (index ^ index) + (txt ^ txt)  <:  (T1 ^ T2)      => T1: index + txt, T2: index + txt
            # 3. (index ^ index) + (txt ^ txt)  <:  (T1 ^ T1)      => T1: index + txt
            # 4. (index & square) + (index & circle)  <:  (index)
            schemaVars, results = {}, []
            for t in a.types:
                if not (fits := fitsWithin(t, b, fittingSigs=fittingSigs)):
                    # 1 is currently not supported
                    return DOES_NOT_FIT
                # next line will through an error for cases 2 & 3
                schemaVars, _ = updateSchemaVarsWith(schemaVars, 0, fits)
                results.append(fits)
            return Fits(True, schemaVars, statistics.mean([r.distance for r in results]))
        elif a.__class__ == BTIntersection: # I O
            case = I_O
        else:                               # O O
            case = O_O


    if case == O_O:
        pass

    elif case == U_U:
        # every a must fit in b
        schemaVars, results = {}, []
        for t in a.types:
            if not (fits := fitsWithin(t, b, fittingSigs=fittingSigs)):
                return DOES_NOT_FIT
            schemaVars, _ = updateSchemaVarsWith(schemaVars, 0, fits)
            results.append(fits)
        # OPEN: U_U_Metric
        return Fits(True, schemaVars, statistics.mean([r.distance for r in results]))
        # return Fits(True, schemaVars, statistics.min([r.distance for r in results]))

    elif case == O_U:
        # a just needs to fit any element in b - select the closest match (for distance we could return mean but
        # schemaVars would be a problem)
        schemVars, results = {}, []
        for t in b.types:
            if (fits := fitsWithin(a, t, fittingSigs=fittingSigs)):
                schemVars, _ = updateSchemaVarsWith(schemVars, 0, fits)  # to the update to wheedle out conflicts
                results.append(fits)
        if results:
            indexOfClosest = 0
            for i in range(1, len(results)):
                if results[i].distance < results[indexOfClosest].distance:
                    indexOfClosest = i
            return results[indexOfClosest]
        else:
            return DOES_NOT_FIT

    elif case == I_U:
        schemaVars, distance = {}, 0
        # two cases
        # 1 - intersection is a union member - (num&fred)  <:  (num&fred) + (str&joe)
        for t in b.types:
            doesFit, schemaVars, distance = fred(fitsWithin(a, t, fittingSigs=fittingSigs), schemaVars, distance)
            if doesFit: return Fits(True, schemaVars, distance)
        # 2 - intersecting the union with another type - (num+str) & fred  <:  (num+str)
        a_, ab, b_, weakenings = _partitionIntersectionTLs(a.types, (b,))
        if _anyNotImplicit(b_):  # check for (matrix) <: (matrix & aliased) etc
            return DOES_NOT_FIT  # i.e. there is something missing in a that is required by b
        if len(a_) == 0:                          # exact match is always fine
            raise PathNotTested()
            return Fits(True, schemaVars, 0 + len(weakenings))
        else:
            raise PathNotTested()
            return _processA_(a_, schemaVars, len(weakenings))

    elif case == I_I:
        if b.hasT:
            Ts, bTypes, bTypesHasT = _inject(b.types, {'Ts':[], 'other':[], 'otherHasT': False}, _THasTOther)
            if len(Ts) > 1:
                raise ProgrammerError('Intersection has more than one T - should not even be possible to construct that')
            if len(Ts) == 0 or bTypesHasT:
                # potentially out of order - e.g. ((N ** ccy) & list) fitsWithIn (T2 & (N ** T1))
                # N log N process? as cross matching is required and need to choose shortest distance for T1, T2 etc

                a_, ab, b_ = _partitionIntersectionTLsWithTInRhs(a.types, bTypes, fittingSigs=fittingSigs)
                if b_:
                    if _anyNotImplicit(b_):  # check for (matrix) <: (matrix & aliased) etc
                        return DOES_NOT_FIT  # i.e. there is something missing in a that is required by b
                    raise PathNotTested()
                # check no conflicts for any T
                schemaVars, distance = {}, 0
                for ta, tb, schemaVars_, distance_ in ab:
                    distance += distance_
                    for TNew, tNew in schemaVars_.items():
                        t = schemaVars.get(TNew, Missing)
                        if t is not Missing:
                            if tNew is not t and t not in _weakenings.get(tNew, ()):
                                if tNew in _weakenings.get(t, ()):
                                    raise PathNotTested()
                                    schemaVars[TNew] = tNew
                                else:
                                    raise PathNotTested()
                                    return DOES_NOT_FIT   # conflict found
                        else:
                            schemaVars[TNew] = tNew
                if len(a_) == 0:  # exact match is always fine
                    if len(Ts) ==1:
                        return DOES_NOT_FIT
                    return Fits(True, schemaVars, distance)
                else:
                    if len(Ts) == 0:
                        # a match but a simple type from the intersection is dropped and we'd prefer that it was caught
                        distance += 1
                    else: # len(Ts) == 1:
                        # add the match to schemaVars - distance is the usual SCHEMA_PENALTY for a T match
                        matchedT = a_[0] if len(a_) == 1 else BTIntersection.noSpaceCheck(a_)
                        schemaVars[Ts[0]] = matchedT
                        distance += SCHEMA_PENALTY
                    return _processA_(a_, schemaVars, distance + len(a_))

            else: # len(Ts) == 1:
                # (str & ISIN) <: (str & T1)
                a_, ab, b_, weakenings = _partitionIntersectionTLs(a.types, bTypes)
                if b_:
                    if _anyNotImplicit(b_):  # check for (matrix) <: (matrix & aliased) etc
                        return DOES_NOT_FIT  # i.e. there is something missing in a that is required by b
                if len(a_) == 0:
                    # (str & ISIN) <: (str & ISIN & T) - T is nullset - not fine
                    return DOES_NOT_FIT  # i.e. there is something missing in a that is required by b
                else:
                    # wildcard match is fine, metric is SCHEMA_PENALTY to loose against exact match
                    matchedT = a_[0] if len(a_) == 1 else BTIntersection.noSpaceCheck(a_)
                    return Fits(True, {Ts[0]: matchedT}, SCHEMA_PENALTY + len(weakenings) + len(a_))
        else:
            a_, ab, b_, weakenings = _partitionIntersectionTLs(a.types, b.types)
            if _anyNotImplicit(b_):         # check for (matrix) <: (matrix & aliased) etc
                return DOES_NOT_FIT   # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return Fits(True, {}, len(weakenings))
            else:
                return _processA_(a_, {}, len(weakenings) + len(a_))

    elif case == I_O:
        # isT(b) has already been handled above in the BTSchemaVariable check
        # (num & col) <: (num)
        a_, ab, b_, weakenings = _partitionIntersectionTLs(a.types, (b,))
        if _anyNotImplicit(b_):  # check for (matrix) <: (matrix & aliased) etc
            return DOES_NOT_FIT  # i.e. there is something missing in a that is required by b
        if len(a_) == 0:                          # exact match is always fine
            return Fits(True, {}, len(weakenings))
        else:
            return _processA_(a_, {}, len(weakenings) + len(a_))

    elif case == O_I:
        # str <: (str&aliased)    (remember aliased is implicit)
        if b.hasT:
            # MUSTDO handle wildcards properly
            a_, ab, b_, weakenings = _partitionIntersectionTLs((a,), b.types)
            if b_:
                if len(b_) == 1 and isT(b_[0]):
                    if len(a_) > 0:
                        # wildcard match is always fine, metric is SCHEMA_PENALTY to loose against exact match
                        matchedT = a_[0] if len(a_) == 1 else BTIntersection.noSpaceCheck(a_)
                        return Fits(True, {b_[0]: matchedT}, SCHEMA_PENALTY + len(weakenings) + len(a_))
                    else:
                        return Fits(True, {b_[0]: sys._gtm.fromId(0)}, SCHEMA_PENALTY + len(weakenings) + len(a_))
                if _anyNotImplicit(b_):  # check for (matrix) <: (matrix & aliased) etc
                    return DOES_NOT_FIT  # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return Fits(True, {}, 0 + len(weakenings))
            else:
                return _processA_(a_, {}, len(weakenings) + len(a_))
        else:
            a_, ab, b_, weakenings = _partitionIntersectionTLs((a,), b.types)
            if _anyNotImplicit(b_):  # check for (matrix) <: (matrix & aliased) etc
                return DOES_NOT_FIT  # i.e. there is something missing in a that is required by b
            if len(a_) == 0:                          # exact match is always fine
                return Fits(True, {}, 0 + len(weakenings))
            else:
                return _processA_(a_, {}, len(weakenings) + len(a_))

    else:
        raise ProgrammerError()


    if isinstance(a, BTFn):
        if isinstance(b, BTFn):
            schemaVars, distance = {}, 0
            if a.numargs != b.numargs:
                return DOES_NOT_FIT

            # we have agreed to handle b and we are checking if a is up to the task of being substitutable with b
            # i.e. is a <: b
            # consider  b : (i+t,    t)   -> b+n         b can take i+t in arg1 and t in arg2 and won't output more than b+n
            #                 /\     /\       \/
            #           a : (i+t+s,  t+s) ->  n          a can take in more in arg1, and arg2 and will output less - therefore it fits

            if isinstance(b.tRet, BTSchemaVariable):
                doesFit, schemaVars, distance = fred(Fits(True, {b.tRet:a.tRet}, SCHEMA_PENALTY), schemaVars, distance)
            elif isinstance(a.tRet, BTSchemaVariable):
                # e.g. T1 < txt or T1 < T1 - discard the info as it really needs some deeper analysis
                doesFit, schemaVars, distance = fred(Fits(True, {}, 0), schemaVars, distance)
            else:
                doesFit, schemaVars, distance = fred(fitsWithin(a.tRet, b.tRet, fittingSigs=fittingSigs), schemaVars, distance)
            if not doesFit:
                # print(f'{a} <: {b} is false')
                return DOES_NOT_FIT

            for aT, bT in zip(a.tArgs, b.tArgs):
                if isinstance(bT, BTSchemaVariable):
                    doesFit, schemaVars, distance = fred(Fits(True, {bT: aT}, SCHEMA_PENALTY), schemaVars, distance)
                elif isinstance(aT, BTSchemaVariable):
                    # e.g. T1 < txt or T1 < T1 - discard the info as it really needs some deeper analysis
                    doesFit, schemaVars, distance = fred(Fits(True, {}, 0), schemaVars, distance)
                else:
                    doesFit, schemaVars, distance = fred(fitsWithin(bT, aT, fittingSigs=fittingSigs), schemaVars, distance)
                if not doesFit:
                    # print(f'{a} <: {b} is false')
                    return DOES_NOT_FIT

            # there may be additional checks here
            # print(f'{a} <: {b} is true')
            return Fits(True, schemaVars, distance)

        elif isinstance(a, BTFamily):
            # we don't do soft typing in coppertop
            return DOES_NOT_FIT

        else:
            return DOES_NOT_FIT

    elif isinstance(a, BTFamily):
        if isinstance(b, BTFn):
            # must be a fit for one of a with b
            schemaVars, distance = {}, 0
            for aT in a.types:
                doesFit, local_schemaVars, distance = fred(fitsWithin(aT, b, fittingSigs=fittingSigs), dict(schemaVars), distance)
                if doesFit: break
            if doesFit:
                return Fits(True, schemaVars, distance)
            else:
                return DOES_NOT_FIT

        elif isinstance(b, BTFamily):
            # a must fit with every one of b
            schemaVars, distance = {}, 0
            for bT in b.types:
                doesFit, local_schemaVars, distance = fred(fitsWithin(a, bT, fittingSigs=fittingSigs), dict(schemaVars), distance)
                if not doesFit: return DOES_NOT_FIT
            return Fits(True, schemaVars, distance)

        else:
            return DOES_NOT_FIT

    elif type(a) is not type(b):
        # the two types are not the same so they cannot fit (we don't allow inheritance - except in case of Ordinals)
        if a in BType._arrayOrdinalTypes and b in BType._arrayOrdinalTypes:
            return Fits(True, {}, 0)
        else:
            return DOES_NOT_FIT

    elif isinstance(b, BTAtom):
        # already a.id != b.id so must be False
        return DOES_NOT_FIT

    elif isinstance(b, BTTuple):
        schemaVars, distance = {}, 0
        aTs, bTs = a.types, b.types
        if len(aTs) != len(bTs): return DOES_NOT_FIT
        for i, aT in enumerate(aTs):
            doesFit, schemaVars, distance = fred(fitsWithin(aT, bTs[i], fittingSigs=fittingSigs), schemaVars, distance)
            if not doesFit: return DOES_NOT_FIT
        return Fits(True, schemaVars, distance)

    elif isinstance(b, BTStruct):
        # b defines what is required, a defines what is available
        schemaVars, distance = {}, 0
        aTypes, bTypes = a.types, b.types
        if len(aTypes) < len(bTypes): return DOES_NOT_FIT
        for nA, tA, nB, tB in zip(a.names, aTypes, b.names, bTypes):
            if nA != nB: return DOES_NOT_FIT
            doesFit, schemaVars, distance = fred(fitsWithin(tA, tB, fittingSigs=fittingSigs), schemaVars, distance)
            if not doesFit: return DOES_NOT_FIT
        return Fits(True, schemaVars, distance)

    # elif isinstance(b, BTRec):
    #     # b defines what is required, a defines what is available
    #     # iterate through b's names and check if they are available in a
    #     aF2T, bF2T = a.typeByName, b.typeByName
    #     if len(aF2T) < len(bF2T): return DOES_NOT_FIT
    #     for bf, bT in bF2T.items():
    #         aT = aF2T.get(bf, Missing)
    #         if aT is Missing: return DOES_NOT_FIT
    #         doesFit, schemaVars, distance = fred(fitsWithin(aT, bT, fittingSigs=fittingSigs), schemaVars, distance)
    #         if not doesFit: return DOES_NOT_FIT
    #     return Fits(True, schemaVars, distance)

    elif isinstance(b, BTSeq):
        schemaVars, distance = {}, 0
        doesFit2, schemaVars, distance = fred(fitsWithin(a.mappedType, b.mappedType, fittingSigs=fittingSigs), schemaVars, distance)
        if not doesFit2: return DOES_NOT_FIT
        return Fits(True, schemaVars, distance)

    elif isinstance(b, BTMap):
        schemaVars, distance = {}, 0
        doesFit1, schemaVars, distance = fred(fitsWithin(a.indexType, b.indexType, fittingSigs=fittingSigs), schemaVars, distance)
        if not doesFit1: return DOES_NOT_FIT
        doesFit2, schemaVars, distance = fred(fitsWithin(a.mappedType, b.mappedType, fittingSigs=fittingSigs), schemaVars, distance)
        if not doesFit2: return DOES_NOT_FIT
        return Fits(True, schemaVars, distance)

    else:
        raise ProgrammerError(f'Unhandled case {a} <: {b}')


def fred(fits, schemaVars, distance):
    if not fits.fits:
        return False, schemaVars, distance
    s, d = updateSchemaVarsWith(schemaVars, distance, fits)
    return fits.fits, s, d


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


_implicitTypes = ()
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

def _processA_(a_, schemaVars, lenWeakenings):
    spaceCount = 0
    for ta in a_:
        if isinstance(ta, BType):
            if ta.explicit:
                return DOES_NOT_FIT
            elif (root := ta.rootSpace):
                # OPEN: needs doing properly
                spaceCount += 1
        else:
            spaceCount += 1
    if spaceCount > 1:
        try:
            tlid = sys._gtm.intersectionTlidFor(a_)
        except:
            print('ponder some more', file=sys.stderr)
            # raise BTypeError("OPEN: Needs description")
    return Fits(True, schemaVars, len(a_) + lenWeakenings)


# prior to 2025.05.25
# def _processA_(a_, schemaVars, lenWeakenings):
#     exclusiveCount = 0
#     for ta in a_:
#         if isinstance(ta, BType):
#             if ta.familial:
#                 implicitWeakenings = [tw for tw in _weakenings.get(ta, ()) if tw in _implicitTypes]
#                 if not implicitWeakenings:
#                     return DOES_NOT_FIT
#             elif ta.explicit:
#                 return DOES_NOT_FIT
#             elif ta.space:
#                 # OPEN: needs doing properly
#                 exclusiveCount += 1
#         else:
#             exclusiveCount += 1
#     if exclusiveCount > 1:
#         raise BTypeError("OPEN: Needs description")
#     return Fits(True, schemaVars, len(a_) + lenWeakenings)


def updateSchemaVarsWith(runningSchemaVars, runningDistance, result):
    resultFits, resultSVRs, resultDistance = result
    if not resultFits: raise ValueError(f'Can only update schemaVars when a <: b which is not the case here')
    runningSchemaVars = dict(runningSchemaVars)
    for TNew, tNew in resultSVRs.items():
        if TNew is T:
            continue   # OPEN: implies that T cannot be part of a schema only a general placeholder. ponder this some more
        if (tRunning := runningSchemaVars.get(TNew, Missing)) is Missing:
            runningSchemaVars[TNew] = tNew
        elif tNew != tRunning:
            weakened = False
            if tRunning not in _weakenings.get(tNew, ()):
                if tNew in _weakenings.get(tRunning, ()):
                    runningSchemaVars[TNew] = tNew
                    weakened = True
            if not weakened:
                raise SchemaError(f'{TNew} could be {tRunning} or {tNew} but currently we don\'t support analysing conflicting schema vars - can be probably be done with unions')
        else:
            # no change
            pass
    return runningSchemaVars, runningDistance + resultDistance


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
            if oAB == nAB or iA == nA or iB == nB:
                break
        elif idA < idB:
            outA[oA] = tA
            oA += 1
            iA += 1
            if oA == nA or iA == nA:
                break
        else:
            outB[oB] = tB
            oB += 1
            iB += 1
            if oB == nB or iB == nB:
                break
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

# every now and then we hack as a temporary measure - OPEN: needs doing properly
bones.ts._type_lang.jones_type_manager._partitionIntersectionTLs = _partitionIntersectionTLs
bones.ts._type_lang.jones_type_manager._BTypeToPyBType = _BTypeToPyBType

def _partitionIntersectionTLsWithTInRhs(a:tuple, b:tuple, *, fittingSigs):
    ab = []
    potentialsByA, potentialsByB = {}, {}
    remainingATypes = list(a)
    remainingBTypes = list(b)
    for ai, ta in enumerate(remainingATypes):
        for bi, tb in enumerate(remainingBTypes):
            fits = fitsWithin(ta, tb, fittingSigs=fittingSigs)
            if fits:
                schemaVars, distance = updateSchemaVarsWith({}, 0, fits)  # handles weakenings
                if distance == 0:
                    ab.append((ta, tb, schemaVars, 0))
                    remainingATypes[ai] = Missing
                    del remainingBTypes[bi]
                    break
                else:
                    potentialsByA.setdefault(ta, []).append((tb, schemaVars, distance))
                    potentialsByB.setdefault(tb, []).append((ta, schemaVars, distance))
    # if any bt fits more than one a we might have a problem
    # but for the moment just check that each potential A and B has length 1
    a_ = {at:at for at in remainingATypes if at is not Missing}
    b_ = {bt:bt for bt in remainingBTypes}
    for ta, potentials in potentialsByA.items():
        if len(potentials) > 1:
            raise NotYetImplemented()
        else:
            tb, schemaVars, distance = potentials[0]
            ab.append((ta, tb, schemaVars, distance))
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


def isT(x):
    return isinstance(x, BTSchemaVariable) and x.hasT  # mildly faster than x.base is T


def determineRetType(md, schemaVars, sigCaller):
    raise NotYetImplemented()


def _find(needle, haystack):
    try:
        return haystack.index(needle)
    except:
        return -1


# **********************************************************************************************************************
# essential btypes used throughout coppertop-bones
# **********************************************************************************************************************

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

btype = BType('btype: atom in mem')     # a BType - OPEN: define in jones?
pytype = BType('pytype: atom in mem')   # a Python type
TBI = BType('TBI: atom in mem')         # To Be Inferred - OPEN: define in jones

_btypeByClass[builtins.type] = pytype   # needed to build @coppertop functions in coppertop.pipe which imports this module
