# **********************************************************************************************************************
#
#                             Copyright (c) 2022 David Briant. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
#
# **********************************************************************************************************************

import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)

import builtins, types
from bones import jones


# rejected ideas:
# 1) from groot import dm - creates dm if it doesn't exist  - can't distinguish between a new module and a misspelt one
# 2) `import dm` or `from fred import dm` always return bones module if it is defined - messing with python imports
#
# unusally we have a __init__ file so that the importer is included even if you just do import coppertop


if '_oldImportFnForCoppertop' not in sys.__dict__:

    class BModule(types.ModuleType):
        def __repr__(self):
            return f'BModule({self.__name__})'

        def __getattribute__(self, name):
            try:
                answer = super().__getattribute__(name)
            except AttributeError as ex:
                raise AttributeError(
                    f"bones module '{self.__name__}' has no attribute '{name}' - maybe it's defined in a python module "
                    f"that needs to be imported"
                ) from None
            return answer


    sys._bmodules = {'': BModule('')}
    sys._oldImportFnForCoppertop = builtins.__import__

    def _newImport(name, globals=None, locals=None, fromlist=(), level=0):
        splits = name.split('.', maxsplit=1)
        # if splits[0] == 'coppertop':
        #     if name in ('coppertop._scopes', 'coppertop.pipe'):
        #         return sys._oldImportFnForCoppertop(name, globals, locals, fromlist, level)
        if splits[0] == 'groot':
            if not fromlist:
                if len(splits) > 1:
                    raise ImportError("groot is a virtual package with no importable submodules - usage is either 'import groot' or 'from groot.x.y import z'")
                else:
                    # i.e. import groot
                    return sys._bmodules['']
            bmodname = splits[1] if len(splits) == 2 else ''   # no splits means we're importing from the root namespace, i.e. from groot import a, b, c
            if (mod := sys._bmodules.get(bmodname, None)):
                for nameToImport in fromlist:
                    all = []
                    if nameToImport == '*':
                        if not all:
                            # reconstruct __all__ - only expose functions not types nor values
                            for k, fn in mod.__dict__.items():
                                if isinstance(fn, (jones._nullary, jones._unary, jones._binary, jones._ternary)):
                                    all.append(k)
                            mod.__dict__['__all__'] = all
                    else:
                        if nameToImport not in mod.__dict__:
                            raise ImportError(
                                f'Can\'t find "{nameToImport}" in {name} - it\'s probably not been loaded yet')
                return mod
            else:
                raise ImportError(f'bones module "{bmodname}" has not been loaded yet')

        mod = sys._oldImportFnForCoppertop(name, globals, locals, fromlist, level)
        # if splits[0]:
        #     mod = sys._bmodules.get(splits[0], mod)
        return mod

    builtins.__import__ = _newImport
