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


# just the types needed by the bones language itself

__all__ = [
    'noun', 'nullary', 'unary', 'binary', 'ternary',
    'mem',
    'TBI', 'void', 'null',
    'tup', 'struct', 'frame',
    'litint', 'litnum', 'littxt', 'litsym', 'litsyms', 'litdate', 'litframe', 'littup', 'litstruct',
    'T', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9',
    '_tv', '_tvfunc',
    'btype', 'pytype',
]

from bones.core.sentinels import Null, Void, Missing
from bones.ts.metatypes import BTAtom, BType, extractConstructors, BTFn, BTTuple
from bones.ts.select import TBI, _tvfunc, btype, pytype



# **********************************************************************************************************************
# general purpose tv structure boxing both type and value
# **********************************************************************************************************************

class _tv:
    __slots__ = ['_t', '_v', '_hash']
    def __new__(cls, *args_, **kwargs_):
        constr, args, kwargs = extractConstructors(args_, kwargs_)
        if constr:
            assert isinstance(constr, (BType, type))
            instance = super(cls, cls).__new__(cls)
            instance._t = constr
            instance._v = args[0]
            instance._hash = Missing
            return instance
        else:
            if len(args) == 2:
                t, v = args
                assert isinstance(t, (BType, type))
                instance = super(cls, cls).__new__(cls)
                instance._t = t
                instance._v = args[1]
                instance._hash = Missing
                return instance
            else:
                raise SyntaxError(f'_tv(...) must be of form _tv(type, value) or _tv(BType, value)')
    def _asT(self, _t):
        return _tv(_t, self._v)
    def __repr__(self):
        return f'tv({self._t},{self._v})'
    def __str__(self):
        return f'<{self._t}:{self._v}>'
    def __eq__(self, other):
        if not hasattr(other, '_tv'):
            return False
        else:
            return (self._t == other._t) and (self._v == other._v)
    def __hash__(self):
        # tv will be hashable if it's type and value are hashable
        if self._hash is Missing:
            self._hash = hash((self._t, self._v))
        return self._hash



# **********************************************************************************************************************
# bones langauge types and structures
# **********************************************************************************************************************

mem = BType('mem')                      # the memory space - defined in jones

noun = BTAtom("noun")
nullary = BTAtom("nullary")
unary = BTAtom("unary")
binary = BTAtom("binary")
ternary = BTAtom("ternary")

void = BTAtom('void', space=mem)        # something that isn't there and shouldn't be there
null = BTAtom('null')                   # the null set - something that isn't there and that's okay
missing = BTAtom('missing')             # something that isn't there but should be - considered an error

Null._t = null
Void._t = void

# bones allows for literal frames, tuples and structs and since we would like to have multiple implementations, for
# example pandas and polars etc, and additionally we can't currently express T1(bstr), T1(btup), etc so we need root
# types to derive from:
agg = BTAtom('agg')                             # conceptually this is nice however not sure how much value it adds given it implies multiple spaces
tup = BType('tup: tup & agg in agg')            # slots are accessed by index only
struct = BType('struct: struct & agg in agg')   # slots are accessed by name (symbol) or index
rec = BType('rec: rec & agg in agg')            # slots are accessed by name (symbol) only, no index access
frame = BType('frame: frame & agg in agg')      # cols are accessed by name (symbol), rows are accessed by index

cstruct = BType('cstruct: cstruct & struct in mem')     # will be laid out in memory using C struct rules


# the following are supplied unboxed for performance reasons

class _litint(int):
    def __new__(cls, *args_, **kwargs_):
        constr, args, kwargs = extractConstructors(args_, kwargs_)
        if len(args) == 1:
            assert constr == litint
            return super(cls, cls).__new__(cls, args[0])
        elif len(args) == 2:
            t, v = args
            assert t == litint
            return super(cls, cls).__new__(cls, v)
        else:
            raise SyntaxError(f'Expected 1 argument, got {len(args)}')
    @property
    def _t(self):
        return litint
    def _v(self):
        return self
    def __repr__(self):
        return f'litint({super().__repr__()})'
litint = BType('litint: atom in mem').setConstructor(_litint).setCoercer(_litint)


class _litnum(float):
    def __new__(cls, *args_, **kwargs_):
        constr, args, kwargs = extractConstructors(args_, kwargs_)
        if len(args) == 1:
            assert constr == litnum
            return super(cls, cls).__new__(cls, args[0])
        else:
            raise SyntaxError(f'Expected 1 argument, got {len(args)}')
    @property
    def _t(self):
        return litnum
    def _v(self):
        return self
    def __repr__(self):
        return f'litnum({super().__repr__()})'
litnum = BType('litnum: atom in mem').setConstructor(_litnum)


class _littxt(str):
    def __new__(cls, *args_, **kwargs_):
        constr, args, kwargs = extractConstructors(args_, kwargs_)
        if len(args) == 1:
            return super(cls, cls).__new__(cls, args[0])
        elif len(args) == 2:
            t, v = args
            assert t == littxt
            return super(cls, cls).__new__(cls, v)
        else:
            raise SyntaxError(f'No args passed')
    @property
    def _t(self):
        return littxt
    @property
    def _v(self):
        return self
    def __repr__(self):
        return f'littxt({super().__repr__()})'
littxt = BType('littxt: atom in mem').setConstructor(_littxt)


# parser / kenrel need to be able to construct litsym and litsyms - Jones's sym is a struct not a tv

def _litsymCons(cls, *args, **kwargs):
    # OPEN: handle str / txt to sym conversion
    if len(args) == 1:
        return _tv(litsym, args[0])
    elif len(args) == 2:
        t, v = args
        assert t == litsym
        return _tv(litsym, v)
    else:
        raise SyntaxError(f'No args passed')
litsym = BTAtom('litsym', space=mem).setConstructor(_litsymCons)
litsyms = BTAtom('litsyms', space=mem)   # OPEN: needs constructor


# the structures for littup, litstruct and litframe are provided by libraries to be constructed by the kernel
littup = BType('littup: littup & tup in mem')
litstruct = BType('litstruct: litstruct & struct in mem')
litframe = BType('litframe: litframe & frame in mem')
litdate = BTAtom('litdate', space=mem)

# OPEN: need litdatetime, litcitydatetime etc


__all__ += [
    'btype'
]


T = BType('T')
for i in range(1, 10):
    t = BType(f'T{i}')
    locals()[t.name] = t
