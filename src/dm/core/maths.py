# **********************************************************************************************************************
#
#                             Copyright (c) 2017-2020 David Briant. All rights reserved.
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


_EPS = 7.105427357601E-15      # i.e. double precision


import builtins, numpy as np, math

from bones.core.errors import NotYetImplemented
from coppertop.pipe import *
from dm.core.types import T1, T2, pylist, N, num, matrix, t
from bones.lang.structs import tvarray

import itertools, scipy

array_ = (N**num)&tvarray
matrix_ = matrix&tvarray

@coppertop(style=binary)
def dotProduct(A:matrix&tvarray, B:matrix&tvarray) -> num:
    return float(np.dot(A, B))

@coppertop
def diff(v:array_) -> array_:
    return np.diff(v)


# **********************************************************************************************************************
# permutations (arrangements) and combinations
# perms and combs are such useful variable names so use fuller name in fn
# **********************************************************************************************************************

@coppertop(style=binary)
def permutations(xs, k):
    return tuple(itertools.permutations(xs, k))

@coppertop(style=binary)
def nPermutations(n, k):
    return math.perm(n, k)

@coppertop(style=binary)
def permutationsR(xs, k):
    return tuple(itertools.product(*([xs]*k)))

@coppertop(style=binary)
def nPermutationsR(n, k):
    return n ** k

@coppertop(style=binary)
def combinations(xs, k):
    return tuple(itertools.combinations(xs, k))

@coppertop(style=binary)
def nCombinations(n, k):
    return math.comb(n, k)

@coppertop(style=binary)
def combinationsR(xs, k):
    return tuple(itertools.combinations_with_replacement(xs, k))

@coppertop(style=binary)
def nCombinationsR(n, k):
    return scipy.special.comb(n, k, exact=True)


# **********************************************************************************************************************
# comparison
# **********************************************************************************************************************

@coppertop(style=nullary)
def EPS():
    return _EPS

@coppertop(style=binary)
def closeTo(a, b):
    if abs(a) < _EPS:
        return abs(b) < _EPS
    else:
        return abs(a - b) / abs(a) < _EPS

@coppertop(style=binary)
def closeTo(a, b, tolerance):
    if abs(a) < tolerance:
        return abs(b) < tolerance
    else:
        return abs(a - b) / abs(a) < tolerance

@coppertop
def within(x, a, b):
    # answers true if x is in the closed interval [a, b]
    return (a <= x) and (x <= b)


# **********************************************************************************************************************
# functions
# **********************************************************************************************************************

@coppertop
def log(v:array_) -> array_:
    return np.log(v)

@coppertop
def sqrt(x):
    return np.sqrt(x)   # answers a nan rather than throwing


# **********************************************************************************************************************
# stats
# **********************************************************************************************************************

@coppertop
def cov(A:matrix&tvarray) -> matrix&tvarray:
    return (matrix&tvarray)(np.cov(A))

@coppertop
def max(x:matrix&tvarray):
    return np.max(x)

@coppertop
def max(x):
    return builtins.max(x)

@coppertop
def mean(ndOrPy):
    return np.mean(ndOrPy)

@coppertop
def min(x:matrix&tvarray):
    return np.min(x)

@coppertop
def min(x):
    return builtins.min(x)

@coppertop
def std(ndOrPy):
    return np.std(ndOrPy, 0)

@coppertop
def std(ndOrPy, dof):
    return np.std(ndOrPy, dof)

@coppertop
def sum(x):
    return builtins.sum(x)

@coppertop
def sum(x:(N**T1)[pylist][T2]) -> num:
    return builtins.sum(x._v)

@coppertop
def sum(x:(N**T1)[pylist]) -> num:
    return builtins.sum(x._v)


# **********************************************************************************************************************
# rounding
# **********************************************************************************************************************

@coppertop
def roundDown(x):
    # i.e. [roundDown(-2.9), roundDown(2.9,0)] == [-3, 2]
    return math.floor(x)

@coppertop
def roundUp(x):
    # i.e. [roundUp(-2.9), roundUp(2.9,0)] == [-2, 3]
    return math.ceil(x)

@coppertop
def roundHalfToZero(x):
    # i.e. [round(-2.5,0), round(2.5,0)] == [-2.0, 2.0]
    return round(x)

@coppertop
def roundHalfFromZero(x):
    raise NotYetImplemented()

@coppertop
def roundHalfToNeg(x):
    raise NotYetImplemented()

@coppertop
def roundHalfToPos(x):
    raise NotYetImplemented()

@coppertop
def round(xs:matrix&tvarray, figs:t.count) -> matrix&tvarray:
    return (matrix&tvarray)(np.round(xs, figs))

@coppertop
def round(xs:array_, figs:t.count) -> array_:
    return (array_)(np.round(xs, figs))
