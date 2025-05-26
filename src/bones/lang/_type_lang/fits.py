# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

import collections

from bones.core.sentinels import Missing
from bones.core.errors import NotYetImplemented



bmtnul = 0      # i.e. not initialised yet
bmtatm = 1      # snuggled in the highest nibble in the type's metadata, i.e. 0x1000_0000

bmtint = 2
bmtuni = 3

bmttup = 4
bmtstr = 5
bmtrec = 6

bmtseq = 7
bmtmap = 8
bmtfnc = 9

bmtsvr = 10


Fits = collections.namedtuple('Fits', ['fits', 'tByT'])
Fits.__bool__ = lambda self: self.fits

IDENTICAL = Fits(True, {})

def fitsWithin(tm, A, B):
    if A.id == B.id: return IDENTICAL
    fits, tByT = tm._fitsCache.get((A.id, B.id), (Missing, Missing))
    if fits is not Missing: return fits
    if type(A).__name__ == 'TBC': A = A.btype
    if type(B).__name__ == 'TBC': B = B.btype
    tm._fitsCache[(A.id, B.id)] = answer = _fitsWithin(tm, A, B)
    return answer

def _fitsWithin(tm, A, B):
    if tm.bmtid(A) == bmtatm:
        if tm.bmtid(B) == bmtatm:
            return Fits(A.id == B.id, {})
        elif tm.bmtid(B) == bmtuni:
            for t in tm.unionTl(B):
                if fitsWithin(tm, A, t):
                    return Fits(True, {})
            return Fits(False, {})
        elif tm.bmtid(B) == bmtsvr:
            return Fits(True, {B: A})
        else:
            return Fits(False, {})
    elif tm.bmtid(A) == bmtint:
        if tm.bmtid(B) == bmtint:
            As = set(tm.intersectionTl(A))
            Bs = set(tm.intersectionTl(B))
            if len(Bs.difference(As)) == 0:
                return Fits(True, {})
            return Fits(False, {})
        for t in tm.intersectionTl(A):
            if fitsWithin(tm, t, B):
                return Fits(True, {})
        return Fits(False, {})
    elif tm.bmtid(A) == bmtuni:
        if tm.bmtid(B) == bmtuni:
            for t in tm.unionTL(A):
                if not fitsWithin(tm, t, B):
                    return Fits(False, {})
            return Fits(True, {})
        else:
            return Fits(False, {})
    else:
        raise NotYetImplemented('#3')

