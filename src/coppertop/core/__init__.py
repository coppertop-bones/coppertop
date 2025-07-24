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

from coppertop.core._context import context
from coppertop.core._sentinels import Missing, Null, Err, Void, EarlyExit
from coppertop.core._errors import (ProgrammerError, CPTBError, NotYetImplemented, PathNotTested, UnhappyWomble, WTF,
    ErrSite, handlersByErrSiteId)
from coppertop.core._utils import raiseLess, assertIs, firstValue, firstKey, HookStdOutErrToLines

ellipsis = type(...)
dict_keys = type({}.keys())
dict_values = type({}.values())
dict_items = type({}.items())
# function = type(lambda x:x)
int = type(1)
str = type('hello')
bool = type(True)
list_iter = type(iter([]))
generator = type((x for x in []))
