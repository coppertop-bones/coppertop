# **********************************************************************************************************************
#
#                             Copyright (c) 2012-2022 David Briant. All rights reserved.
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
    for k in d:
        return k
    raise ProgrammerError(f'd is empty')

def firstValue(d):
    # https://stackoverflow.com/questions/30362391/how-do-you-find-the-first-key-in-a-dictionary
    for v in d.values():
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


class _StreamToLines(object):
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


class assertRaises(object):

    def __init__(self, expectedExceptionType):
        self.expectedExceptionType = expectedExceptionType
        self.exceptionType = None
        self.exceptionValue = None
        self.tb = None

    def __enter__(self):
        return self

    def __exit__(self, exceptionType, exceptionValue, tb):
        self.exceptionType = exceptionType
        self.exceptionValue = exceptionValue
        self.tb = tb
        if exceptionType is None:
            # no exception was raised
            raise AssertionError("No exception raised, %s expected." % self.expectedExceptionType)        # no error was raised
        elif not issubclass(exceptionType, self.expectedExceptionType):
            # the wrong exception was raised
            # print the tb to make it easier to figure why the test is failing
            traceback.print_tb(tb)
            raise AssertionError("%s raised. %s expected." % (exceptionType, self.expectedExceptionType))
        else:
            # the correct error was raised
            return True
