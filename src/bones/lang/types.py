# **********************************************************************************************************************
#
#                             Copyright (c) 2011-2021 David Briant. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
#
# **********************************************************************************************************************

import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)


# define the types here that are needed by the language itself


__all__ = [
    'noun', 'nullary', 'unary', 'binary', 'ternary',
    'mem',
    'TBI', 'void', 'null',
    'tup', 'struct', 'frame',
    'litint', 'litdec', 'littxt', 'litsym', 'litsyms', 'litdate', 'litframe', 'littup', 'litstruct',
]

from bones.core.sentinels import Null, Void
from bones.lang.metatypes import BTAtom, BType

mem = BType('mem')
noun = BTAtom("noun")
nullary = BTAtom("nullary")
unary = BTAtom("unary")
binary = BTAtom("binary")
ternary = BTAtom("ternary")

TBI = BTAtom("TBI", space=mem)
void = BTAtom('void', space=mem)      # something that isn't there and shouldn't be there
null = BTAtom('null')                       # the null set - something that isn't there and that's okay

Null._t = null
Void._t = void

# so we can have more than one class for frames (and tups and structs, maybe less likely)
# dframe = frame[dstruct].nameAs('dframe')
# polarframe = frame[pl.DataFrame].nameAs('polarframe')
tup = BTAtom('tup')
struct = BTAtom('struct')
frame = BTAtom('frame')


# literal types used in parser
litint = BTAtom('litint', space=mem)      # OPEN: sort out standard types
litdec = BTAtom('litdec', space=mem)
littxt = BTAtom('littxt', space=mem)      # this allows us to provide different encodings in source and map to the core one
litsym = BTAtom('litsym', space=mem)
litsyms = BTAtom('litsyms', space=mem)
litdate = BTAtom('litdate', space=mem)
littup = BType('littup: littup & tup in mem')
litstruct = BType('litstruct: litstruct & struct in mem')
litframe = BType('litframe: litframe & frame in mem')



# expose a bunch of schema variables - code can get more via schemaVariableForOrd
T = BType('T')
for i in range(1, 10):
    t = BType(f'T{i}')
    locals()[t.name] = t
# for o in range(26):
#     t = BType(f"T{chr(ord('a') + o)}")
#     locals()[t.name] = t

__all__ += [
    'T',
    'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', #'T10',
    # 'T11', 'T12', 'T13', 'T14', 'T15', 'T16', 'T17', 'T18', 'T19', 'T20',
    # 'Ta', 'Tb', 'Tc', 'Td', 'Te', 'Tf', 'Tg', 'Th', 'Ti', 'Tj', 'Tk', 'Tl', 'Tm',
    # 'Tn', 'To', 'Tp', 'Tq', 'Tr', 'Ts', 'Tt', 'Tu', 'Tv', 'Tw', 'Tx', 'Ty', 'Tz'
]
