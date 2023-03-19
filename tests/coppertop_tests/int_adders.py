# **********************************************************************************************************************
#
#                             Copyright (c) 2021 David Briant. All rights reserved.
#                               Contact the copyright holder for licensing terms.
#
# **********************************************************************************************************************

BONES_NS = 'tests.adders'

from coppertop.pipe import *
from dm.core.types import index, pylist


@coppertop
def addOne(x:index) -> index:
    return x + 1

# test that functions can be redefined in the same file (and thus same module)
@coppertop
def addOne(x: index) -> index:
    return x + 1

@coppertop
def eachAddOne(xs:pylist) -> pylist:
    answer = []
    for x in xs:
        answer.append(x >> addOne)
    return answer

@coppertop
def addTwo(x:index) -> index:
    return x + 2

@coppertop
def eachAddTwo(xs:pylist) -> pylist:
    answer = []
    for x in xs:
        answer.append(x >> addTwo)
    return answer
