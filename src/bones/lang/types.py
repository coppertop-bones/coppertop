# **********************************************************************************************************************
#
#                             Copyright (c) 2011-2021 David Briant. All rights reserved.
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

import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)


# define the types here that are needed by the language itself


__all__ = [
    'noun', 'nullary', 'unary', 'binary', 'ternary',
    'obj',
    'TBI', 'void', 'null',
    'litint', 'litdec', 'littxt', 'litsym', 'litsyms', 'litdate',
    'btup', 'bstruct', 'bseq', 'bmap', 'bframe',
]

from bones.core.sentinels import Null, Void
from bones.lang.metatypes import BTAtom, BType


noun = BTAtom.define("noun")
nullary = BTAtom.define("nullary")
unary = BTAtom.define("unary")
binary = BTAtom.define("binary")
ternary = BTAtom.define("ternary")
# rau = BTAtom.define("rau")

# obj is used in setOrthogonal to show the type and an object of some sort and thus the intersection with
# other orthogonal(obj) types is uninhabited
obj = BTAtom.define("obj")

TBI = BTAtom.define("TBI").setOrthogonal(obj)
void = BTAtom.define('void').setOrthogonal(obj)     # something that isn't there and shouldn't be there
null = BTAtom.define('null')                        # the null set - something that isn't there and that's okay

Null._t = null
Void._t = void


# types used in parser
litint = BTAtom.define('litint').setOrthogonal(obj)
litdec = BTAtom.define('litdec').setOrthogonal(obj)
littxt = BTAtom.define('littxt').setOrthogonal(obj)      # this allows us to provide different encodings in source and map to the core one
litsym = BTAtom.define('litsym').setOrthogonal(obj)
litsyms = BTAtom.define('litsyms').setOrthogonal(obj)
litdate = BTAtom.define('litdate').setOrthogonal(obj)

# types for the implementation classes
btup = BTAtom.define('btup').setOrthogonal(obj)
bstruct = BTAtom.define('bstruct').setOrthogonal(obj)
bseq = BTAtom.define('bseq').setOrthogonal(obj)
bmap = BTAtom.define('bmap').setOrthogonal(obj)
bframe = BTAtom.define('bframe').setOrthogonal(obj)


def _addConstructors():
    from bones.lang.structs import tvarray, bstruct_, bseq_, bmap_, bframe_
    import bones.lang.structs
    btup.setConstructor(tvarray)
    bstruct.setConstructor(bstruct_)
    bseq.setConstructor(bseq_)
    bmap.setConstructor(bmap_)
    bframe.setConstructor(bframe_)

    bones.lang.structs.btup = btup
    bones.lang.structs.bstruct = bstruct
    bones.lang.structs.bseq = bseq
    bones.lang.structs.bmap = bmap
    bones.lang.structs.bframe = bframe

_addConstructors()



# expose a bunch of schema variables - code can get more via schemaVariableForOrd
T = BType('T')
for i in range(1, 21):
    t = BType(f'T{i}')
    locals()[t.name] = t
for o in range(26):
    t = BType(f"T{chr(ord('a') + o)}")
    locals()[t.name] = t

__all__ += [
    'T',
    'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10',
    'T11', 'T12', 'T13', 'T14', 'T15', 'T16', 'T17', 'T18', 'T19', 'T20',
    'Ta', 'Tb', 'Tc', 'Td', 'Te', 'Tf', 'Tg', 'Th', 'Ti', 'Tj', 'Tk', 'Tl', 'Tm',
    'Tn', 'To', 'Tp', 'Tq', 'Tr', 'Ts', 'Tt', 'Tu', 'Tv', 'Tw', 'Tx', 'Ty', 'Tz'
]
