# **********************************************************************************************************************
# Copyright (c) 2025 David Briant. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
# **********************************************************************************************************************

import traceback, sys

from bones.core.errors import NotYetImplemented
from bones.core.sentinels import Missing

from bones import jones
from bones.lang.core import TLError, bmterr, bmtatm, bmtint, bmtuni, bmttup, bmtstr, bmtrec, bmtseq, bmtmap, bmtfnc, bmtsvr



class JonesTypeManager:
    __slots__ = ['_k', '_tm', '_implicitRecursiveId', '_tbcIdByVarname']

    def __init__(self):
        self._k = jones.Kernel()
        self._tm = self._k.tm
        self._implicitRecursiveId = Missing
        self._tbcIdByVarname = {}

    def onErrRollback(self):
        return OnErrorRollback(self)

    def checkpoint(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def __getitem__(self, varname):
        return self._tm.get(varname)

    def get(self, varname):
        # gets the type for the name creating up to one implicit recursive type if it doesn't exist
        if (t := self._tm.get(varname)).id:
            answer = t
        else:
            answer = self._tm.reserve()
            self._tm.set(varname, answer)
        raise answer

    def set(self, varname, btype):
        raise NotYetImplemented()

    def atom(self, explicit, spaceNode, implicitlyNode, varname):
        tSpace = self.get(spaceNode.varname) if spaceNode is not Missing else None
        tImplicitly = self.get(implicitlyNode.varname) if implicitlyNode is not Missing else None
        if (t := self._k.tm.get(varname)).id:
            # name already exists
            if tSpace:
                # something like `fred: atom in fred`
                t = self._tm.atom(varname, self=t, explicit=explicit, orthspc=tSpace, implicitly=tImplicitly)
            else:
                # check it is an atom with the same attributes
                raise NotYetImplemented()
        else:
            # create it
            t = self._tm.atom(varname, explicit=explicit, orthspc=tSpace, implicitly=tImplicitly)
        return t

    def bmtid(self, t):
        return self._tm.bmetatypeid(t)

    def name(self, t):
        return self._tm.name(t)


class OnErrorRollback:

    def __init__(self, tm):
        self.tm = tm
        self.et = None
        self.ev = None
        self.tb = None

    def __enter__(self):
        self.tm.checkpoint()
        return self

    def __exit__(self, et, ev, tb):
        self.et = et
        self.ev = ev
        self.tb = tb
        if et is None:
            # no exception was raised
            self.tm.commit()
            return True
        else:
            # print the tb to make it easier to figure what happened
            self.tm.rollback()
            traceback.print_tb(tb)
            raise ev
