# **********************************************************************************************************************
# Copyright (c) 2025 David Briant. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
# **********************************************************************************************************************

import itertools, traceback
from collections import namedtuple

from bones.lang.core import TLError, bmterr, bmtatm, bmtint, bmtuni, bmttup, bmtstr, bmtrec, bmtseq, bmtmap, bmtfnc, bmtsvr

from bones.core.sentinels import Missing
from bones.core.errors import ProgrammerError, NotYetImplemented

# OPEN: monkey patch the contexts corresponding to ruleNames, i.e. TypeLangParser.Tl_bodyContext, etc with a label
# property that returns the label of the rule or subrule, e.g. 'tl_body', 'ignore1', etc


_gVarnameById = Missing

def atom__repr__(self):
    return f'{_gVarnameById[self.id]}'

def inter__repr__(self):
    return f'Inter{self.id}({" & ".join([repr(t) for t in self.types])})'

def union__repr__(self):
    return f'Union{self.id}({" + ".join([repr(t) for t in self.types])})'

def tuple__repr__(self):
    return f'Tup{self.id}({" * ".join([repr(t) for t in self.types])})'




# types

# OPEN: add hasT

Atom = namedtuple('Atom', ['bmtid', 'id', 'explicit', 'space', 'implicitly'])
Atom.__repr__ = atom__repr__

Inter = namedtuple('Inter', ['bmtid', 'id', 'types', 'space'])
Inter.__repr__ = inter__repr__

Union = namedtuple('Union', ['bmtid', 'id', 'types'])
Union.__repr__ = union__repr__

Tuple = namedtuple('Tuple', ['bmtid', 'id', 'types'])
Tuple.__repr__ = tuple__repr__

Struct = namedtuple('Struct', ['bmtid', 'id', 'fields'])
Struct.__repr__ = lambda self: f'Struct({self.fields!r})'

Rec = namedtuple('Rec', ['bmtid', 'id', 'fields'])
Rec.__repr__ = lambda self: f'Rec({self.fields!r})'

Seq = namedtuple('Seq', ['bmtid', 'id', 'contained'])
Seq.__repr__ = lambda self: f'Seq({self.contained!r})'

Map = namedtuple('Map', ['bmtid', 'id', 'tLhs', 'tRhs'])
Map.__repr__ = lambda self: f'Map({self.tLhs!r}, {self.tRhs!r})'

Fn = namedtuple('Fn', ['bmtid', 'id', 'tArgs', 'tRet'])
Fn.__repr__ = lambda self: f'Fn({self.tArgs!r}, {self.tRet!r})'

Mutable = namedtuple('Mutable', ['bmtid', 'id', 'contained'])
Mutable.__repr__ = lambda self: f'Mutable({self.contained!r})'

SchemaVar = namedtuple('SchemaVar', ['bmtid', 'id'])
SchemaVar.__repr__ = lambda self: f'SchemaVar({self.id!r})'

class Recursive:
    __slots__ = ('bmtid', 'id', 'main', 'space')
    def __init__(self, id, space):
        self.bmtid = bmterr
        self.id = id
        self.main = Missing
        self.space = space
    def __repr__(self):
        # OPEN: handle recursion - could add varname for PP
        if self.main:
            return f'Recursive({type(self.main).__name__})' + (f' in {type(self.main).__name__}' if self.space else '')
        else:
            return f'TBC({self.id})' + (f' in {self.space}' if self.space else '')


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

        t = Atom(bmterr, 0, False, Missing, Missing)
        self._btypeById[t.id] = t

        for i in range(1, 20):
            t = SchemaVar(bmtsvr, next(self._seed))
            self._btypeById[t.id] = t
            self._idByVarname[f'T{t.id}'] = t.id
            self._varnameById[t.id] = f'T{t.id}'

    def onErrRollback(self):
        return OnErrorRollback(self)

    def checkpoint(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def __getitem__(self, varname):
        if (id := self._idByVarname.get(varname, Missing)) is not Missing:
            return self._btypeById[id]
        else:
            return self._btypeById[0]  # Not A Type

    def bmtid(self, t):
        """Answer the bmtid for the given type t."""
        return t.bmtid

    def name(self, t):
        return self._varnameById[t.id]

    def exists(self, varname):
        return varname in self._idByVarname

    def get(self, varname):
        # gets the type for the name creating up to one implicit recursive type if it doesn't exist
        if (btypeid := self._idByVarname.get(varname, Missing)) is Missing:
            # create the contemporaneously sole implicit recursive type
            if (btypeid := self._tbcIdByVarname.get(varname, Missing)) is not Missing: raise ProgrammerError()
            if (btypeid := self._implicitRecursiveId) is not Missing and self._varnameById[btypeid] != varname:
                raise TLError(f'Only one implicit recursive type can be defined simutaneously. "{varname}" encountered but "{self._varnameById[btypeid]}" is already the currently defined implicit recursive type.')
            btypeid = self.recursive(Missing).id
            self._implicitRecursiveId = self._tbcIdByVarname[varname] = btypeid
            self._idByVarname[varname] = btypeid
            self._varnameById[btypeid] = varname
        return self._btypeById[btypeid]

    def set(self, varname, btype):
        # checks the type if it already exists (so can do identical redefines) and sets the type for the name
        # clearing any recursive types (including the single implicit one) that are waiting

        if (currentid := self._idByVarname.get(varname, Missing)) is not Missing:
            if isinstance(currentType := self._btypeById[currentid], Recursive):
                if currentType.main is Missing:
                    # redefine recursive type to match the contained type
                    if (rec := self._tbcIdByVarname.pop(varname, Missing)) is Missing:
                        raise ProgrammerError(f'Expected to find recursive type "{varname}" in _tbcIdByVarname')
                    if self._implicitRecursiveId == currentid:
                        # we are now defining the sole implicit recursive type
                        self._implicitRecursiveId = Missing
                    currentType.bmtid = btype.bmtid
                    currentType.main = btype
                    if hasattr(btype, 'space'):
                        currentType.space = btype.space
                    print(f'{varname}: {self.pp(btype)}')
                    return
                else:
                    # check recursive type
                    if currentType.main.id == btype.id:
                        # same
                        return
                    else:
                        raise TLError(f'Variable "{varname}" already defined as recursive type with "{currentType.main}"')
            else:
                if currentid == btype.id:
                    # same
                    return
                else:
                    # different
                    raise TLError(f'Variable "{varname}" already defined as type "{currentType}')
        else:
            # define
            self._idByVarname[varname] = btype.id
            self._varnameById[btype.id] = varname
            if isinstance(btype, Recursive):
                self._tbcIdByVarname[varname] = btype.id
            print(f'{varname}: {self.pp(btype)}')
            return

    def pp(self, t):
        if t.bmtid == bmtatm:
            name = self._varnameById[t.id]
            return f'Atom({name}, explicit=True)' if t.explicit else f'Atom({name})'
            # f'"{self.name!s}"' if self.explicit else f'{self.name!s}'
        elif isinstance(t, Recursive):
            name = self._varnameById[t.id]
            return f'Recursive({name}, in={self.pp(t.space)})' if t.space else f'Recursive({name})'
        else:
            return repr(t)

    def checkImplicitRecursiveAssigned(self):
        if (btypeid := self._implicitRecursiveId) is not Missing:
            raise TLError(f'Implicit recursive type "{self._varnameById[btypeid]}" has not been assigned')
        return Missing

    def done(self):
        if self._implicitRecursiveId: raise ValueError(f'Implicit recursive variables not assigned: {self._implicitRecursiveId}')
        if self._tbcIdByVarname: raise ValueError(f'Declared recursive variables not assigned: {", ".join(self._tbcIdByVarname)}')
        return None

    def atom(self, explicit, spacenode, implicitly, varname):
        if (currentId := self._idByVarname.get(varname, Missing)) is Missing:
            space = self.get(spacenode.varname) if spacenode is not Missing else Missing
            answer = Atom(bmtatm, next(self._seed), explicit, space, implicitly)
            self._btypeById[answer.id] = answer
        else:
            current = self._btypeById[currentId]
            if isinstance(current, Recursive):
                # this is only possible with fred: atom [explicit] in fred
                # 2 cases
                if varname in self._tbcIdByVarname:
                    # we are defining the atom for the first time
                    assert spacenode
                    space = spacenode.eval(self, Missing)
                    assert space.id == currentId
                    atom = Atom(bmtatm, currentId, explicit, space, implicitly)
                    current.main = atom
                    current.space = space
                    current.bmtid = bmtatm
                    if self._implicitRecursiveId == currentId: self._implicitRecursiveId = Missing
                    del self._tbcIdByVarname[varname]
                    answer = current
                else:
                    # we are redefining the atome - so check the definition
                    raise NotYetImplemented()
            else:
                # we are redefining the atom so check the definition
                if not (current := self._btypeById[currentId]).explicit and explicit: raise TLError(f'"{varname}" is already defined but without explicit matching')
                if current.space is Missing:
                    if spacenode is not Missing:
                        raise TLError(f'"{varname}" is already defined in space "{self.pp(current.space)}"')
                else:
                    if spacenode is not Missing:
                        space = spacenode.eval(self, Missing)
                        if space.id != current.space.id:
                            raise TLError(f'"{varname}" is already defined in space "{self.pp(current.space)}"')
                if current.implicitly != implicitly: raise TLError(f'"{varname}" is already defined as implicitly "{self.pp(current.implicitly)}"')
                answer = current
        return answer

    def recursive(self, space):
        t = Recursive(next(self._seed), space)
        self._btypeById[t.id] = t
        return t

    def inter(self, types, space, id=Missing):
        sortedtypes = []
        for t in (sorted(types, key=lambda t: t.id)):
            if t not in sortedtypes:
                sortedtypes.append(t)
        totalCount, independentIds = 0, set()
        for t in sortedtypes:
            parents = _parentIds(t, self)
            totalCount += len(parents)
            independentIds = independentIds.union(parents)
        if len(independentIds) < totalCount:
            raise TLError('common rooots')
        sortedtypes = tuple(sortedtypes)
        if (inter := self._interByTypes.get(sortedtypes, Missing)) is Missing:
            if id is Missing:
                inter = Inter(bmtint, next(self._seed), sortedtypes, space)
                self._btypeById[inter.id] = inter
            else:
                # recursive intersection
                inter = Inter(bmtint, id, sortedtypes, space)
            self._interByTypes[sortedtypes] = inter
        return inter

    def union(self, types):
        sortedtypes = []
        for t in (sorted(types, key=lambda t: t.id)):
            if t not in sortedtypes:
                sortedtypes.append(t)
        sortedtypes = tuple(sortedtypes)
        if (union := self._unionByTypes.get(sortedtypes, Missing)) is Missing:
            union = Union(bmtuni, next(self._seed), types)
            self._btypeById[union.id] = union
            self._unionByTypes[sortedtypes] = union
        return union

    def tuple(self, types):
        if (tup := self._tupleByTypes.get(types, Missing)) is Missing:
            tup = Tuple(bmttup, next(self._seed), types)
            self._btypeById[tup.id] = tup
            self._tupleByTypes[types] = tup
        return tup

    def struct(self, fields):
        if (struct := self._structByFields.get(fields, Missing)) is Missing:
            struct = Struct(bmtstr, next(self._seed), fields)
            self._btypeById[struct.id] = struct
            self._structByFields[fields] = struct
        return struct

    def rec(self, fields):
        if (rec := self._recByFields.get(fields, Missing)) is Missing:
            rec = Rec(bmtrec, next(self._seed), fields)
            self._btypeById[rec.id] = rec
            self._recByFields[fields] = rec
        return rec

    def seq(self, contained):
        contained = contained[0]
        if (seq := self._seqByContained.get(contained, Missing)) is Missing:
            seq = Seq(bmtseq, next(self._seed), contained)
            self._btypeById[seq.id] = seq
            self._seqByContained[contained] = seq
        return seq

    def map(self, types):
        if (map := self._mapByLhsRhs.get(types, Missing)) is Missing:
            map = Map(bmtmap, next(self._seed), types[0], types[1])
            self._btypeById[map.id] = map
            self._mapByLhsRhs[types] = map
        return map

    def mutable(self, contained):
        contained = contained[0]
        if (mutable := self._mutableByContained.get(contained, Missing)) is Missing:
            mutable = Mutable(next(self._seed), contained)
            self._btypeById[mutable.id] = mutable
            self._mutableByContained[contained] = mutable
        return mutable

    def fn(self, types):
        if (fn := self._fnByLhsRhs.get(types, Missing)) is Missing:
            fn = Fn(bmtfnc, next(self._seed), types[0], types[1])
            self._btypeById[fn.id] = fn
            self._fnByLhsRhs[types] = fn
        return fn

    def fitsWithin(self, A, B):
        if A.id == B.id: return True
        fits, tByT = self._fitsCache.get((A.id, B.id), (Missing, Missing))
        if fits is not Missing: return fits
        if isinstance(A, Recursive): A = A.main
        if isinstance(B, Recursive): B = B.main
        if A.bmtid == bmtatm:
            if B.bmtid == bmtatm:
                self._fitsCache[(A.id, B.id)] = (A.id == B.id, {})
                return A.id == B.id
            elif B.bmtid == bmtuni:
                for t in B.types:
                    if self.fitsWithin(A, t):
                        self._fitsCache[(A.id, B.id)] = (True, {})
                        return True
                self._fitsCache[(A.id, B.id)] = (False, {})
                return False
            elif B.bmtid == bmtsvr:
                self._fitsCache[(A.id, B.id)] = (True, {B: A})
                return True
            else:
                self._fitsCache[(A.id, B.id)] = (False, {})
                return False
        elif A.bmtid == bmtint:
            if B.bmtid == bmtint:
                As = set(A.types)
                Bs = set(B.types)
                if len(Bs.difference(As)) == 0:
                    self._fitsCache[(A.id, B.id)] = (True, {})
                    return True
                self._fitsCache[(A.id, B.id)] = (False, {})
                return False
            for t in A.types:
                if self.fitsWithin(t, B):
                    self._fitsCache[(A.id, B.id)] = (True, {})
                    return True
            self._fitsCache[(A.id, B.id)] = (False, {})
            return False
        elif A.bmtid == bmtuni:
            if B.bmtid == bmtuni:
                for t in A.types:
                    if not self.fitsWithin(t, B):
                        self._fitsCache[(A.id, B.id)] = (False, {})
                        return False
                self._fitsCache[(A.id, B.id)] = (True, {})
                return True
            else:
                self._fitsCache[(A.id, B.id)] = (False, {})
                return False
        else:
            raise NotYetImplemented('#3')


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



class OnErrorRollback:

    def __init__(self, tm):
        self.tm = tm
        self.et = None
        self.ev = None
        self.tb = None

    def __enter__(self):
        self.tm.checkpoint()
        return self

    def __exit__(self, et, ev, tb):
        self.et = et
        self.ev = ev
        self.tb = tb
        if et is None:
            # no exception was raised
            self.tm.commit()
            return True
        else:
            # print the tb to make it easier to figure what happened
            self.tm.rollback()
            traceback.print_tb(tb)
            raise ev

