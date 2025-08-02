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

import contextlib, traceback


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


class assertIs:
    def __init__(self, type):
        self.type = type
    def __rrshift__(self, lhs):     # lhs >> self
        assert isinstance(lhs, self.type)
        return lhs


class assertRaises:

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

