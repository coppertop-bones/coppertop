# **********************************************************************************************************************
#
#                             Copyright (c) 2021-2022 David Briant. All rights reserved.
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

from typing import Iterable
import abc

from bones.core.errors import NotYetImplemented
from bones.core.sentinels import Missing
from bones.lang.metatypes import BType
from bones.lang.utils import Constructors


class tv:
    __slots__ = ['_t_', '_v_', '_hash']
    def __init__(self, _t, _v):
        _t = _t[0] if isinstance(_t, Constructors) else _t
        assert isinstance(_t, (BType, type))
        self._t_ = _t
        self._v_ = _v
        self._hash = Missing
    def __setattr__(self, key, value):
        if key in ('_t_', '_v_', '_hash'):
            tv.__dict__[key].__set__(self, value)
        else:
            raise AttributeError()
    @property
    def _t(self):
        return self._t_
    @property
    def _v(self):
        return self._v_
    @property
    def _tv(self):
        return (self._t_, self._v_)
    def _asT(self, _t):
        return tv(_t, self._v)
    def __repr__(self):
        return f'tv({self._t_},{self._v_})'
    def __str__(self):
        return f'<{self._t_}:{self._v_}>'
    def __eq__(self, other):
        if not isinstance(other, tv):
            return False
        else:
            return (self._t_ == other._t_) and (self._v_ == other._v_)
    def __hash__(self):
        # tv will be hashable if it's type and value are hashable
        if self._hash is Missing:
            self._hash = hash((self._t, self._v))
        return self._hash


class tvtuple:
    def __init__(self):
        raise NotYetImplemented


class _tvstruct:
    __slots__ = ['_pub', '_pvt']

    def __init__(self, *args_, **kwargs):
        super().__init__()
        super().__setattr__('_pvt', {})
        super().__setattr__('_pub', {})
        super().__getattribute__('_pvt')['_t'] = type(self)
        super().__getattribute__('_pvt')['_v'] = self

        constr, args = (args_[0][0], args_[1:]) if args_ and isinstance(args_[0], Constructors) else (Missing, args_)
        if len(args) == 0:
            # _tvstruct(), _tvstruct(**kwargs)
            if constr:
                super().__getattribute__('_pvt')['_t'] = constr
            if kwargs:
                super().__getattribute__('_pub').update(kwargs)
        elif len(args) == 1:
            # _tvstruct(_tvstruct), _tvstruct(dictEtc)
            arg1 = args[0]
            if isinstance(arg1, _tvstruct):
                # _tvstruct(_tvstruct)
                super().__getattribute__('_pvt')['_t'] = arg1._t
                super().__getattribute__('_pub').update(arg1._pub)
            elif isinstance(arg1, (dict, list, tuple, zip)):
                # _tvstruct(dictEtc)
                super().__getattribute__('_pub').update(arg1)
                if constr:
                    super().__getattribute__('_pvt')['_t'] = constr
            else:
                # _tvstruct(t), _tvstruct(t, **kwargs)
                super().__getattribute__('_pvt')['_t'] = arg1
                if kwargs:
                    # _tvstruct(t, **kwargs)
                    super().__getattribute__('_pub').update(kwargs)
        elif len(args) == 2:
            # _tvstruct(t, _tvstruct), _tvstruct(t, dictEtc)
            arg1, arg2 = args
            if kwargs:
                # this needs sorting but I don't have time right now
                # came up for `PMF(Brown=30, Yellow=20, Red=20, Green=10, Orange=10, Tan=10)`
                # having two types (PMF and then _tvstruct do the construction so args is (_tvstruct, PMF)
                super().__getattribute__('_pvt')['_t'] = arg2
                super().__getattribute__('_pub').update(kwargs)
                # raise TypeError('No kwargs allowed when 2 args are provided')
                return None
            super().__getattribute__('_pvt')['_t'] = arg1
            if isinstance(arg2, _tvstruct):
                # _tvstruct(t, _tvstruct)
                super().__getattribute__('_pub').update(arg2._pub)
            else:
                # _tvstruct(t, dictEtc)
                super().__getattribute__('_pub').update(arg2)
        else:
            raise TypeError(
                '_tvstruct(...) must be of form _tvstruct(), _tvstruct(**kwargs), _tvstruct(_tvstruct), _tvstruct(dictEtc), ' +
                '_tvstruct(t), _tvstruct(t, **kwargs), _tvstruct(t, _tvstruct), _tvstruct(t, dictEtc), '
            )

    def __asT__(self, t):
        super().__getattribute__('_pvt')['_t'] = t
        return self

    def __copy__(self):
        return _tvstruct(self)

    def __getattribute__(self, f):
        if f[0:2] == '__':
            try:
                answer = super().__getattribute__(f)
            except AttributeError as e:
                answer = super().__getattribute__('_pvt').get(f, Missing)
            if answer is Missing:
                if f in ('__class__', '__len__', '__members__', '__getstate__'):
                    # don't change behaviour
                    raise AttributeError()
            return answer

        if f[0:1] == "_":
            if f == '_pvt': return super().__getattribute__('_pvt')
            if f == '_pub': return super().__getattribute__('_pub')
            if f == '_asT': return super().__getattribute__('__asT__')
            if f == '_t': return super().__getattribute__('_pvt')['_t']
            if f == '_v': return super().__getattribute__('_pvt')['_v']
            # if f == '_asT': return super().__getattribute__('_asT')
            if f == '_keys': return super().__getattribute__('_pub').keys
            if f == '_kvs': return super().__getattribute__('_pub').items
            if f == '_values': return super().__getattribute__('_pub').values
            if f == '_update': return super().__getattribute__('_pub').update
            if f == '_get': return super().__getattribute__('_pub').get
            if f == '_pop': return super().__getattribute__('_pub').pop
            # if names have been added e.g. by self['_10y'] allow access as long as not double entered
            pub = super().__getattribute__('_pub').get(f, Missing)
            pvt = super().__getattribute__('_pvt').get(f, Missing)
            if pub is Missing: return pvt
            if pvt is Missing: return pub
            raise AttributeError(f'public and private entries exist for {f}')
        # print(f)
        # I think we can get away without doing the following
        # if f == 'items':
        #     # for pycharm :(   - pycharm knows we are a subclass of dict so is inspecting us via items
        #     # longer term we may return a BTStruct instead of struct in response to __class__
        #     return {}.items
        v = super().__getattribute__('_pub').get(f, Missing)
        if v is Missing:
            raise AttributeError(f'{f} is Missing')
        else:
            return v

    def __setattr__(self, f, v):
        if f[0:1] == "_":
            if f == '_t_': return super().__getattribute__('_pvt').__setitem__('_t', v)
            # if f in ('_t', '_v', '_pvt', '_pub'): raise AttributeError(f"Can't set {f} on _tvstruct")
            if f in ('_pvt', '_pub'): raise AttributeError(f"Can't set {f} on _tvstruct")
            return super().__getattribute__('_pvt').__setitem__(f, v)
        return super().__getattribute__('_pub').__setitem__(f, v)

    def __getitem__(self, fOrFs):
        if isinstance(fOrFs, (list, tuple)):
            kvs = {f: self[f] for f in fOrFs}
            return _tvstruct(self._t, kvs)
        else:
            return super().__getattribute__('_pub').__getitem__(fOrFs)

    def __setitem__(self, f, v):
        if isinstance(f, str):
            if f[0:1] == "_":
                if f in ('_pvt', '_pub', '_keys', '_kvs', '_values', '_update', '_get'):
                    raise AttributeError(f'name {f} is reserved for use by _tvstruct')
                # if f in super().__getattribute__('_pvt'):
                #     raise AttributeError(f'name {f} is already in pvt use')
        super().__getattribute__('_pub').__setitem__(f, v)

    def __delitem__(self, fOrFs):
        if isinstance(fOrFs, (list, tuple)):
            for f in fOrFs:
                super().__getattribute__('_pub').__delitem__(f)
        else:
            super().__getattribute__('_pub').__delitem__(fOrFs)

    def __contains__(self, f):
        return super().__getattribute__('_pub').__contains__(f)

    def __call__(self, **kwargs):
        # OPEN: do we neeed this?
        _pub = super().__getattribute__('_pub')
        for f, v in kwargs.items():
            _pub.__setitem__(f, v)
        return self

    def __dir__(self) -> Iterable[str]:
        # return super().__getattribute__('_pub').keys()
        return [k for k in super().__getattribute__('_pub').keys() if isinstance(k, str)]

    def __repr__(self):
        _pub = super().__getattribute__('_pub')
        _t = super().__getattribute__('_pvt')['_t']
        itemStrings = (f"{str(k)}={repr(v)}" for k, v in _pub.items())

        if type(_t) is abc.ABCMeta or _t is _tvstruct:
            name = _t.__name__
        else:
            name = str(self._t)
        rep = f'{name}({", ".join(itemStrings)})'
        return rep

    def __len__(self):
        return len(super().__getattribute__('_pub'))

    def __eq__(self, rhs):  # self == rhs
        if isinstance(rhs, dict):
            raise NotYetImplemented()
        elif isinstance(rhs, _tvstruct):
            return self._kvs() == rhs._kvs()
        else:
            return False

    def __iter__(self):
        return iter(super().__getattribute__('_pub').values())

