# **********************************************************************************************************************
#
#                             Copyright (c) 2021 David Briant. All rights reserved.
#                               Contact the copyright holder for licensing terms.
#
# **********************************************************************************************************************

import sys
# sys._TRACE_IMPORTS = True
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

from coppertop.pipe import *
from bones.core.utils import assertRaises
from dm.testing import check, equals
from dm.core.aggman import collect
from dm.core.types import txt, index, N, py, bseq, pylist


def test_anon():
    f = makeFn(index^index, lambda x: x + 1)
    fxs = bseq((N ** index)[bseq], [1, 2, 3]) >> collect >> f
    fxs >> check >> typeOf >> (N ** index)[bseq]
    with assertRaises(TypeError):
        bseq((N ** index)[bseq], [1, 2, 3]) >> collect >> makeFn(txt ^ txt, lambda x: x + 1)


def test_partial():
    @coppertop
    def myunary_(a, b, c):
        return a + b + c
    myunary_ >> typeOf >> check >> equals >> ((py*py*py)^py)

    @coppertop
    def myunary(a: index, b: index, c: index) -> index:
        return a + b + c

    myunary >> check >> typeOf >> ((index*index*index)^index)
    myunary(1,_,3) >> check >> typeOf >> (index^index)

    [1, 2, 3] >> collect >> myunary(0,_,1) >> check >> typeOf >> pylist >> check >> equals >> [2,3,4]

    [1,2,3] >> collect >> makeFn((index*index) ^ index, lambda x, y: x + y)(_, 1) >> check >> equals >> [2,3,4]


def main():
    test_anon()
    test_partial()


if __name__ == '__main__':
    main()
    print('pass')

