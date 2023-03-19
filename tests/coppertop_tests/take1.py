# **********************************************************************************************************************
#
#                             Copyright (c) 2021 David Briant. All rights reserved.
#                               Contact the copyright holder for licensing terms.
#
# **********************************************************************************************************************


import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

from coppertop.pipe import *
from dm.core.types import pylist, pytuple, index

ellipsis = type(...)


sys._BREAK = True  # hasattr(sys, '_BREAK') and sys._BREAK


@coppertop(style=binary)
def _take(xs:pylist, n:index) -> pylist:
    '''hello'''
    if n >= 0:
        return xs[:n]
    else:
        return xs[len(xs) + n:]

@coppertop(style=binary)
def _take(xs: pylist, os: pylist) -> pylist:
    '''there'''
    return [xs[o] for o in os]

@coppertop(style=binary)
def _take(xs:pylist, ss:pytuple) -> pylist:
    s1, s2 = ss
    if s1 is Ellipsis:
        if s2 is Ellipsis:
            return xs
        else:
            return xs[:s2]
    else:
        if s2 is Ellipsis:
            return xs[s1:]
        else:
            return xs[s1:s2]
