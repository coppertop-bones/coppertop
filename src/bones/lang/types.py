# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)


# just the types needed by the bones itself

__all__ = [
    'noun', 'nullary', 'unary', 'binary', 'ternary',
    'mem',
    'TBI', 'void', 'null',
    'tup', 'struct', 'frame',
    'litint', 'litdec', 'littxt', 'litsym', 'litsyms', 'litdate', 'litframe', 'littup', 'litstruct',
]

from bones.core.sentinels import Null, Void
from bones.ts.metatypes import BTAtom, BType

mem = BType('mem')
noun = BTAtom("noun")
nullary = BTAtom("nullary")
unary = BTAtom("unary")
binary = BTAtom("binary")
ternary = BTAtom("ternary")

TBI = BTAtom("TBI", space=mem)
void = BTAtom('void', space=mem)        # something that isn't there and shouldn't be there
null = BTAtom('null')                   # the null set - something that isn't there and that's okay

Null._t = null
Void._t = void

# bones allows for literal frames, tuples and structs and since we would like to have multiple implementations, for
# example pandas and polars etc, we need root types to derive from.
tup = BTAtom('tup')
struct = BTAtom('struct')
frame = BTAtom('frame')

litint = BTAtom('litint', space=mem)
litdec = BTAtom('litdec', space=mem)
littxt = BTAtom('littxt', space=mem)
litsym = BTAtom('litsym', space=mem)
litsyms = BTAtom('litsyms', space=mem)
litdate = BTAtom('litdate', space=mem)
littup = BType('littup: littup & tup in mem')
litstruct = BType('litstruct: litstruct & struct in mem')
litframe = BType('litframe: litframe & frame in mem')

T = BType('T')
for i in range(1, 10):
    t = BType(f'T{i}')
    locals()[t.name] = t

__all__ += ['T','T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9']
