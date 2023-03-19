# **********************************************************************************************************************
#
#                             Copyright (c) 2021 David Briant. All rights reserved.
#                               Contact the copyright holder for licensing terms.
#
# **********************************************************************************************************************


import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)


from coppertop.pipe import *
from bones.core.utils import assertRaises
from bones.core.errors import NotYetImplemented
from bones.lang.metatypes import BTAtom
import dm.core, dm.testing
from groot import check, equals, fitsWithin, collect
from coppertop_tests.take1 import _take
from coppertop_tests.take2 import _take
from dm.core.types import index, pylist, litint, btup

mat = BTAtom.ensure("mat2")
vec = BTAtom.ensure("vec2")


@coppertop(style=binary)
def mmul(A:mat, B:vec) -> vec:
    answer = A @ B | vec
    return answer


def test_mmul():
    a = btup(mat, [[1, 2], [3, 4]])
    b = btup(vec, [1, 2])
    res = a >> mmul >> b
    res >> check >> typeOf >> vec


def testTake():
    [1, 2, 3] >> _take >> 2 >> check >> equals >> [1, 2]
    [1, 2, 3] >> _take >> -2 >> check >> equals >> [2, 3]
    [1, 2, 3] >> _take >> (..., ...) >> check >> equals >> [1, 2, 3]
    [1, 2, 3] >> _take >> (1, ...) >> check >> equals >> [2, 3]
    [1, 2, 3] >> _take >> (..., 2) >> check >> equals >> [1, 2]
    [1, 2, 3] >> _take >> (0, 2) >> check >> equals >> [1, 2]

    {"a":1, "b":2, "c":3} >> _take >> "a" >> check >> equals >> {"a":1}
    {"a":1, "b":2, "c":3} >> _take >> ["a", "b"] >> check >> equals >> {"a":1, "b":2}


def testTypeOf():
    1 >> check >> typeOf >> litint
    1 >> typeOf >> check >> fitsWithin >> index


def testDoc():
    _take(pylist, index).d.__doc__ >> check >> equals >> 'hello'
    _take(pylist, pylist).d.__doc__ >> check >> equals >> 'there'


def main():
    testTake()
    testTypeOf()
    testDoc()
    test_mmul()


if __name__ == '__main__':
    main()
    print('pass')

