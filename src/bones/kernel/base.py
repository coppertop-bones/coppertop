# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

from bones.core.sentinels import Missing
from bones.lang.types import unary

# keep the contexts on the kernel to relieve the burden of type memory management from the storage manager

class BaseKernel:
    __slots__ = ['ctxs', 'sm', 'modByPath', 'styleByName']
    def __init__(self, sm):
        self.ctxs = {}
        self.sm = sm
        self.modByPath = {}
        self.styleByName = {}

    def styleForName(self, name):
        return self.styleByName.get(name, unary)


kernelForCoppertop = BaseKernel(Missing)
