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


from bones.ts._type_lang.jones_type_manager import BTypeError
from bones.jones import SchemaError


bmtnul = 0      # i.e. not initialised yet
bmtatm = 1      # snuggled in the highest nibble in the type's metadata, i.e. 0x1000_0000

bmtint = 2
bmtuni = 3

bmttup = 4
bmtstr = 5
bmtrec = 6

bmtseq = 7
bmtmap = 8
bmtfnc = 9

bmtsvr = 10


bmtnameById = {
    bmtnul: 'TBC',
    bmtatm: 'Atom',
    bmtint: 'Inter',
    bmtuni: 'Union',
    bmttup: 'Tuple',
    bmtstr: 'Struct',
    bmtrec: 'Rec',
    bmtseq: 'Seq',
    bmtmap: 'Map',
    bmtfnc: 'Fn',
    bmtsvr: 'T',
}


class TLError(Exception): pass

class Constructors(list): pass
