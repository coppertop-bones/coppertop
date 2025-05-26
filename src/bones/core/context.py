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

from contextlib import contextmanager as _contextmanager
from bones.core.sentinels import Missing
from bones.core.errors import ProgrammerError

if not hasattr(sys, '_ContextStack'):
    sys._ContextStack = {}



# **********************************************************************************************************************
# context
# **********************************************************************************************************************

class _Context:

    def __call__(self, *args, **kwargs):
        if args and len(args) > 1: raise ProgrammerError(f'Can only get one context value at a time, but {args} was requested')
        return _setContext(**kwargs)

    def __getattr__(self, name):
        return sys._ContextStack.get(name, [Missing])[-1]

    def __setattr__(self, name, value):
        # if there is no context for the name, i.e.  established via with `context(name=val):`, then this have no effect
        sys._ContextStack.get(name, [Missing])[-1] = value


@_contextmanager
def _setContext(*args, **kwargs):
    # push context
    for k, v in kwargs.items():
        sys._ContextStack.setdefault(k, []).append(v)
    answer = None
    try:
        yield answer
    finally:
        # pop context, deleting if empty
        for k in kwargs.keys():
            sys._ContextStack[k] = sys._ContextStack[k][:-1]
            if len(sys._ContextStack[k]) == 0:
                del sys._ContextStack[k]

context = _Context()

def _PP(x):
    print(str(x))
    return x

def _EE(x):
    print(str(x), file = sys.stderr)
    return x

sys._ContextStack.setdefault('PP', []).append(_PP)
sys._ContextStack.setdefault('NB', []).append(_EE)
sys._ContextStack.setdefault('EE', []).append(_EE)

if __name__ == '__main__':
    with context(fred=1):
        assert context.fred == 1
        context.fred += 1
        assert context.fred == 2
    assert context.fred is Missing
    print('pass')
