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

import inspect, types, traceback, contextlib
from bones.core.errors import ProgrammerError

ignore = [
    'IPython', 'ipykernel', 'pydevd', 'coppertop.pipe', '_pydev_imps._pydev_execfile', 'tornado', 'runpy', 'asyncio',
    'traitlets'
]

def raiseLess(ex, includeMe=True):
    tb = None
    frame = inspect.currentframe()  # do not use `frameInfos = inspect.stack(0)` as it is much much slower
    # discard the frames for add_traceback
    if not includeMe:
        if frame.f_code.co_name == 'raiseLess':
            frame = frame.f_back
    while True:
        try:
            # frame = sys._getframe(depth)
            frame = frame.f_back
            if not frame: break
        except ValueError as e:
            break
        fullname = frame.f_globals['__name__'] + '.' + frame.f_code.co_name
        # print(fullname)
        if not [fullname for i in ignore if fullname.startswith(i)]:
            # print('-------- '+fullname)
            tb = types.TracebackType(tb, frame, frame.f_lasti, frame.f_lineno)
        else:
            pass
            # print(fullname)
        if fullname == '__main__.<module>': break
    hasPydev = False
    hasIPython = False
    if frame:
        while True:
            # frame = sys._getframe(depth)
            frame = frame.f_back
            if not frame: break
            fullname = frame.f_globals['__name__'] + '.' + frame.f_code.co_name
            # print(fullname)
            if fullname.startswith("pydevd"): hasPydev = True
            if fullname.startswith("IPython"): hasIPython = True
    if hasPydev or hasIPython:
        raise ex.with_traceback(tb) from None
    else:
        raise ex from None #ex.with_traceback(tb)


def firstKey(d):
    # https://stackoverflow.com/questions/30362391/how-do-you-find-the-first-key-in-a-dictionary
    for k, v in d.items():
        return k
    raise ProgrammerError(f'd is empty')

def firstValue(d):
    # https://stackoverflow.com/questions/30362391/how-do-you-find-the-first-key-in-a-dictionary
    for k, v in d.items():
        return v
    raise ProgrammerError(f'd is empty')



@contextlib.contextmanager
def HookStdOutErrToLines():
    oldout, olderr = sys.stdout, sys.stderr
    try:
        sys.stdout = _StreamToLines()
        sys.stderr = _StreamToLines()
        yield [sys.stdout.lines, sys.stderr.lines]
    finally:
        sys.stdout, sys.stderr = oldout, olderr


class _StreamToLines:
    def __init__(self):
        self.lines = []
        self.textBuffer = ""
    def write(self, text=""):
        if len(text) > 0:
            splits = text.split("\n")
            for split in splits[:-1]:
                self.textBuffer += split
                self.lines.append(self.textBuffer)
                self.textBuffer = ""
            self.textBuffer += splits[-1:][0]
