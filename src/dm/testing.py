# **********************************************************************************************************************
#
#                             Copyright (c) 2020-2021 David Briant. All rights reserved.
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


import builtins
from bones import jones
from coppertop.pipe import *
from dm.core.maths import closeTo
from dm.core.types import bmap, T1, T2, T3, T4, T5, T6, bool, pydict, bstruct, matrix
from bones.lang.structs import tvarray

_EPS = 7.105427357601E-15      # i.e. double precision



@coppertop(style=ternary)
def check(actual, fn, expected):
    fnName = fn.name if hasattr(fn, 'name') else (fn.d.name if isinstance(fn, jones._fn) else '')
    with context(showFullType=False):
        if fn is builtins.type or fnName == 'typeOf':
            res = fn(actual)
            assert res == expected, f'Expected type <{expected}> but got type <{fn(actual)}>'
        else:
            res = fn(actual, expected)
            ppAct = repr(actual)
            ppExp = repr(expected)
            assert res == True, f'\nChecking fn \'{fn}\' failed the following:\nactual:   {ppAct}\nexpected: {ppExp}'
    return actual

@coppertop(style=binary, dispatchEvenIfAllTypes=True)
def equal(a, b) -> bool:
    return a == b

@coppertop(style=binary, dispatchEvenIfAllTypes=True)
def equal(a:matrix&tvarray, b:matrix&tvarray) -> bool:
    return bool((a == b).all())

@coppertop(style=binary)
def different(a, b) -> bool:
    return a != b

@coppertop(style=binary)
def different(a:matrix&tvarray, b:matrix&tvarray) -> bool:
    return bool((a != b).any())

@coppertop(style=binary)
def sameLen(a, b):
    return len(a) == len(b)

@coppertop(style=binary)
def sameShape(a, b):
    return a.shape == b.shape


# **********************************************************************************************************************
# sameNames
# **********************************************************************************************************************

@coppertop(style=binary)
def sameKeys(a:pydict, b:pydict) -> bool:
    return a.keys() == b.keys()

@coppertop(style=binary)
def sameNames(a:bmap, b:bmap) -> bool:
    return a._keys() == b._keys()

# some adhoc are defined like this (num ** account)[bstruct]["positions"]
@coppertop(style=binary)
def sameNames(a:(T1 ** T2)[bstruct][T3], b:(T4 ** T2)[bstruct][T5]) -> bool:
    return a._keys() == b._keys()


@coppertop(style=binary)
def sameNames(a:(T1 ** T2)[bstruct][T3], b:(T5 ** T4)[bstruct][T6]) -> bool:
    assert a._keys() != b._keys()
    return False

# many structs should be typed (BTStruct)[bstruct] and possibly (BTStruct)[bstruct][T]   e.g. xy in pixels and xy in data

# if we can figure how to divide up the dispatch space (or even indicate it) this would be cool
# the total space below is T1[BTStruct][bstruct] * T2[BTStruct][bstruct] with
# T1[BTStruct][bstruct] * T1[BTStruct][bstruct] as a subspace / set
# can dispatch to the total space and then to the specific subset - with one as default
# @coppertop(style=binary)
# def sameNames(a:T1[BTStruct][bstruct], b:T2[BTStruct][bstruct]) -> bool:
#     assert a._keys() != b._keys()
#     return False
#
# #@coppertop(style=binary, memberOf=(T1[BTStruct][bstruct]) * (T2[BTStruct][bstruct])))
# @coppertop(style=binary)
# def sameNames(a:T1[BTStruct][bstruct], b:T1[BTStruct][bstruct]) -> bool:
#     assert a._keys() == b._keys()
#     return True

# any should really be unhandles or alt or others or not default


