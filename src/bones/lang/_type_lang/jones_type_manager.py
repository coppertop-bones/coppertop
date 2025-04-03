# **********************************************************************************************************************
# Copyright (c) 2025 David Briant. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
# **********************************************************************************************************************


from bones.core.errors import NotYetImplemented
from bones.core.sentinels import Missing

from bones import jones
from bones.jones import BTypeError
from bones.lang.core import TLError, bmtnul, bmtatm, bmtint, bmtuni, bmttup, bmtstr, bmtrec, bmtseq, bmtmap, bmtfnc, bmtsvr, bmtnameById
from bones.lang._type_lang.utils import OnErrorRollback
from bones.lang._type_lang.fits import fitsWithin



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
        if (current := self._tm.lookup(name)).id and self._tm.bmetatypeid(btype) != bmtnul:
            btype = self._tm.checkAtom(current, btype=btype or None, explicit=explicit or False, space=space or None, implicitly=implicitly or None)
        else:
            btype = self._tm.initAtom(btype=btype or None, explicit=explicit or False, space=space or None, implicitly=implicitly or None)
        return self.bind(name, btype)

    def bind(self, name, btype):
        try:
            btype = self._tm.bind(name, btype)
            if self._tm.isRecursive(btype) and self._tm.bmetatypeid(btype) != bmtnul:
                # reserving sets recursive !! bother so defend against it here
                self._tbcByVarname.pop(name, None)
                if self._implicitRecursive and self._implicitRecursive.id == btype.id: self._implicitRecursive = Missing
        except BTypeError as ex:
            if 'already bound' in ex.args[0]:
                current = self._tm.lookup(name)
                bmtid = self._tm.bmetatypeid(current)
                raise BTypeError(f'"{name}" is already bound to {bmtnameById[bmtid]}{current.id}')
            else:
                raise
        return btype

    def bmtid(self, t):
        return self._tm.bmetatypeid(t)

    def check(self, A, B):
        if A.id == B.id: return True
        if self.bmtid(A) != self.bmtid(B): raise BTypeError()
        if self.bmtid(A) == bmtatm:
            # OPEN: implement properly
            return True
        raise NotYetImplemented()

    def fn(self, tArgs, tRet, *, btype=Missing):
        return self._tm.fn(tArgs, tRet, btype=btype or None)

    def fnTArgs(self, btype):
        return self._tm.fnTArgs(btype)

    def fnTRet(self, btype):
        return self._tm.fnTRet(btype)

    def hasT(self, btype):
        return self._tm.hasT(btype)

    def initAtom(self, *, explicit=Missing, space=Missing, implicitly=Missing, btype=Missing):
        return self._tm.initAtom(btype=btype or None, explicit=explicit or False, space=space or None, implicitly=implicitly or None)

    def intersection(self, types, *, space=Missing, btype=Missing):
        return self._tm.intersection(*types, space=space or None, btype=btype or None)

    def intersectionTl(self, t):
        return self._tm.intersectionTl(t)

    def isRecursive(self, t):
        return self._tm.isRecursive(t)

    def lookup(self, name):
        return self._tm.lookup(name) or Missing

    def lookupOrImplicitTbc(self, name):
        # gets the type for the name creating up to one implicit recursive type if it doesn't exist
        if (btype := self._tm.lookup(name)).id == 0:
            # do the implicit recursive check
            if (currentOne := self._implicitRecursive) is not Missing and self._tm.name(currentOne) != name:
                raise TLError(
                    f'Only one implicit recursive type can be defined simutaneously. "{name}" encountered but "{self._tm.name(currentOne)}" is already the currently defined implicit recursive type.')
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

    def rootSpace(self, t):
        return self._tm.rootSpace(t)

    def schemavar(self, btype=Missing):
        return self._tm.schemavar(btype=btype or None)

    def seq(self, contained, *, btype=Missing):
        return self._tm.seq(contained, btype=btype or None)

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


# intersection get or create
# get intersect_tlid
# btype = lookup_intersection
# if not found
#     btype = reserve(optional space)
#     btype = intersect(self, tlid)
# if btype and space
#     assert btype.space == space
# return btype
#
#
# intersection create and bind
#

# reserve -> note_tbc, add_tbc, make_tbc, tbc, create_tbc
#
# confirm_inter_in
# confirm_tuple
#
# vs
# inter_in(B_NAT or tbcId, ...),
# tuple(B_NAT or tbcId, ...),



# we are trying to avoid accidentally create an intersection that we later want to create in a space
#
# 5 cases
# fred: A & B
# fred: fred & B
# (A&B)
# fred: A & B in C
# fred: fred & B in C
#
# (A&B) will get A & B in C or A & B if fred is already bound or create A & B (not in C) if not already bound
# (A & B in C) is illegal
#
#
# test1 => GBP: GBP_ & ccy in ccyfx
# test2 => GBP: GBP & ccy in ccyfx
# test3 => GBP: GBP & ccy in ccy
#
# // &
# GBP = lookupOrImplicitTbc(GBP) => bind(GBP, reserve())
# ccy = lookupOrImplicitTbc(ccy)
#
# // in
# ccyfx = lookup(ccyfx)
#
# // bind
# GBP = lookup(GBP)
#
# // create and bind
# if GBP is tbc:
#     bind(GBP, confirm_inter_in(self=GBP, types=(GBP, ccy), space=ccyfx)) OR
#     bind(GBP, inter_in(self=GBP, types=(GBP, ccy), space=ccyfx))
# elif GBP is B_NAT:
#     bind(GBP, inter_in(types=(GBP, ccy), space=ccyfx)) OR
#     bind(GBP, inter_in(self=B_NEW, types=(GBP, ccy), space=ccyfx))
# else:
#     assert GBP == inter(types=(GBP, ccy))
#
# can't be in yourself? yes, here's a counter example
# domfor: {dom: ccy & T1, for: ccy & T2} & domfor in domfor
# {dom:GBP, for:USD} & domfor in domfor
# {dom:USD, for:JPY} & domfor in domfor

#
# to be confirmed
# confirm
#
# to be defined
# define
# however surely fred: ... is a define too



# I was trying to make it impossible to mutate via the api
# but I think that is impossible so instead we should just make it hard



