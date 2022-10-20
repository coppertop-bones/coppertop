# **********************************************************************************************************************
#
#                             Copyright (c) 2020 David Briant. All rights reserved.
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


# Useful references
# https://github.com/Calysto/metakernel/
# https://andrew.gibiansky.com/blog/ipython/ipython-kernels/
# https://jupyter-client.readthedocs.io/en/latest/kernels.html
# https://jupyter-client.readthedocs.io/en/stable/messaging.html


import sys, logging, traceback, ast, datetime
from coppertop.pipe import *
from bones.core.utils import HookStdOutErrToLines
from bones.core.sentinels import Missing, Void
from bones.core.errors import ProgrammerError, BonesError
from ipykernel.kernelbase import Kernel
from bones.kernel import psm
from bones.kernel.bones import BonesKernel
from bones.lang.execute import TCInterpreter
from bones.lang.core import GLOBAL, SCRATCH
from bones.lang.ctx import Ctx


from traitlets import Any, Bool, Instance, List, Type, observe, observe_compat
from pygments.lexers import load_lexer_from_file, get_all_lexers, _load_lexers
# from bones.ipykernel.bones_lexer import BonesLexer
_load_lexers('bones.ipykernel.pygments_lexers')


STD_ERR = 'stderr'
STD_OUT = 'stdout'


MAGIC = '%%'    # %%python seams to cause Jupyter notebook to do python syntax highlighting :) but not Jupyter lab :(
DEFAULT_HANDLER = 'DEFAULT_HANDLER'
DEFAULT_CMD = 'execute'
_groupCommands = ['restartAll']




def _newKernel():
    sm = psm.PythonStorageManager()
    k = BonesKernel(sm)
    k.ctxs[GLOBAL] = Ctx(k, Missing, Missing, Missing, Missing, GLOBAL)
    k.ctxs[SCRATCH] = scratchCtx = Ctx(k, Missing, Missing, Missing, k.ctxs[GLOBAL], SCRATCH)
    k.scratch = scratchCtx
    k.tcrunner = TCInterpreter(k, scratchCtx)
    sm.frameForCtx(k.ctxs[GLOBAL])
    sm.frameForCtx(k.ctxs[SCRATCH])
    return k


class BonesHandler(object):

    def __init__(self):
        self.bonesKernel = _newKernel()

    def execute(self, kernel, src, *args):
        kwargs = {'isInJupyter': True}
        # print(f'args: {args}', file=sys.stderr)
        if 'groups' in args: kwargs['showGroups'] = True
        if 'ast' in args: kwargs['showTc'] = True
        if 'types' in args: kwargs['showTypes'] = True
        if 'norun' in args: kwargs['norun'] = True
        try:
            with context(**kwargs):
                res = self.bonesKernel.run(src)
                if res.error: raise res.error
                if res.result == Void:
                    return kernel.OK_SUPPRESS, [res.result]
                else:
                    return kernel.OK, [res.result]
        except BonesError as ex:
            msg = f'{ex.__class__.__name__}: {ex.args[0]}'
            return kernel.ERROR, [msg]
        except Exception as ex:
            et, ev, tb = sys.exc_info()
            x = traceback.format_exception_only(et, ev)
            print(f'{traceback.format_exc()}', file=sys.stderr)
            return kernel.ERROR, [ex]

    def ast(self, kernel, src, *args):
        return self.execute(kernel, src, *args + ('ast',))

    def groups(self, kernel, src, *args):
        return self.execute(kernel, src, *args + ('groups',))

    def types(self, kernel, src, *args):
        return self.execute(kernel, src, *args + ('types',))

    def norun(self, kernel, src, *args):
        return self.execute(kernel, src, *args + ('norun',))

    def restart(self, kernel, *args):
        try:
            self.bonesKernel = _newKernel()
            return kernel.OK, []
        except Exception as ex:
            return kernel.ERROR, [f'Error restarting bones kernel: {ex}']


    # except Exception:
    #     f = open(DBLogFilename, "a")
    #     t, v, tb = sys.exc_info()
    #     f.write(time.strftime("%I:%M:%S %p, %a %d %b %Y", time.gmtime(time.time())))
    #     f.write(" - Error calling DBStartWing (%s)\n" % traceback.format_exception_only(t, v)[0].strip())
    #     traceback.print_tb(tb, file=f)
    #     f.close()
    #     result = traceback.format_exception_only(t, v)[0].strip()
    #     except Exception:
    #         et, ev, tb = sys.exc_info()
    #         results = {}
    #         results['error'] = "#Unhandled error!"
    #         results['tberror'] = "%s" % traceback.format_exception_only(et, ev)[0].strip()
    #         results['traceback'] = traceback.extract_tb(tb)
    #         results['stack'] = traceback.extract_stack()
    #         if nameArgIndex > 0:
    #             name = args[nameArgIndex - 1]
    #         else:
    #             name = ""
    #         if repositoryNamePrefix: name = "%s.%s" (repositoryNamePrefix, name)
    #         return bundleNameAndObject(name, results, False, "%s(%s)" % (et, ev))             # could possible view the stack to see if errorLocator is defined in wrapped fn
    #
    #     except Exception:
    #         et, ev, tb = sys.exc_info()
    #         tbList = traceback.extract_tb(tb)
    #         for i, line in enumerate(tbList):
    #             if line[0] == filename: break
    #         return "line %s - %s: %s" % (
    #
    #             tbList[i][1], traceback.format_exception_only(et, ev)[0].strip(), traceback.extract_tb(tb)[-1])  # , )
    #
    #     except Exception:
    #         et, ev, tb = sys.exc_info()
    #         return "%s" % ev
    #
    #     return wrapper
    # traceback.format_exc()




class PythonHandler(object):

    def __init__(self):
        self._globals = {'_logger': _logger}

    def execute(self, kernel, src, *args):
        with context(isInJupyter=True):
            #parseAstCompileAndExecute
            self._globals['_kernel'] = kernel
            astModule = ast.parse(src, mode='exec')
            values = []
            lastValue = Missing
            for i, each in enumerate(astModule.body):
                '%r: %r' % (i, type(each))
                if isinstance(each, ast.Expr):
                    e = ast.Expression(each.value)   # change the ast.Expr into an ast.Expression which is suitable for eval
                    bc = compile(e, filename="%r:%r" % (each.lineno, each.end_lineno), mode='eval')
                    lastValue = eval(bc, self._globals)
                    values.append(lastValue)
                else:
                    m = ast.Module([each], astModule.type_ignores)
                    bc = compile(m, filename="%r:%r" % (each.lineno, each.end_lineno), mode='exec')
                    exec(bc, self._globals)
                    lastValue = Void
                    values.append(lastValue)
            if 'noout' in args:
                lastValue = Void

        strippedSrc = src.strip()
        if strippedSrc:
            if strippedSrc[-1] == ';' or lastValue is Void:
                return kernel.OK_SUPPRESS, values
            else:
                return kernel.OK, values
        else:
            return kernel.OK_SUPPRESS, values

    def restart(self, kernel, *args):
        self._globals = {'_logger': _logger}

    def noout(self, kernel, src, *args):
        return self.execute(kernel, src, *args + ('noout',))



class GroupHandler(object):

    OK = 'OK'
    OK_SUPPRESS = 'OK_SUPPRESS'
    ERROR = 'ERROR'

    def __init__(self):
        self.handlers = {}
        self.handlers['python'] = PythonHandler()
        self.handlers['bones'] = BonesHandler()
        self.defaultHandler = 'bones'

    def restartAll(self, kernel, *args):
        for handlerName, handler in self.handlers.items():
            handler.restart(kernel, *args)
            print(f'{handlerName} restarted at %r' % datetime.datetime.now())
        return self.OK_SUPPRESS, []



class MultiKernel(Kernel):
    # Kernel (the base class) takes the responsibility for incrementing execution_count so we don't have to

    # Kernel info fields
    implementation = 'multi_kernel'
    implementation_version = '0.1.0'
    banner = 'bone multi-kernel'

    # ('IPython', ['ipython2', 'ipython'], [],
    #   ['text/x-python', 'application/x-python', 'text/x-python3', 'application/x-python3'])
    # ('IPython3', ['ipython3'], [],
    #   ['text/x-python', 'application/x-python', 'text/x-python3', 'application/x-python3'])

    language_info = {
        'name': 'bones',
        'mimetype': 'text/x-bones',
        # "mimetype": "text/x-python",
        # 'file_extension': '.bones',
        "version": 10,
        "codemirror_mode": {"name": "robotframework"},
        # "codemirror_mode": {"name": "ipython", "version": 3},
        "pygments_lexer": "bones",
        # "pygments_lexer": "python3",
        # "nbconvert_exporter": "python",
        # "file_extension": ".py",
    }

    # ('Python', ('python', 'py', 'sage', 'python3', 'py3'), (
    # '*.py', '*.pyw', '*.jy', '*.sage', '*.sc', 'SConstruct', 'SConscript', '*.bzl', 'BUCK', 'BUILD', 'BUILD.bazel',
    # 'WORKSPACE', '*.tac'), ('text/x-python', 'application/x-python', 'text/x-python3', 'application/x-python3'))
    # ('Python Traceback', ('pytb', 'py3tb'), ('*.pytb', '*.py3tb'),
    #  ('text/x-python-traceback', 'text/x-python3-traceback'))

    # implementation = "ipython"
    # implementation_version = release.version
    # language_info = {
    #     "name": "python",
    #     "version": sys.version.split()[0],
    #     "codemirror_mode": {"name": "ipython", "version": sys.version_info[0]},
    #     "pygments_lexer": "ipython%d" % 3,
    #     "nbconvert_exporter": "python",
    #     "file_extension": ".py",
    # }


    # # This should be overridden by wrapper kernels that implement any real
    # # language.
    # language_info: t.Dict[str, object] = {}
    #
    # # any links that should go in the help menu
    # help_links = List()



    help_links = List(
        [
            {
                "text": "Bones Reference",
                "url": "https://github.com/DangerMouseB/coppertop-bones",
            },
        ]
    ).tag(config=True)





    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._groupHandler = GroupHandler()
        # self.log.setLevel(logging.INFO)
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y.%m.%d %I:%M:%S %p')
        if False:
            _logger.error = LogTo(self.log, logging.ERROR)
            _logger.warn = LogTo(self.log, logging.ERROR)
            _logger.info = LogTo(self.log, logging.ERROR)
            _logger.debug = LogTo(self.log, logging.ERROR)


    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        self.stream(STD_ERR,
            repr((code, silent, store_history, user_expressions, allow_stdin))
        )
        if silent or len(code.strip()) == 0:
            return self.execute_reply_ok()

        sectionNum = 0
        sections = _splitSections(code)
        for magicLine, sectionSrc in sections:
            sectionNum += 1
            with HookStdOutErrToLines() as stdouterrLines:
                try:
                    handlerId, cmd, args, handler = Missing, Missing, Missing, Missing
                    if magicLine == DEFAULT_HANDLER:
                        # no magic to parse
                        handlerId = self._groupHandler.defaultHandler
                        cmd = DEFAULT_CMD
                        args = [sectionSrc]
                        handler = self._groupHandler.handlers.get(handlerId, None)
                    else:
                        # PARSE MAGIC
                        t = magicLine.split('%%')
                        tokens = [e for e in [e.strip() for e in t[1].split(',')] if e]
                        handlerOrMethod = tokens[0]                 # OPEN: take intersection so order is less important?
                        if handlerOrMethod in _groupCommands:
                            # sending a group command - %%group_cmd, arg1, arg2, ...
                            handlerId = 'kernel'
                            cmd = handlerOrMethod
                            args = tokens[1:]
                            if sectionSrc:
                                raise SyntaxError(f'Group cmd {cmd} does not process src so it must not be provided')
                            handler = self._groupHandler
                        elif handlerOrMethod in self._groupHandler.handlers:
                            # sending a command to a specific handler - %%handler, arg1, arg2, ...
                            if len(tokens) == 1:
                                # print(f'2a. {magicLine} (section {sectionNum}) - {tokens}', file=sys.stderr)
                                handlerId = handlerOrMethod
                                cmd = DEFAULT_CMD
                                args = [sectionSrc]
                                handler = self._groupHandler.handlers[handlerId]
                            elif len(tokens) > 1:
                                # print(f'2b. {magicLine} (section {sectionNum}) - {tokens}', file=sys.stderr)
                                handlerId = handlerOrMethod
                                cmd = tokens[1]
                                args = [sectionSrc] + tokens[1:]
                                handler = self._groupHandler.handlers[handlerId]
                            else:
                                raise ProgrammerError()
                        else:
                            # sending to the default kernel
                            if len(tokens) == 1:
                                # %%arg
                                # print(f'3a. {magicLine} (section {sectionNum}) - {tokens}', file=sys.stderr)
                                handlerId = self._groupHandler.defaultHandler
                                cmd = handlerOrMethod
                                args = [sectionSrc] + [handlerOrMethod]
                                handler = self._groupHandler.handlers[handlerId]
                            elif len(tokens) >= 2:
                                # print(f'3b. {magicLine} (section {sectionNum}) - {tokens}', file=sys.stderr)
                                handlerId = self._groupHandler.defaultHandler
                                cmd = handlerOrMethod
                                args = [sectionSrc] + tokens
                                handler = self._groupHandler.handlers[handlerId]
                            else:
                                raise ProgrammerError()

                    if handler:
                        # _logger.info(handlerId)
                        # call execute on the default if it exists
                        handlerFn = getattr(handler, cmd, None)
                        if handlerFn:
                            # print(f'4. (section {sectionNum}) {cmd} - {args}', file=sys.stderr)
                            # HANDLE THE SECTION
                            outcome, values = handlerFn(self._groupHandler, *args)

                            # TODO handle other mime types, e.g. for plotnine etc
                            if values:
                                if outcome == self._groupHandler.OK:
                                    print(values[-1])
                                elif outcome == self._groupHandler.ERROR:
                                    print(values[-1], file=sys.stderr)
                                elif outcome == self._groupHandler.OK_SUPPRESS:
                                    pass
                        else:
                            print('%s (section %s) - %s has no handler fn %s' % (magicLine, sectionNum, handlerId, cmd), file=sys.stderr)
                    else:
                        if magicLine == DEFAULT_HANDLER:
                            print('No default handler defined', file=sys.stderr)
                        else:
                            if handlerId:
                                print('%s (section %s) - no handler found' % (magicLine, sectionNum), file=sys.stderr)
                            else:
                                print('%s (section %s) - Unknown magic' % (magicLine, sectionNum), file=sys.stderr)

                except Exception as ex:
                    t, v, tb = sys.exc_info()
                    traceback.print_exception(t, v, tb, file=sys.stderr)
                    print()

            stdoutLines, stderrLines = stdouterrLines
            if stdoutLines:
                if len(sections) > 1:
                    self.stream(STD_OUT, '[%s] %s\n' % (sectionNum, magicLine))
                self.stream(STD_OUT, '\n'.join(stdoutLines))
                self.stream(STD_OUT, '\n')
            if stderrLines:
                if len(sections) > 1:
                    self.stream(STD_ERR, '[%s] %s\n' % (sectionNum, magicLine))
                self.stream(STD_ERR, '\n'.join(stderrLines))
                self.stream(STD_ERR, '\n')

        return self.execute_reply_ok()



    def do_complete(self, code, cursor_pos):
        # for the moment use ' ' to break up tokens
        _logger.info << code << ", " << str(cursor_pos)
        return {
            'matches': ['fred', 'joe'],
            'cursor_start': 0,
            'cursor_end': cursor_pos,
            'metadata': dict(),
            'status': 'ok'
        }

    #     code = code[:cursor_pos]
    #     default = {'matches': [], 'cursor_start': 0,
    #                'cursor_end': cursor_pos, 'metadata': dict(),
    #                'status': 'ok'}
    #
    #     if not code or code[-1] == ' ':
    #         return default
    #
    #     tokens = code.replace(';', ' ').split()
    #     if not tokens:
    #         return default
    #
    #     matches = []
    #     token = tokens[-1]
    #     start = cursor_pos - len(token)
    #
    #     if token[0] == '$':
    #         # complete variables
    #         cmd = 'compgen -A arrayvar -A export -A variable %r' % token[1:] # strip leading $
    #         output = self.bashwrapper.run_command(cmd).rstrip()
    #         completions = set(output.split())
    #         # append matches including leading $
    #         matches.extend(['$'+c for c in completions])
    #     else:
    #         # complete functions and builtins
    #         cmd = 'compgen -cdfa %r' % token
    #         output = self.bashwrapper.run_command(cmd).rstrip()
    #         matches.extend(output.split())
    #
    #     if not matches:
    #         return default
    #     matches = [m for m in matches if m.startswith(token)]
    #
    #     return {'matches': sorted(matches), 'cursor_start': start,
    #             'cursor_end': cursor_pos, 'metadata': dict(),
    #             'status': 'ok'}


    def stream(self, name, text):
        self.send_response(
            self.iopub_socket,
            'stream',
            dict(
                name=name,
                text=text
            )
        )

    def execute_reply_ok(self):
        return dict(
            status='ok',
            execution_count=self.execution_count,
            payload=[],
            user_expressions={}
        )

    def execute_reply_error(self):
        return dict(
            status='error',
            execution_count=self.execution_count
        )



# **********************************************************************************************************************
# helpers
# **********************************************************************************************************************

def _splitSections(txt):
    # answers list of (magicLine, src) where each section has prior lines as 
    # blank (so line-numbers are preserved in compiling) and magic blanked out
    sections = []
    currentSection = []
    lines = txt.splitlines()
    magic = DEFAULT_HANDLER
    for line in lines:
        if line.startswith(MAGIC):
            if currentSection:
                sections.append((magic, '\n'.join(currentSection)))
            currentSection = [''] * (len(currentSection))
            magic = line
            line = ''         # blank out the magic
        currentSection.append(line)
    if currentSection:
        sections.append((magic, '\n'.join(currentSection)))
    return sections


def logTo(logger, level):
    def actual(msg, **kwargs):
        logger.log(level, msg, **kwargs)
    return actual


class _Dummy(object):pass
_logger = _Dummy()
_logger.error = logTo(logging.getLogger(__name__), logging.ERROR)
_logger.warn = logTo(logging.getLogger(__name__), logging.WARN)
_logger.info = logTo(logging.getLogger(__name__), logging.INFO)
_logger.debug = logTo(logging.getLogger(__name__), logging.DEBUG)
_logger.critical = logTo(logging.getLogger(__name__), logging.CRITICAL)



if __name__ == '__main__':
    # for e in get_all_lexers():
    #     print(e)
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=MultiKernel)

