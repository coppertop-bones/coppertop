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

import inspect, types

from coppertop._utils.sentinels import Missing

handlersByErrSiteId = {}

def _ensureErrors():
    # general exceptions occuring in coppertop-bones

    if not hasattr(sys, '_CPTBError'):
        class CPTBError(Exception):
            def __str__(self):
                if len(self.args) == 0:
                    return super().__str__()
                if len(self.args) == 1:
                    return self.args[0]
                elif len(self.args) == 2:
                    msg, errSite = self.args
                    return msg + f" ({errSite})"
                else:
                    return self.args[0] + f" ({self.args[1:]})"
        sys._CPTBError = CPTBError
    CPTBError = sys._CPTBError

    if not hasattr(sys, '_ProgrammerError'):
        class ProgrammerError(CPTBError): pass
        sys._ProgrammerError = ProgrammerError

    if not hasattr(sys, '_NotYetImplemented'):
        class NotYetImplemented(CPTBError): pass
        sys._NotYetImplemented = NotYetImplemented

    if not hasattr(sys, '_PathNotTested'):
        class PathNotTested(CPTBError): pass
        sys._PathNotTested = PathNotTested

    if not hasattr(sys, '_UnhappyWomble'):
        class UnhappyWomble(CPTBError): pass
        sys._UnhappyWomble = UnhappyWomble

    if not hasattr(sys, '_WTF'):        # polite interpretation pls - What The Flip, What The Frac
        class WTF(CPTBError): pass
        sys._WTF = WTF

    if not hasattr(sys, '_ImpossiblePathError'):
        class ImpossiblePathError(CPTBError): pass
        sys._ImpossiblePathError = ImpossiblePathError


_ensureErrors()
CPTBError = sys._CPTBError
ProgrammerError = sys._ProgrammerError
NotYetImplemented = sys._NotYetImplemented
PathNotTested = sys._PathNotTested
UnhappyWomble = sys._UnhappyWomble
WTF = sys._WTF
ImpossiblePathError = sys._ImpossiblePathError



class ErrSite:
    def __init__(self, *args):
        # args are [class], [id]
        frame = inspect.currentframe()
        if frame.f_code.co_name == '__init__':
            frame = frame.f_back
        self._moduleName = frame.f_globals.get('__name__', Missing)
        self._packageName = frame.f_globals.get('__package__', Missing)
        self._fnName = frame.f_code.co_name
        self._className = Missing
        self._label = Missing

        if len(args) == 0:
            pass
        elif len(args) == 1:
            # id or class
            if isinstance(args[0], type):
                self._className = args[0].__name__
            else:
                self._label = args[0]
        elif len(args) == 2:
            # class, id
            if isinstance(args[0], type):
                self._className = args[0].__name__
                self._label = args[1]
            elif isinstance(args[1], type):
                self._label = args[0]
                self._className = args[1].__name__
        else:
            raise TypeError('too many args')

    @property
    def id(self):
        return (self._moduleName, self._className, self._fnName, self._label)

    def __repr__(self):
        return f'{self._moduleName}{"" if self._className is Missing else f".{self._className}"}>>{self._fnName}' + \
               f'{"" if self._label is Missing else f"[{self._label}]"}'

handlersByErrSiteId = {

    ('__main__', Missing, 'importStuff', "Can't find name") : '...',

    ('bones.kernel.parse_phrase', Missing, 'parsePhrase', 'unknown function') : '...',
    ('bones.kernel.parse_phrase', Missing, 'parsePhrase', 'unknown name') : '...',
    ('bones.kernel.parse_phrase', Missing, 'parsePhrase', 'name already defined'): '...',

}


_ignore = [
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
        if not [fullname for i in _ignore if fullname.startswith(i)]:
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


