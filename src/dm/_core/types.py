# **********************************************************************************************************************
#
#                             Copyright (c) 2021-2022 David Briant. All rights reserved.
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

# a collection of usual types that aren't essential to the language
# in bones types can have constructors associated with them - so we have some classes embedded in the types module
# more for convenience and ease of understanding the module structure rather than anything deeper


import sys, builtins
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

from bones.core.sentinels import Missing
from bones.lang.metatypes import BTAtom, BType, weaken
from bones.lang.types import *
import bones.lang.types
from bones.lang.structs import tvarray, tv
from bones.lang.utils import Constructors


__all__ = bones.lang.types.__all__


i8 = BTAtom.define('i8').setOrthogonal(obj)
u8 = BTAtom.define('u8').setOrthogonal(obj)
i16 = BTAtom.define('i16').setOrthogonal(obj)
u16 = BTAtom.define('u16').setOrthogonal(obj)
i32 = BTAtom.define('i32').setOrthogonal(obj)
u32 = BTAtom.define('u32').setOrthogonal(obj)
i64 = BTAtom.define('i64').setOrthogonal(obj)
u64 = BTAtom.define('u64').setOrthogonal(obj)
f32 = BTAtom.define('f32').setOrthogonal(obj)
f64 = BTAtom.define('f64').setOrthogonal(obj)

__all__ += [
    'i8', 'u8', 'i16', 'u16', 'i32', 'u32', 'i64', 'u64', 'f32', 'f64',
]



# litbool is parsed in the SM to a storage format of a python bool and on assignment is notionally weakened to a
# bool - in reality we just equate bool and python bool
def _makeBool(t, v):
    return builtins.bool(v)
bool = BTAtom.define('bool').setOrthogonal(obj).setCoercer(_makeBool).setConstructor(_makeBool)
__all__ += ['bool']



# **********************************************************************************************************************
# classes for the underlying storage of floats - for num _t is hard-coded to avoid boxing
# **********************************************************************************************************************

# litfloat is parsed in the SM to a storage format of a python float and on assignment is notionally weakened to
# a num - in reality we just equate num and python float
class num_(float):
    def __new__(cls, t, v, *args, **kwargs):
        return super(cls, cls).__new__(cls, v)

    @property
    def _t(self):
        return num

    def _v(self):
        return self

    def __repr__(self):
        return f'n{super().__repr__()}'
num = f64['num'].setCoercer(num_)        # f64 is already orthogonal
__all__ += ['num']


class tvfloat(float):
    def __new__(cls, t, v, *args, **kwargs):
        instance = super(cls, cls).__new__(cls, v)
        instance._t_ = t
        return instance
    @property
    def _v(self):
        return super().__new__(float, self)
    @property
    def _t(self):
        return self._t_
    def __repr__(self):
        return f'{self._t}{super().__repr__()}'
    def _asT(self, t):
        self._t_ = t
        return self
__all__ += ['tvfloat']



# **********************************************************************************************************************
# classes for the underlying storage of integers - for index, count and offset _t is hard-coded to avoid boxing
# **********************************************************************************************************************

class ptr_(int):
    def __new__(cls, t, v, *args, **kwargs):
        return super(cls, cls).__new__(cls, v)
    @property
    def _t(self):
        return ptr
    @property
    def _v(self):
        return self
    def __repr__(self):
        return f'*{self:012x}'          # could add hidden flag later on
ptr = u64['ptr'].setCoercer(ptr_)
__all__ += ['ptr']


# litint is parsed in the SM to a storage format of a python int and on assignment is notionally weakened to an
# index - in reality we just equate num and python float
class index_(int):
    # 1 based
    def __new__(cls, t, v, *args, **kwargs):
        return super(cls, cls).__new__(cls, v)
    @property
    def _t(self):
        return index
    def _v(self):
        return self
    def __repr__(self):
        return f'i{super().__repr__()}'
index = i64['index'].setCoercer(index_)         # i64 is already orthogonal
__all__ += ['index']


for o in range(26):
    locals()['I'+chr(ord('a')+o)] = index
__all__ += [
    'Ia', 'Ib', 'Ic', 'Id', 'Ie', 'If', 'Ig', 'Ih', 'Ii', 'Ij', 'Ik', 'Il', 'Im',
    'In', 'Io', 'Ip', 'Iq', 'Ir', 'Is', 'It', 'Iu', 'Iv', 'Iw', 'Ix', 'Iy', 'Iz'
]


N = BType('N')
for i in range(1, 11):
    t = N.ensure(BType(f'{i}'))
    locals()[t.name] = t
for o in range(26):
    t = N.ensure(BType(chr(ord('a')+o)))
    locals()[t.name] = t
__all__ += [
    'N',
    'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', 'N10',
    'Na', 'Nb', 'Nc', 'Nd', 'Ne', 'Nf', 'Ng', 'Nh', 'Ni', 'Nj', 'Nk', 'Nl', 'Nm',
    'Nn', 'No', 'Np', 'Nq', 'Nr', 'Ns', 'Nt', 'Nu', 'Nv', 'Nw', 'Nx', 'Ny', 'Nz'
]


class count_(int):
    # tv representing counts, natural numbers starting at 0
    def __new__(cls, t, v, *args, **kwargs):
        return super(cls, cls).__new__(cls, v)
    # def __add__(self, other):
    #     return NotImplemented
    # def __sub__(self, other):
    #     return NotImplemented
    # def __mul__(self, other):
    #     return NotImplemented
    # def __div__(self, other):
    #     return NotImplemented
    @property
    def _t(self):
        return count
    @property
    def _v(self):
        return self
    def __repr__(self):
        return f'c{super().__repr__()}'
count = i64['count'].setCoercer(count_)
__all__ += ['count']


class offset_(int):
    # (0 based)
    def __new__(cls, t, v, *args, **kwargs):
        return super(cls, cls).__new__(cls, v)
    @property
    def _t(self):
        return offset
    def _v(self):
        return self
    def __repr__(self):
        return f'o{super().__repr__()}'
offset = i64['offset'].setCoercer(offset_)
__all__ += ['offset']
for o in range(26):
    locals()['O'+chr(ord('a')+o)] = offset
__all__ += [
    'Oa', 'Ob', 'Oc', 'Od', 'Oe', 'Of', 'Og', 'Oh', 'Oi', 'Oj', 'Ok', 'Ol', 'Om',
    'On', 'Oo', 'Op', 'Oq', 'Or', 'Os', 'Ot', 'Ou', 'Ov', 'Ow', 'Ox', 'Oy', 'Oz'
]


class tvint(int):
    def __new__(cls, t, v, *args, **kwargs):
        instance = super(cls, cls).__new__(cls, v)
        instance._t_ = t
        return instance
    @property
    def _v(self):
        return super().__new__(int, self)
    @property
    def _t(self):
        return self._t_
    def __repr__(self):
        return f'{self._t}{super().__repr__()}'
    def _asT(self, t):
        self._t_ = t
        return self
__all__ += ['tvint']



# **********************************************************************************************************************
# classes for the underlying storage of text - for index, count and offset _t is hard-coded to avoid boxing
# **********************************************************************************************************************

# littxt is a python str and on assignment is notionally weakened to a txt - in reality we just equate
# txt and python str
class str_(builtins.str):
    def __new__(cls, t, v, *args, **kwargs):
        return super(cls, cls).__new__(cls, v)
    @property
    def _t(self):
        return txt
    def _v(self):
        return self
    def __repr__(self):
        return f'{super().__repr__()}'
txt = BTAtom.define('txt').setOrthogonal(obj).setCoercer(str_).setConstructor(str_)


class tvstr(builtins.str):

    def __new__(cls, t, v, *args, **kwargs):
        t, v = 1, 2
        instance = super(cls, cls).__new__(cls, v)
        instance._t_ = t
        return instance

    @property
    def _v(self):
        return super().__new__(float, self)

    @property
    def _t(self):
        return self._t_

    def __repr__(self):
        return f'{self._t}{super().__repr__()}'

    def _asT(self, t):
        self._t_ = t
        return self

__all__ += ['txt', 'tvstr']



# **********************************************************************************************************************
# classes for the underlying storage of dates
# **********************************************************************************************************************

# litdate is parsed in the SM to a storage format of a python datetime.date and on assignment is notionally weakened
# to a date - in reality we just equate rub date and python datetime.date
date = BTAtom.define('date').setOrthogonal(obj)

__all__ += ['date']



# **********************************************************************************************************************
# types for dealing with python - not needed in a non-python implementation
# **********************************************************************************************************************

py = BTAtom.ensure("py").setOrthogonal(obj)

pylist = py['pylist']
pytuple = py['pytuple']
pydict = py['pydict']
pyset = py['pyset']
npfloat = py['npfloat']
pydict_keys = py['pydict_keys']
pydict_values = py['pydict_values']
pydict_items = py['pydict_items']
pyfunc = py['pyfunc']


__all__ += [
    'py', 'pylist', 'pytuple', 'pydict', 'pyset', 'npfloat', 'pydict_keys', 'pydict_values', 'pydict_items', 'pyfunc',
    'matrix', 'vec'
]



# **********************************************************************************************************************
# other
# **********************************************************************************************************************


err = BTAtom.define('err')             # an error code of some sort
missing = BTAtom.define('missing')     # something that isn't there and should be there

sys._Missing._t = missing
sys._ERR._t = err


__all__ += [
    'err', 'missing', 'null', 'void',
]


# **********************************************************************************************************************
# vec and matrix
# **********************************************************************************************************************

vec = (N**num)['vec']                   # N**num is common so vec is (N**num)&_vec
matrix = (N**N**num)['matrix']          # ditto - (N**N**num)&_matrix


def create1DTvArray(*args_, **kwargs):
    constr, args = (args_[0][0], args_[1:]) if args_ and isinstance(args_[0], Constructors) else (Missing, args_)
    if len(args) == 1:
        t, x = constr, args[0]
    else:
        t, x = args
    answer = tvarray(t, x)
    ndims = len(answer.shape)
    if ndims == 0:
        answer.shape = (1, )
    elif ndims == 2:
        if answer.shape[0] == 1:
            answer.shape = answer.shape[1]
        elif answer.shape[1] == 1:
            answer.shape = answer.shape[0]
        else:
            raise TypeError(f'Can\' coerce shape {answer.shape} to 1D')
    elif ndims > 2:
        raise TypeError('x has more than 2 dimensions')
    return answer | t

def create2DTvArray(*args_, **kwargs):
    constr, args = (args_[0][0], args_[1:]) if args_ and isinstance(args_[0], Constructors) else (Missing, args_)
    if len(args) == 1:
        t, x = constr, args[0]
    else:
        t, x = args
    answer = tvarray(t, x)
    ndims = len(answer.shape)
    if ndims == 0:
        answer.shape = (1, 1)
    elif ndims == 1:
        answer.shape = (answer.shape[0], 1)
    elif ndims > 2:
        raise TypeError('x has more than 2 dimensions')
    return answer | t

((N**num)&tvarray).setConstructor(create1DTvArray)
(vec&tvarray).setConstructor(create1DTvArray)
(matrix&tvarray).setConstructor(create2DTvArray)



# could make +, -, / and * be type aware by having index, offset, count, etc being familial as well as orthogonal

weaken(litint, (index, num, offset, count))
weaken(litdec, (num,))
weaken(type(None), (null, void))
weaken(littxt, (txt,))

class thing(object): pass
t = thing()     # t for types in anticipation of BType namespacing and import coppertop.bones_types as t
t.count = count
t.index = index
t.offset = offset

if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__ + ' - done')
