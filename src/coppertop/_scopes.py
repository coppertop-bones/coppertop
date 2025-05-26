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

import copy
from ctypes import c_long
from bones.core.errors import ProgrammerError, NotYetImplemented
from bones.core.sentinels import Missing

_from_address = c_long.from_address
_numCopies = 0
_numNotCopied = 0


ANON_NAME = "<anon>"
ROOT_NAME = "<root>"


# **********************************************************************************************************************
# _CoWScope - copy on write - https://stackoverflow.com/questions/628938/what-is-copy-on-write
# **********************************************************************************************************************

def _targetCount(p):
    return c_long.from_address(p._targetId).value

class _CoWProxy:
    __slots__ = ['_parentProxy', '_k', '_target', '_targetId']

    def __init__(self, parentProxy, k, target):
        super().__setattr__('_parentProxy', parentProxy)
        super().__setattr__('_k', k)
        super().__setattr__('_target', target)
        super().__setattr__('_targetId', id(target))

    def _copyIfNeeded(self, eId):
        _targetId = super().__getattribute__('_targetId')
        if eId == _targetId:
            raise ValueError('Cycle to parent detected - needs a better error message')
        parentProxy = super().__getattribute__('_parentProxy')
        if isinstance(parentProxy, _CoWProxy):
            parentProxy._copyIfNeeded(eId)
        if _from_address(_targetId).value > 2:  # 1 plus 1 for the proxy
            targetRefCount = _from_address(_targetId).value
            # newTarget = copy.copy(super().__getattribute__('_target'))
            super().__setattr__('_target', copy.copy(super().__getattribute__('_target')))
            newTargetId = id(super().__getattribute__('_target'))
            super().__setattr__('_targetId', newTargetId)
            newTargetRefCount = _from_address(newTargetId).value
            parentProxy._target[super().__getattribute__('_k')] = super().__getattribute__('_target')
            newTargetRefCount2 = _from_address(newTargetId).value
            global _numCopies
            _numCopies += 1
        else:
            global _numNotCopied
            _numNotCopied += 1

    def __delitem__(self, k):  # del _.fred[1]    k = 1, target is the indexable fred
        super().__getattribute__('_copyIfNeeded')(0)
        del super().__getattribute__('_target')[k]

    def __getitem__(self, k):  # _.fred[1]      k = 1, target is the indexable fred
        _target = super().__getattribute__('_target')
        # answer a new proxy every time (rather than answering an already created proxy) so ref count keeps going up
        # if the caller holds on to it just like a normal python object
        return _CoWProxy(self, k, _target[k])

    def __iter__(self):
        return super().__getattribute__('_target').__iter__()

    def __next__(self):
        return super().__getattribute__('_target').__next__()

    def __setitem__(self, k, newTarget):  # _.fred[1] = x      k = 1, target is the indexable fred
        newTarget = newTarget._target if isinstance(newTarget, _CoWProxy) else newTarget
        super().__getattribute__('_copyIfNeeded')(id(newTarget))
        super().__getattribute__('_target')[k] = newTarget   # target has not changed just the element the target contains

    def __getattribute__(self, k):
        # if context('print'):
        #     print(k)
        if k in ('_target', '_copyIfNeeded', '_targetId', '_parentProxy', '__len__', '_nRefs', '_setAttr', '_setItem'):
            return super().__getattribute__(k)
        elif k == '_t':
            return super().__getattribute__('_target')._t
        else:
            # _target = super().__getattribute__('_target')
            if isinstance(super().__getattribute__('_target'), list):
                if k in ('clear', 'extend', 'pop', 'remove', 'insert', 'reverse'):
                    raise ProgrammerError(f'list>>{k} is disabled for _CoWScope')
                elif k in ('append', 'sort'):
                    # _target = None
                    super().__getattribute__('_copyIfNeeded')(0)        # could append a parent!!! TODO fix
                    # if a copy was needed then _target has changed so get it again
                    return getattr(super().__getattribute__('_target'), k)
                else:
                    # __contains__, __iter__, __add__, __mul__, __reversed__, copy, count, index
                    return super().__getattribute__('_target').__getattribute__(k)
            if isinstance(super().__getattribute__('_target'), dict):
                if k in ('clear', 'pop', 'popitem', 'update'):
                    raise ProgrammerError(f'dict>>{k} is disabled for _CoWScope')
                elif k in ('setdefault'):
                    raise NotYetImplemented()
                    # _target = None
                    super().__getattribute__('_copyIfNeeded')(0)  # could append a parent!!! TODO fix
                    # if a copy was needed then _target has changed so get it again
                    return getattr(super().__getattribute__('_target'), k)
                else:
                    # __contains__, __iter__, __reversed__, __ror__, fromkeys, get, items, keys, values
                    return super().__getattribute__('_target').__getattribute__(k)
            return _CoWProxy(self, k, super().__getattribute__('_target').__getattribute__(k))

    def __setattr__(self, k, newElement):    # _.fred.name = x      _target=fred, k=name, newElement=x
        super().__getattribute__('_copyIfNeeded')(newElement._targetId if isinstance(newElement, _CoWProxy) else id(newElement))
        setattr(super().__getattribute__('_target'), k, newElement)  # target has not changed just the element the target contains

    def __str__(self):
        return super().__getattribute__('_target').__str__()

    def __repr__(self):
        return f"[{super().__getattribute__('_k')}]{{{super().__getattribute__('_target').__repr__()}}}"

    def __len__(self):
        return super().__getattribute__('_target').__len__()

    def __bool__(self):
        _target = super().__getattribute__('_target')
        if hasattr(_target, '__bool__'):
            return _target.__bool__()
        else:
            return _target.__len__() > 0

    def __call__(self, *args, **kwargs):
        return super().__getattribute__('_target')(*args, **kwargs)

    def __add__(self, rhs):
        return super().__getattribute__('_target') + rhs

    def __radd__(self, lhs):
        return lhs + super().__getattribute__('_target')

    def __sub__(self, rhs):
        return super().__getattribute__('_target') - rhs

    def __rsub__(self, lhs):
        return lhs - super().__getattribute__('_target')

    def __mul__(self, rhs):
        return super().__getattribute__('_target') * rhs

    def __rmul__(self, lhs):
        return lhs - super().__getattribute__('_target')

    def __truediv__(self, rhs):
        return super().__getattribute__('_target') / rhs

    # def __rdiv__(self, lhs):
    #     return lhs / super().__getattribute__('_target')

    def __rtruediv__(self, lhs):
        return lhs / super().__getattribute__('_target')

    def __iadd__(self, rhs):          # _.fred.age += rhs       _target=age, k=age
        oldTarget = super().__getattribute__('_target')
        newTarget = oldTarget + rhs
        newtargetId = id(newTarget)
        assert not isinstance(newTarget, _CoWProxy)  # unlikely but just in case
        # self won't need to check for copies as we have a new target, so start with parent
        _parentProxy = super().__getattribute__('_parentProxy')
        if isinstance(_parentProxy, _CoWProxy):
            _parentProxy._copyIfNeeded(newtargetId)
        k = super().__getattribute__('_k')
        _parentProxy._setAttr(k, newTarget)
        return newTarget        #__iadd__ must return the new value

    def __imul__(self, rhs):        # self *= rhs
        raise NotYetImplemented()

    def __eq__(self, rhs):          # self == rhs
        return super().__getattribute__('_target') == (rhs._target if isinstance(rhs, _CoWProxy) else rhs)

    def _nRefs(self):
        return _from_address(super().__getattribute__('_targetId')).value

    def _setAttr(self, k, v):
        setattr(super().__getattribute__('_target'), k, v)

    def _setItem(self, k, v):
        super().__getattribute__('_target')[k] = v


# to decrease any ref count object deletion must be detected thus we need to create an object on access - this is
# the cost of the optimisation in Python

class _CoWScope:
    _slots__ = ['_vars', '_name']

    def __init__(self):
        super().__setattr__('_vars', {})

    def __getattribute__(self, k):      # _.fred or
        if k == '_target': # _._target
            return super().__getattribute__('_vars')
        if k in ('__class__', '__module__', '_setAttr'):
            return super().__getattribute__(k)
        _vars = super().__getattribute__('_vars')
        if k in _vars: # _.fred
            # answer a new proxy every time so ref count goes up
            return _CoWProxy(self, k, _vars[k])
        else:
            raise AttributeError(k)

    def __setattr__(self, k, newValue):
        if isinstance(newValue, _CoWProxy):
            newValue = newValue._target
        super().__getattribute__('_vars')[k] = newValue

    def __delattr__(self, k):
        vars = super().__getattribute__('_vars')
        if k in vars:
            del vars[k]
            return
        raise AttributeError(k)

    def __repr__(self):
        # for pretty display in pycharm debugger
        return f"TBC{{{','.join(super().__getattribute__('_vars'))}}}"

    def __dir__(self):
        return list(super().__getattribute__('_vars').keys())

    def _setAttr(self, k, v):
        super().__getattribute__('_vars')[k] = v



class _ContextualScopeManager:
    __slots__ = ['_current', '_namedScopes']

    def __init__(self):
        super().__setattr__('_namedScopes', {})
        super().__setattr__('_current', _MutableContextualScope(self, Missing, ROOT_NAME))

    def __setattr__(self, k, newValue):
        if k == '_current':
            super().__setattr__('_current', newValue)
        else:
            setattr(super().__getattribute__('_current'), k, newValue)

    def __getattribute__(self, k):
        if k in ('_current', '_namedScopes'):
            return super().__getattribute__(k)
        else:
            return getattr(super().__getattribute__('_current'), k)

    def __delattr__(self, k):
        if k in ('_current', '_namedScopes'):
            raise AttributeError("Can't delete _current or _namedScopes")
        else:
            return delattr(super().__getattribute__('_current'), k)

    def __repr__(self):
        # for pretty display in pycharm debugger
        return f"TBC{{{','.join(self._current._vars)}}}"

    def __dir__(self):
        return dir(super().__getattribute__('_current'))



class _MutableContextualScope:
    _slots__ = ['_vars', '_parent', '_manager', '_name']

    def __init__(self, manager, parent, name=Missing):
        super().__setattr__('_vars', {})
        super().__setattr__('_manager', manager)
        super().__setattr__('_name', name)
        if parent == Missing:
            parent = self   # to prevent loosing the root contextual scope
        if name is not Missing:
            manager._namedScopes[name] = self
        super().__setattr__('_parent', parent)

    def __setattr__(self, k, newValue):
        super().__getattribute__('_vars')[k] = newValue

    def __getattribute__(self, k):
        if k in ('_parent', '_manager', '_vars', '_name'):
            return super().__getattribute__(k)
        if (answer := super().__getattribute__('_vars').get(k, Missing)) is Missing:    # numpy overides pythons truth function in an odd way
            raise AttributeError(k)
        else:
            return answer

    def __delattr__(self, k):
        vars = super().__getattribute__('_vars')
        if k in vars:
            del vars[k]
            return
        raise AttributeError(k)

    def __repr__(self):
        return f'ContextualScope({ANON_NAME if self._name is Missing else self._name})'

    def __dir__(self):
        return list(super().__getattribute__('_vars').keys())



if not hasattr(sys, '_UNDERSCORE'):
    sys._UNDERSCORE = _ContextualScopeManager()     # kept on sys so its identity isn't changed on reload (as happens in Jupyter)

_UNDERSCORE = sys._UNDERSCORE



if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__ + ' - done')
