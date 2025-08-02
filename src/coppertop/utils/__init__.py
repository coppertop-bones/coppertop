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

from coppertop._utils.context import context
from coppertop._utils.sentinels import Missing, Null, Err, Void, EarlyExit
from coppertop._utils.errors import ProgrammerError, CPTBError, NotYetImplemented, PathNotTested, UnhappyWomble, WTF, \
    ErrSite, handlersByErrSiteId, raiseLess, ImpossiblePathError
from coppertop._utils.testing import assertIs, assertRaises
