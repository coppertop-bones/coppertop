# **********************************************************************************************************************
#
#                             Copyright (c) 2017-2021 David Briant. All rights reserved.
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

BONES_NS = ''

import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

import csv

from coppertop.pipe import *
from bones.core.errors import NotYetImplemented
from bones.core.sentinels import Missing
from dm.core.types import bframe, txt, pydict, btup


# **********************************************************************************************************************
# frame.fromCsv
# **********************************************************************************************************************

@coppertop(module='dm.frame')
def fromCsv(pfn:txt, renames:pydict, conversions:pydict) -> bframe:
    with open(pfn, mode='r') as f:
        r = csv.DictReader(f)
        d = {}
        for name in r.fieldnames:
            d[name] = list()
        for cells in r:
            for k, v in cells.items():
                d[k].append(v)
        a = bframe()
        for k in d.keys():
            newk = renames.get(k, k)
            fn = conversions.get(newk, lambda l: btup(l, Missing))     ## we could insist the conversions return btup s
            a[newk] = fn(d[k])
    return a

@coppertop(module='dm.frame')
def fromCsv(pfn:txt, renames:pydict, conversions:pydict, cachePath) -> bframe:
    with open(pfn, mode='r') as f:
        r = csv.DictReader(f)
        d = {}
        for name in r.fieldnames:
            d[name] = list()
        for cells in r:
            for k, v in cells.items():
                d[k].append(v)
        a = bframe()
        for k in d.keys():
            newk = renames.get(k, k)
            fn = conversions.get(newk, lambda l: btup(l, Missing))     ## we could insist the conversions return btup s
            a[newk] = fn(d[k])
    return a


# **********************************************************************************************************************
# sortBy
# **********************************************************************************************************************

@coppertop
def sortBy(x:bframe, fields):
    raise NotYetImplemented()

@coppertop
def sortBy(x:bframe, fields, directions):
    raise NotYetImplemented()


# **********************************************************************************************************************
# lj
# **********************************************************************************************************************

@coppertop(style=binary)
def lj(agg1:bframe, agg2:bframe):
    raise NotYetImplemented()


# **********************************************************************************************************************
# aj
# **********************************************************************************************************************

@coppertop(style=binary)
def aj(agg1:bframe, agg2:bframe):
    raise NotYetImplemented()

