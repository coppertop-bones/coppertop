# **********************************************************************************************************************
#
#                             Copyright (c) 2021 David Briant. All rights reserved.
#                               Contact the copyright holder for licensing terms.
#
# **********************************************************************************************************************


import sys, builtins
# sys._TRACE_IMPORTS = True
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

from coppertop.pipe import *
from bones.core.utils import assertRaises
import dm.core, dm.testing, dm.pp
from groot import check, equals, PP, collect, interleave
from dm.core.types import txt, index, num, bool, T1, litint, pylist
from bones.lang.metatypes import BTAtom
from bones.lang.structs import tv

from coppertop_tests.int_adders import addOne, eachAddOne, eachAddTwo


A = BTAtom.ensure("A")
B = BTAtom.ensure("B")
(A & B & litint).setCoercer(tv)
(A & litint).setCoercer(tv)
(B & litint).setCoercer(tv)



@coppertop
def fred(a:index, b:txt, c:bool, d, e:num, f:num, g:txt+num) -> txt:
    return [a,b,c,d,e,f,g] >> collect >> typeOf >> collect >> builtins.str >> interleave >> ","
    # [a,b,c,d,e,f,g] collect {e typeOf to(,<:txt>)} interleave ","

@coppertop
def addOneAgain(x: txt) -> txt:
    return x + 'One'

@coppertop
def addOneAgain(x):
    return x + 1

@coppertop
def addOneAgain(x):
    return x + 2

@coppertop
def joe(x:pylist):
    return x

@coppertop
def sally(x:T1 & A & B, tByT):
    return f"AB {tByT[T1]}"

@coppertop
def sally(x:T1&A, tByT):
    return f"A {tByT[T1]}"



def test_sally():
    with context(stop=True):
        (1 | (litint & A & B)) >> sally >> check >> equals >> "AB litint"
        (1 | (litint & A)) >> sally >> check >> equals >> "A litint"
        with assertRaises(Exception):
            1 | (litint & B) >> sally >> check >> equals >> "A"

def test_joe():
    # check joe can't be called with dict_keys
    with assertRaises(Exception):
        dict(a=1).keys() >> joe

def test_redefine():
    1 >> addOneAgain >> check >> equals >> 3

def check_types_of_weak_things():
    fred(1 | index, "hello", True, (), 1, 1.3, 1.3 | num) >> check >> equals >> "index,txt,bool,pytuple,litint,litdec,num"


def main():
    test_sally()
    test_redefine()
    check_types_of_weak_things()
    test_joe()


if __name__ == '__main__':
    main()
    print('pass')

