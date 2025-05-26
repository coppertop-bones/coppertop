# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

import traceback

def ctxLabel(ctx):
    label = type(ctx).__name__
    if label.endswith('Context'): label = label[:-7].lower()
    return label


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
            # # print the tb to make it easier to figure what happened
            # print('---------------- OnErrorRollback -----------------')
            # print(''.join(traceback.format_exception(ev)))
            # print('--------------------------------------------------')
            self.tm.rollback()
            raise ev
