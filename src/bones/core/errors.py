# **********************************************************************************************************************
#
#                             Copyright (c) 2019-2020 David Briant. All rights reserved.
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

import sys, inspect

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


_ensureErrors()
CPTBError = sys._CPTBError
ProgrammerError = sys._ProgrammerError
NotYetImplemented = sys._NotYetImplemented
PathNotTested = sys._PathNotTested
UnhappyWomble = sys._UnhappyWomble

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

class ParagraphError(BonesError):           # grouping errors
    def __init__(self, msg, errSite, group, token):
        super().__init__(msg, errSite)
        self._group = group
        self._token = token

class SentenceError(BonesError): pass       # phrase parsing errors

class GrammarError(BonesError): pass        # for type errors

class DictionaryError(BonesError): pass     # can't find a name in a phrase

class AmbiguousVerbError(BonesError): pass  # aka does not understand, i.e. the necessary overload doesn't exist

class LoadingError(BonesError): pass      # load tool.kit

class ImportError(BonesError): pass         # e.g. from tools.bag import x - x doesn't exist

class ScopeError(BonesError): pass          # e.g. trying to get from or set in the wrong scope



class ErrSite(object):
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
