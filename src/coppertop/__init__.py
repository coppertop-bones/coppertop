# **********************************************************************************************************************
#
#                             Copyright (c) 2022 David Briant. All rights reserved.
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


import builtins, sys
from bones import jones


# rejected ideas:
# 1) from coppertop import dm - creates dm if it doesn't exist  - can't distinguish between new module and misspelt thing
# 2) `import dm` or `from fred import dm` always return bones module if it is defined - messing with python imports


if '_oldImportFnForCoppertop' not in sys.__dict__:
    sys._bmodules = {}
    sys._oldImportFnForCoppertop = builtins.__import__

    def _newImport(name, globals=None, locals=None, fromlist=(), level=0):
        splits = name.split('.', maxsplit=1)
        if splits[0] == 'coppertop':
            if name in ('coppertop._scopes', 'coppertop.pipe'):
                return sys._oldImportFnForCoppertop(name, globals, locals, fromlist, level)
            if not fromlist:
                raise ImportError('coppertop has modified builtins.__import__ to handle bones style modules - correct usage is from coppertop.x.y.z import a, b, c')
            bmodname = splits[1] if len(splits) == 2 else ''   # no splits means we're importing from the root namespace, i.e. from coppertop import a, b, c
            if (mod := sys._bmodules.get(bmodname, None)):
                for nameToImport in fromlist:
                    all = []
                    if nameToImport == '*':
                        if not all:
                            # reconstruct __all__ - only expose functions not types nor values
                            for k, fn in mod.__dict__.items():
                                if isinstance(fn, (jones._nullary, jones._unary, jones._binary, jones._ternary, jones._rau)):
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




if __name__ == "__main__":
    import dm.pp
    from coppertop import *
    dm >> TT >> DD
    from coppertop import dm
    dm >> TT >> DD
    from coppertop.pipe import *
    coppertop >> TT >> DD

    '2' >> PP
    import dm.pp
    dm >> TT >> DD
    dm.pp >> TT >> DD

    '3' >> PP
    from coppertop import dm
    dm >> TT >> DD
    from dm.pp import Missing
    dm >> TT >> DD
    dm.pp >> TT >> DD

