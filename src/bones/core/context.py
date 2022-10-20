# **********************************************************************************************************************
#
#                             Copyright (c) 2019-2022 David Briant. All rights reserved.
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
from contextlib import contextmanager as _contextmanager
from bones.core.sentinels import Missing
from bones.core.errors import ProgrammerError

if not hasattr(sys, '_ContextStack'):
    sys._ContextStack = {}



# **********************************************************************************************************************
# context
# **********************************************************************************************************************

class _Context(object):

    def __call__(self, *args, **kwargs):
        if args:
            if len(args) > 1: raise ProgrammerError(f'Can only get one context value at a time, but {args} was requested')
            # get context

        else:
            return _setContext(**kwargs)

    def __getattr__(self, name):
        return sys._ContextStack.get(name, [Missing])[-1]

    def __setattr__(self, name, value):
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