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

from bones.core.sentinels import Missing
from bones.lang.metatypes import BType
from bones.lang.utils import Constructors

class tv(object):
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

