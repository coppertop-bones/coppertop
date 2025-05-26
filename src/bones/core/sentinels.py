# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

import sys, types, typing

if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)



__all__ = ['Missing', 'Null', 'Void', 'Err', 'EarlyExit']


def _ensureSentinels():
    # These are kept on sys so their identity isn't changed on module reload (a frequent occurrence in Jupyter)


    # error sentinels - cf missing, null, nan in databases

    # something should / could be there but it is definitely not there
    if not hasattr(sys, '_Missing'):
        # OPEN: add a metaclass
        class Missing:
            def __bool__(self):
                return False
            def __repr__(self):
                # for pretty display in pycharm debugger
                return 'Missing'
            def __or__(self, other):
                # see https://peps.python.org/pep-0604/
                if (
                        isinstance(other, type) or
                        (t := typing.get_origin(other) is typing.Union) or
                        t is types.UnionType
                ):
                    return typing.Union[type(self), other]
                else:
                    return NotImplemented
            def __ror__(self, other):
                # see https://peps.python.org/pep-0604/
                if (
                        isinstance(other, type) or
                        (t := typing.get_origin(other) is typing.Union) or
                        t is types.UnionType
                ):
                    return typing.Union[type(self), other]
                else:
                    return NotImplemented
        sys._Missing = Missing()
        sys._Missing._t = sys._Missing


    # the null set
    if not hasattr(sys, '_NULL'):
        class _NULL:
            def __bool__(self):
                return False
            def __repr__(self):
                # for pretty display in pycharm debugger
                return 'Null'
        sys._NULL = _NULL()
        sys._NULL._t = sys._Missing

    # OPEN: consider if Err the general error sentinel of type err is ever needed? i.e. return an Err without
    # explaining what it is? at min it's not hard to do "There's an emergency going on" | +err >> signal
    # possibly in prototype code you could do Err >> signal, but why not Null | +err >> signal
    if not hasattr(sys, '_ERR'):
        class _ERR:
            def __repr__(self):
                # for pretty display in pycharm debugger
                return 'Err'
        sys._ERR = _ERR()
        sys._ERR._t = sys._Missing

    # VOID - the uninitialised variable state - in general this is
    # undetectable and has no place in code - just as part of the
    # building process
    if not hasattr(sys, '_VOID'):
        class _VOID:
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
        class EarlyExit:
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
generator = type((x for x in []))


if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__ + ' - done')
