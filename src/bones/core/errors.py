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

import inspect

from bones.core.sentinels import Missing, classType

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

    if not hasattr(sys, '_WTF'):        # polite interpretation of pls - What The Flip, What The Frac
        class WTF(CPTBError): pass
        sys._WTF = WTF


_ensureErrors()
CPTBError = sys._CPTBError
ProgrammerError = sys._ProgrammerError
NotYetImplemented = sys._NotYetImplemented
PathNotTested = sys._PathNotTested
UnhappyWomble = sys._UnhappyWomble
WTF = sys._WTF

class DocumentationError(Exception): pass

class BonesError(Exception):
    def __init__(self, msg, errSite):
        super().__init__(msg)
        self._site = errSite
        if (desc := handlersByErrSiteId.get(errSite.id, Missing)) is Missing:
            print(f'Unknown ErrSiteId - {errSite.id}')
            raise DocumentationError()
        elif desc.endswith('...'):
            pass
            # print(f'{errSite.id} needs work:')
            # print(desc)

class SpellingError(BonesError): pass       # lex errors

class GroupError(BonesError):               # grouping errors
    def __init__(self, msg, errSite, group, token):
        super().__init__(msg, errSite)
        self._group = group
        self._token = token

class SentenceError(BonesError): pass       # phrase parsing errors

class GrammarError(BonesError): pass        # for type errors

class DictionaryError(BonesError): pass     # can't find a name in a phrase

class AmbiguousVerbError(BonesError): pass  # aka does not understand, i.e. the necessary overload doesn't exist

class LoadingError(BonesError): pass        # load tool.kit

class ImportError(BonesError): pass         # e.g. from tools.bag import x - x doesn't exist

class ScopeError(BonesError): pass          # e.g. trying to get from or set in the wrong scope



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
            if isinstance(args[0], classType):
                self._className = args[0].__name__
            else:
                self._label = args[0]
        elif len(args) == 2:
            # class, id
            if isinstance(args[0], classType):
                self._className = args[0].__name__
                self._label = args[1]
            elif isinstance(args[1], classType):
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

    ('bones.lang.parse_phrase', Missing, 'parsePhrase', 'unknown function') : '...',
    ('bones.lang.parse_phrase', Missing, 'parsePhrase', 'unknown name') : '...',
    ('bones.lang.parse_phrase', Missing, 'parsePhrase', 'name already defined'): '...',

}
