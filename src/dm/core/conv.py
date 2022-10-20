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


import numpy as np, csv

from coppertop.pipe import *
from bones.core.sentinels import Missing
from bones.core.errors import NotYetImplemented
from bones.lang.structs import tvarray
from bones.lang.metatypes import BType
from dm.core.aggman import values, collect
from dm.core.datetime import toCTimeFormat, parseDate
from dm.core.types import bframe, bmap, txt, pylist, pydict, T1, N, pytuple, pydict_keys, pydict_values, date, index, \
    num, npfloat, btup, bseq, matrix


array_ = (N**num)&tvarray
matrix_ = matrix&tvarray


# **********************************************************************************************************************
# to
# **********************************************************************************************************************

@coppertop(style=binary)
def to(x:pydict+pylist, t:bmap) -> bmap:
    return t(x)

@coppertop(style=binary)
def to(x, t):
    if isinstance(t, BType):
        return t(x)
    try:
        return t(x)
    except Exception as ex:
        raise TypeError(f'Catch all can\'t convert {repr(x)} to {repr(t)} - {ex}')

@coppertop(style=binary)
def to(x:pydict_keys+pydict_values, t:pylist) -> pylist:
    return list(x)

@coppertop(style=binary)
def to(x, t:pylist) -> pylist:
    return list(x)

@coppertop(style=binary)
def to(x:bmap, t:pydict) -> pydict:
    return dict(x.items())

@coppertop(style=binary)
def to(x, t:pydict) -> pydict:
    return dict(x)

@coppertop(style=binary)
def to(x:txt, t:date, f:txt) -> date:
    return parseDate(x, toCTimeFormat(f))

@coppertop(style=binary)
def to(x, t:txt) -> txt:
    return str(x)

@coppertop(style=binary)
def to(v:T1, t:T1) -> T1:
    return v

@coppertop(style=binary)
def to(x, t:index) -> index:
    return int(x)

@coppertop(style=binary)
def to(x, t:num) -> num:
    return float(x)

@coppertop(style=binary)
# def to(x:pylist, t:matrix&tvarray) -> matrix&tvarray:
def to(x:pylist, t:matrix&tvarray) -> matrix&tvarray:
    return (matrix&tvarray)(t, x)

@coppertop(style=binary)
def to(x:matrix&tvarray, t:array_) -> array_:
    return array_(x.reshape(max(x.shape)))

@coppertop(style=binary)
def to(x:array_, t:np.ndarray) -> np.ndarray:
    return np.array(x)

def parseNum(x:txt) -> num:
    try:
        return float(x)
    except:
        return np.nan

@coppertop(style=binary)
def to(xs:pylist, t:array_) -> array_:
    return array_([parseNum(x) for x in xs])

@coppertop(style=binary)
def to(xs:pylist, t:(N**date)&tvarray, f:txt) -> (N**date)&tvarray:
    cFormat = toCTimeFormat(f)
    return tvarray((N**date)&tvarray, [parseDate(x, cFormat) for x in xs])

@coppertop
def toRowVec(xs:pylist) -> matrix&tvarray:
    if len(xs) == 0: raise ValueError("can't create an empty matrix")
    if isinstance(xs[0], str):
        raise NotYetImplemented()
    raise NotYetImplemented()
    cFormat = toCTimeFormat(f)
    return tvarray((N**date)&tvarray, [parseDate(x, cFormat) for x in xs])

@coppertop
def toColVec(xs:pylist) -> matrix&tvarray:
    if len(xs) == 0: raise ValueError("can't create an empty matrix")
    if isinstance(xs[0], str):
        raise NotYetImplemented()
    return tvarray(matrix&tvarray, xs).reshape(len(xs), 1)
