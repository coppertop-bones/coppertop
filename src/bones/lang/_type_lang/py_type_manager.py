# **********************************************************************************************************************
# Copyright (c) 2025 David Briant. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
# **********************************************************************************************************************

import collections, itertools

from bones.lang.core import bmtnul, bmtatm, bmtint, bmtuni, bmttup, bmtstr, bmtrec, bmtseq, bmtmap, bmtfnc, bmtsvr

from bones.jones import BTypeError
from bones.core.sentinels import Missing
from bones.core.errors import ProgrammerError, NotYetImplemented
from bones.lang._type_lang.utils import OnErrorRollback
from bones.lang._type_lang.fits import fitsWithin

# OPEN: monkey patch the contexts corresponding to ruleNames, i.e. TypeLangParser.Tl_bodyContext, etc with a label
# property that returns the label of the rule or subrule, e.g. 'tl_body', 'ignore1', etc


_gVarnameById = Missing


# types

# OPEN: add hasT


# it might be nice to be able to do `if a is list:` ?
# this is nice because a type is globally unique and its python identity could correspond to its c identity, i.e. the
# field. However this means that we have just the one class PyBType to cover all btypes. Or we could get clever and
# monkey-patch the class to separate out Union behaviour from Struct behaviour.

# more easily is to override the == operator. Also can override the <= operator for the case where we just need the
# boolean result and not the distance or tByT or we allow return a True box and False box from <=



Fit = collections.namedtuple('Fit', ['distance', 'tByT'])
Fit.__bool__ = lambda self: True

NoFit = collections.namedtuple('NoFit', ['distance', 'tByT'])
NoFit.__bool__ = lambda self: False


class PyBType:
    __slots__ = ('bmtid', '_id')
    def __init__(self, bmtid, id):
        self.bmtid = bmtid
        self._id = id
    def __repr__(self):
        return f'{type(self).__name__}{self.id}'
    def __bool__(self):
        return self._id > 0
    def __eq__(self, other):
        return isinstance(other, PyBType) and self._id == other._id
    def __le__(self, other):
        raise NotYetImplemented('needs a global singleton or a back pointer to the type manager I belong to or an global identity set backpointing to the TypeManager')
    def __hash__(self):
        return self._id
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, value):
        raise AttributeError()


class TBC(PyBType):
    __slots__ = ('btype', 'space')
    def __init__(self, id, space):
        super().__init__(bmtnul, id)
        self.btype = Missing
        self.space = space
    def __repr__(self):
        spaceRepr = (f'TBC{self._id}' if isinstance(self.space, TBC) else repr(self.space)) if self.space is not Missing else ''
        return (f'TBC{self._id}({self.btype})' if self.btype else f'TBC{self._id}') + (f' in {spaceRepr}' if self.space else '')
    def mergeWith(self, btype, space):
        self.btype = btype
        btype._id = self._id
        self.space = space
        self.bmtid = btype.bmtid


def _reprTypes(types):
    return [((f'TBC{t.id}' if t.btype else f'TBC{t.id}') if isinstance(t, TBC) else repr(t)) for t in types]


class Atom(PyBType):
    __slots__ = ('explicit', 'space', 'implicitly')
    def __init__(self, bmtid, id, explicit, space, implicitly):
        super().__init__(bmtid, id)
        self.explicit = explicit
        self.space = space
        self.implicitly = implicitly
    def __repr__(self):
        return f'Atom{self.id}("{_gVarnameById.get(self.id, "unnamed")}")'


class Inter(PyBType):
    __slots__ = ('types', 'space')
    def __init__(self, bmtid, id, types, space):
        super().__init__(bmtid, id)
        assert isinstance(types, tuple)
        self.types = types
        self.space = space
    def __repr__(self):
        return f'Inter{self.id}({" & ".join(_reprTypes(self.types))})' + (f' in {self.space}' if self.space else '')


class Union(PyBType):
    __slots__ = ('types',)
    def __init__(self, bmtid, id, types):
        super().__init__(bmtid, id)
        assert isinstance(types, tuple)
        self.types = types
    def __repr__(self):
        return f'Union{self.id}({" + ".join(_reprTypes(self.types))})'


class Tuple(PyBType):
    __slots__ = ('types',)
    def __init__(self, bmtid, id, types):
        super().__init__(bmtid, id)
        assert isinstance(types, tuple)
        self.types = types
    def __repr__(self):
        return f'Tuple{self.id}({" * ".join(_reprTypes(self.types))})'


class Struct(PyBType):
    __slots__ = ('names', 'btypes')
    def __init__(self, bmtid, id, names, btypes):
        super().__init__(bmtid, id)
        self.names = names
        self.btypes = btypes
    def __repr__(self):
        return f'Struct{self.id}({self.names!r},{self.btypes!r})'


class Rec(PyBType):
    __slots__ = ('names', 'btypes')
    def __init__(self, bmtid, id, names, btypes):
        super().__init__(bmtid, id)
        self.names = names
        self.btypes = btypes
    def __repr__(self):
        return f'Struct{self.id}({self.names!r},{self.btypes!r})'


class Seq(PyBType):
    __slots__ = ('contained',)
    def __init__(self, bmtid, id, contained):
        super().__init__(bmtid, id)
        assert isinstance(contained, PyBType)
        self.contained = contained
    def __repr__(self):
        return f'Seq{self.id}({self.contained!r})'


class Map(PyBType):
    __slots__ = ('tK', 'tV')
    def __init__(self, bmtid, id, tK, tV):
        super().__init__(bmtid, id)
        self.tK = tK
        self.tV = tV
    def __repr__(self):
        return f'Map{self.id}({self.tK!r}, {self.tV!r})'


class Fn(PyBType):
    __slots__ = ('tArgs', 'tRet')
    def __init__(self, bmtid, id, tArgs, tRet):
        super().__init__(bmtid, id)
        self.tArgs = tArgs
        self.tRet = tRet
    def __repr__(self):
        return f'Fn{self.id}({self.tArgs!r}, {self.tRet!r})'


class Mutable(PyBType):
    __slots__ = ('contained',)
    def __init__(self, bmtid, id, contained):
        super().__init__(bmtid, id)
        self.contained = contained
    def __repr__(self):
        return f'Mutable{self.id}({self.contained!r})'


class SchemaVar(PyBType):
    __slots__ = ()
    def __init__(self, bmtid, id):
        super().__init__(bmtid, id)
    def __repr__(self):
        return f'SchemaVar{self.id}("{_gVarnameById.get(self.id, "unnamed")}")'



class PyTypeManager:
    __slots__ = [
        '_seed', '_btypeById', '_idByVarname', '_varnameById', '_checkpointIds', '_implicitRecursiveId', '_tbcIdByVarname',
        '_unwinds',
        '_interByTypes', '_unionByTypes', '_tupleByTypes', '_structByFields', '_recByFields', '_seqByContained',
        '_mapByLhsRhs', '_fnByLhsRhs', '_mutableByContained',
        '_fitsCache',
    ]

    def __init__(self):
        global _gVarnameById
        self._seed = itertools.count(start=1)
        self._btypeById = {}
        self._idByVarname = {}
        self._varnameById = _gVarnameById = {}
        self._checkpointIds = []
        self._implicitRecursiveId = Missing
        self._tbcIdByVarname = {}

        self._unwinds = Missing
        
        self._interByTypes = {}
        self._unionByTypes = {}
        self._tupleByTypes = {}
        self._structByFields = {}
        self._recByFields = {}
        self._seqByContained = {}
        self._mapByLhsRhs = {}
        self._fnByLhsRhs = {}
        self._mutableByContained = {}

        self._fitsCache = {}            # a tuple {doesFit, tByT, distance} by {a.id, b.id}

        t = Atom(bmtnul, 0, False, Missing, Missing)
        self._btypeById[t.id] = t

        for i in range(1, 20):
            t = SchemaVar(bmtsvr, next(self._seed))
            self._btypeById[t.id] = t
            self._idByVarname[f'T{t.id}'] = t.id
            self._varnameById[t.id] = f'T{t.id}'


    # parsing process

    def checkImplicitRecursiveAssigned(self):
        if (btypeid := self._implicitRecursiveId) is not Missing:
            raise BTypeError(f'Implicit recursive type "{self._varnameById[btypeid]}" has not been confirmed')
        return Missing

    def checkpoint(self):
        pass

    def commit(self):
        pass

    def done(self):
        if self._implicitRecursiveId: raise ValueError(f'Implicit recursive variables not assigned: {self._implicitRecursiveId}')
        if self._tbcIdByVarname: raise ValueError(f'Declared recursive variables not assigned: {", ".join(self._tbcIdByVarname)}')
        return None

    def onErrRollback(self):
        return OnErrorRollback(self)

    def rollback(self):
        pass



    # BType creation and accessing

    def __getitem__(self, name):
        if isinstance(name, str):
            if (id := self._idByVarname.get(name, Missing)) is not Missing:
                return self._btypeById[id]
            else:
                return self._btypeById[0]  # Not A Type
        else:
            answer = []
            for n in name:
                if (id := self._idByVarname.get(n, Missing)) is not Missing:
                    answer.append(self._btypeById[id])
                else:
                    answer.append(self._btypeById[0])  # Not A Type
            return answer

    def bind(self, name, btype):
        # checks the type if it already exists (so can do identical redefines) and sets the type for the name
        # clearing any recursive types (including the single implicit one) that are waiting

        if (currentid := self._idByVarname.get(name, Missing)) is not Missing:
            if isinstance(currentType := self._btypeById[currentid], TBC):
                if currentType.btype is Missing:
                    # redefine recursive type to match the contained type
                    if (rec := self._tbcIdByVarname.pop(name, Missing)) is Missing:
                        raise ProgrammerError(f'Expected to find recursive type "{name}" in _tbcIdByVarname')
                    if self._implicitRecursiveId == currentid:
                        # we are now defining the sole implicit recursive type
                        self._implicitRecursiveId = Missing
                    # change the btypes identity! OPEN: is there any way to not waste an id?
                    currentType.mergeWith(btype, btype.space if hasattr(btype, 'space') else Missing)
                    print(f'{name}: {self.pp(currentType)}')
                    return btype
                else:
                    # check recursive type
                    if currentType.btype.id == btype.id:
                        # same
                        return btype
                    else:
                        raise BTypeError(f'Variable "{name}" already defined as recursive type with "{currentType.btype}"')
            else:
                if currentid == btype.id:
                    # same
                    return btype
                else:
                    # different
                    raise BTypeError(f'Variable "{name}" already defined as type "{currentType}')
        else:
            # define
            self._idByVarname[name] = btype.id
            self._varnameById[btype.id] = name
            if isinstance(btype, TBC) and btype.bmtid == bmtnul:
                self._tbcIdByVarname[name] = btype.id
            print(f'{name}: {self.pp(btype)}')
            return btype

    def bmtid(self, t):
        """Answer the bmtid for the given type t."""
        return t.bmtid

    def check(self, A, B):
        if A.id == B.id: return True
        raise NotYetImplemented()

    def exists(self, name):
        return name in self._idByVarname

    def fn(self, tArgs, tRet, *, btype=Missing):
        types = (tArgs, tRet)
        if (fn := self._fnByLhsRhs.get(types, Missing)) is Missing:
            fn = Fn(bmtfnc, next(self._seed), tArgs, tRet)
            self._btypeById[fn.id] = fn
            self._fnByLhsRhs[types] = fn
        return fn

    def fnTArgs(self, btype):
        return btype.tArgs

    def fnTRet(self, btype):
        return btype.tRet

    def initAtom(self, *, explicit=Missing, space=Missing, implicitly=Missing, name=Missing, btype=Missing):
        if btype:
            assert isinstance(btype, TBC)
            name = self._varnameById.get(btype.id, Missing)
            if self._implicitRecursiveId == btype.id: self._implicitRecursiveId = Missing
            if name and name in self._tbcIdByVarname:
                del self._tbcIdByVarname[name]
            atom = Atom(bmtatm, btype.id, explicit, btype.space or space, implicitly)
            btype.btype = atom
            btype.bmtid = bmtatm
            answer = btype
        elif (currentId := self._idByVarname.get(name, Missing)) is Missing:
            answer = Atom(bmtatm, next(self._seed), explicit or False, space, implicitly)
            self._btypeById[answer.id] = answer
        else:
            current = self._btypeById[currentId]
            if isinstance(current, TBC):
                # this is only possible with fred: atom [explicit] in fred
                # 2 cases
                if name in self._tbcIdByVarname:
                    # we are defining the atom for the first time
                    assert space.id == currentId
                    atom = Atom(bmtatm, currentId, explicit, space, implicitly)
                    current.btype = atom
                    current.space = space
                    current.bmtid = bmtatm
                    if self._implicitRecursiveId == currentId: self._implicitRecursiveId = Missing
                    del self._tbcIdByVarname[name]
                    answer = current
                else:
                    # we are redefining the atome - so check the definition
                    raise NotYetImplemented()
            else:
                # we are redefining the atom so check the definition
                if not (current := self._btypeById[currentId]).explicit and explicit: raise BTypeError(f'"{name}" is already defined but without explicit matching')
                if current.space is Missing:
                    if space is not Missing:
                        raise BTypeError(f'"{name}" is already defined in space "{self.pp(current.space)}"')
                else:
                    if space is not Missing:
                        if space.id != current.space.id:
                            raise BTypeError(f'"{name}" is already defined in space "{self.pp(current.space)}"')
                if current.implicitly != implicitly: raise BTypeError(f'"{name}" is already defined as implicitly "{self.pp(current.implicitly)}"')
                answer = current
        return answer

    def intersection(self, types, *, space=Missing, btype=Missing):
        typelist = self._intersectionTypeList(types)
        if (inter := self._interByTypes.get(typelist, Missing)) is Missing:
            if btype is Missing:
                inter = Inter(bmtint, next(self._seed), typelist, space)
                self._btypeById[inter.id] = inter
            else:
                # recursive intersection
                inter = Inter(bmtint, btype.id, typelist, space)
            self._interByTypes[typelist] = inter
        return inter

    def intersectionTl(self, t):
        return t.types

    def _intersectionTypeList(self, types):
        # Example
        # (GBP: GBP & ccy in ccy) & (EUR: EUR & ccy in ccy) >> expandTypes and remove duplicates => GBP & ccy & EUR
        # GBP & ccy & EUR >> getSpaces => [ccy] + [] + [ccy] => 2 parents
        # [ccy, ccy] >> unique => [ccy] => 1 independent space
        # 1 independent space from the 2 spaces so has common roots therefore illegal

        # fully expand any intersections in types, removing duplicates (via sort and compact)
        typelist = []
        for t in types:
            if isinstance(t, TBC) and t.btype and t.btype.bmtid == bmtint:
                for t2 in t.btype.types:
                    if t2 not in typelist:
                        typelist.append(t2)
            elif t.bmtid == bmtint:
                for t2 in t.types:
                    if t2 not in typelist:
                        typelist.append(t2)
            else:
                if t not in typelist:
                    typelist.append(t)
        typelist = tuple(sorted(typelist, key=lambda t: t.id))

        # check all spaces and spaces of spaces, etc, return NAT if any duplicates
        totalCount, independentIds = 0, set()
        for t in typelist:
            parents = _parentIds(t, self)
            totalCount += len(parents)
            independentIds = independentIds.union(parents)
            if len(independentIds) < totalCount:
                raise BTypeError('The types share common orthogonal spaces')

        return typelist

    def isRecursive(self, t):
        raise NotYetImplemented()

    def lookup(self, name):
        answer = self._idByVarname.get(name, Missing)
        if answer: answer = self._btypeById[answer]
        return answer

    def lookupOrImplicitTbc(self, name):
        # gets the type for the name creating up to one implicit recursive type if it doesn't exist
        if (btypeid := self._idByVarname.get(name, Missing)) is Missing:
            # create the contemporaneously sole implicit recursive type
            if (btypeid := self._tbcIdByVarname.get(name, Missing)) is not Missing: raise ProgrammerError()
            if (btypeid := self._implicitRecursiveId) is not Missing and self._varnameById[btypeid] != name:
                raise BTypeError(f'Only one implicit recursive type can be defined simutaneously. "{name}" encountered but "{self._varnameById[btypeid]}" is already the currently defined implicit recursive type.')
            btypeid = self.reserve().id
            self._implicitRecursiveId = self._tbcIdByVarname[name] = btypeid
            self._idByVarname[name] = btypeid
            self._varnameById[btypeid] = name
        return self._btypeById[btypeid]

    def map(self, tK, tV, *, btype=Missing):
        if (map := self._mapByLhsRhs.get((tK, tV), Missing)) is Missing:
            map = Map(bmtmap, next(self._seed), tK, tV)
            self._btypeById[map.id] = map
            self._mapByLhsRhs[(tK, tV)] = map
        return map

    def mapTK(self, btype):
        return btype.tK

    def mapTV(self, btype):
        return btype.tV

    def mutable(self, contained, *, btype=Missing):
        contained = contained[0]
        if (mutable := self._mutableByContained.get(contained, Missing)) is Missing:
            mutable = Mutable(next(self._seed), contained)
            self._btypeById[mutable.id] = mutable
            self._mutableByContained[contained] = mutable
        return mutable

    def name(self, t):
        return self._varnameById.get(t.id, None)

    def pp(self, t):
        # if isinstance(t, TBC):
        #     repr(t)
        #     name = self._varnameById[t.id]
        #     return f'TBC({name}, in={self.pp(t.space)})' if t.space else f'TBC({name})'
        # elif t.bmtid == bmtatm:
        #     name = self._varnameById[t.id]
        #     return f'Atom("{name}", explicit=True)' if t.explicit else f'Atom("{name}")'
        #     # f'"{self.name!s}"' if self.explicit else f'{self.name!s}'
        # else:
        return repr(t)

    def rec(self, fields, *, btype=Missing):
        if (rec := self._recByFields.get(fields, Missing)) is Missing:
            rec = Rec(bmtrec, next(self._seed), fields)
            self._btypeById[rec.id] = rec
            self._recByFields[fields] = rec
        return rec

    def reserve(self, *, space=Missing, btype=Missing):
        t = TBC(next(self._seed), space)
        self._btypeById[t.id] = t
        return t

    def rootSpace(self, t):
        root = Missing
        while t.bmtid in (bmtatm, bmtint):
            if t.space is Missing:
                break
            else:
                root = t.space
                t = t.space
        return root

    def schemavar(self, *, btype=Missing):
        t = SchemaVar(bmtsvr, next(self._seed))
        self._btypeById[t.id] = t
        return t

    def seq(self, contained, *, btype=Missing):
        if (seq := self._seqByContained.get(contained, Missing)) is Missing:
            seq = Seq(bmtseq, next(self._seed), contained)
            self._btypeById[seq.id] = seq
            self._seqByContained[contained] = seq
        return seq

    def seqT(self, btype):
        return btype.contained

    def space(self, t):
        return t.space

    def struct(self, names, btypes, *, btype=Missing):
        if (struct := self._structByFields.get((names, btypes), Missing)) is Missing:
            struct = Struct(bmtstr, next(self._seed), names, btypes)
            self._btypeById[struct.id] = struct
            self._structByFields[(names, btypes)] = struct
        return struct

    def tuple(_self, types, *, btype=Missing):
        types = types if isinstance(types, tuple) else tuple(types)
        if (tup := _self._tupleByTypes.get(types, Missing)) is Missing:
            tup = Tuple(bmttup, next(_self._seed), types)
            _self._btypeById[tup.id] = tup
            _self._tupleByTypes[types] = tup
        return tup

    def tupleTl(self, btype):
        return btype.types

    def union(self, types, *, btype=Missing):
        typelist = self.union_tlid_for(types)
        if (union := self._unionByTypes.get(typelist, Missing)) is Missing:
            union = Union(bmtuni, next(self._seed), types)
            self._btypeById[union.id] = union
            self._unionByTypes[typelist] = union
        return union

    def union_tlid_for(self, btypes):
        # a bit lazy answer a tuple of btypes rather than an integer
        # fully expand any unions in types, removing duplicates (via bubble)
        typelist = []
        for t in btypes:
            if t.bmtid == bmtuni:
                for t2 in self.unionTl(t):
                    if t2 not in typelist:
                        typelist.append(t2)
            else:
                if t not in typelist:
                    typelist.append(t)
        return tuple(sorted(typelist, key=lambda t: t.id))

    def unionTl(self, btype):
        return btype.types


PyTypeManager.fitsWithin = fitsWithin


def _parentIds(t, tm):
    visited = set()
    return _parentIds2(t, tm, visited)

def _parentIds2(t, tm, visited):
    if t.id in visited:
        return visited
    else:
        visited.add(t.id)
        if t.bmtid in (bmtatm, bmtint) and t.space is not Missing:
            return _parentIds2(t.space, tm, visited)
        else:
            return visited
