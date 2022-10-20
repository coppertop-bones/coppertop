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

import sys, inspect
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)



__all__ = ['Missing', 'Null', 'Void', 'Err', 'EarlyExit']


def _ensureSentinels():
    # These are kept on sys so their identity isn't changed on module reload (a frequent occurrence in Jupyter)


    # error sentinels - cf missing, null, nan in databases

    # something should / could be there but it is definitely not there
    if not hasattr(sys, '_Missing'):
        class Missing(object):
            def __bool__(self):
                return False
            def __repr__(self):
                # for pretty display in pycharm debugger
                return 'Missing'
        sys._Missing = Missing()
        sys._Missing._t = sys._Missing


    # the null set
    if not hasattr(sys, '_NULL'):
        class _NULL(object):
            def __repr__(self):
                # for pretty display in pycharm debugger
                return 'Null'
        sys._NULL = _NULL()
        sys._NULL._t = sys._Missing

    # OPEN: consider if Err the general error sentinel of type err is ever needed? i.e. return an Err without
    # explaining what it is? at min it's not hard to do "There's an emergency going on" | +err >> signal
    # possibly in prototype code you could do Err >> signal, but why not Null | +err >> signal
    if not hasattr(sys, '_ERR'):
        class _ERR(object):
            def __repr__(self):
                # for pretty display in pycharm debugger
                return 'Err'
        sys._ERR = _ERR()
        sys._ERR._t = sys._Missing

    # VOID - the uninitialised variable state - in general this is
    # undetectable and has no place in code - just as part of the
    # building process
    if not hasattr(sys, '_VOID'):
        class _VOID(object):
            def __bool__(self):
                return False
            def __repr__(self):
                # for pretty display in pycharm debugger
                return 'Void'
        sys._VOID = _VOID()
        sys._VOID._t = sys._Missing

    # not a - e.g. not a number, not a date, etc #NA!, #NUM!, #VALUE!
    # np.log(0)  => -inf, #np.log(-1)  => nan, tbd


    # Just to indicate we are exiting early rather than ensuring if statements are fully complete
    if not hasattr(sys, '_ExitEarly'):
        class EarlyExit(object):
            def __bool__(self):
                return False
            def __repr__(self):
                # for pretty display in pycharm debugger
                return 'EarlyExit'
        sys._ExitEarly = EarlyExit()
        sys._ExitEarly._t = sys._ExitEarly


_ensureSentinels()
Missing = sys._Missing
Null = sys._NULL
Err = sys._ERR
Void = sys._VOID
EarlyExit = sys._ExitEarly

ellipsis = type(...)
dict_keys = type({}.keys())
dict_values = type({}.values())
dict_items = type({}.items())
function = type(lambda x:x)
int = type(1)
str = type("hello")
bool = type(True)
classType = type(object)
list_iter = type(iter([]))


if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__ + ' - done')
