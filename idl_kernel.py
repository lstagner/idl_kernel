from IPython.kernel.zmq.kernelbase import Kernel
from IPython.utils.path import locate_profile
from IPython.core.displaypub import publish_display_data
from pexpect import replwrap,EOF,spawn

import signal
from subprocess import check_output
import tempfile
import re
import os
from glob import glob
from shutil import rmtree
from base64 import b64encode
from distutils.spawn import find_executable

__version__ = '0.4'

version_pat = re.compile(r'Version (\d+(\.\d+)+)')

class IDLKernel(Kernel):
    implementation = 'idl_kernel'
    implementation_version = __version__
    language = 'IDL'
    @property
    def language_version(self):
        try:
            m = version_pat.search(self.banner)
            return m.group(1)
        except:
            return "Version ?.?"

    _banner = None
    @property
    def banner(self):
        if self._banner is None:
            try:
                if os.path.basename(self._executable) == 'idl':
                    self._banner = check_output([self._executable, '-e','"print,string(0B)"']).decode('utf-8')
                else:
                    self._banner = check_output([self._executable, '--version']).decode('utf-8')
            except:
                self._banner = ''

        return self._banner
    
    language_info = {'name': 'idl',
                     'codemirror_mode': 'idl',
                     'mimetype': 'text/x-idl',
                     'file_extension': '.pro'}

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_idl()

        try:
            self.hist_file = os.path.join(locate_profile(),'idl_kernel.hist')
        except:
            self.hist_file = None
            self.log.warn('No default profile found, history unavailable')

        self.max_hist_cache = 1000
        self.hist_cache = []

    def _start_idl(self):
        # Signal handlers are inherited by forked processes, and we can't easily
        # reset it from the subprocess. Since kernelapp ignores SIGINT except in
        # message handlers, we need to temporarily reset the SIGINT handler here
        # so that IDL and its children are interruptible.
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            self._executable = find_executable("idl")
            self._child  = spawn(self._executable,timeout = 300)
            self.idlwrapper = replwrap.REPLWrapper(self._child,u"IDL> ",None)
        except:
            self._executable = find_executable("gdl")
            self._child  = spawn(self._executable,timeout = 300)
            self.idlwrapper = replwrap.REPLWrapper(self._child,u"GDL> ",None)
        finally:
            signal.signal(signal.SIGINT, sig)

        self.idlwrapper.run_command("!quiet=1 & defsysv,'!inline',0 & !more=0".rstrip(), timeout=None)
        # Compile IDL routines/functions
        dirname = os.path.dirname(os.path.abspath(__file__))
        self.idlwrapper.run_command(".compile "+dirname+"/snapshot.pro",timeout=None)

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):

        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payloads': [], 'user_expressions': {}}

        elif (code.strip() == 'exit' or code.strip() == 'quit'):
            self.do_shutdown(False)
            return {'status':'abort','execution_count':self.execution_count}

        elif (code.strip().startswith('.') or code.strip().startswith('@')):
            # This is a IDL Executive command
            output = self.idlwrapper.run_command(code.strip(), timeout=None) 

            if os.path.basename(self._executable) == 'idl':
                output = '\n'.join(output.splitlines()[1::])+'\n'

            if not silent:
                stream_content = {'name': 'stdout', 'text':output}
                self.send_response(self.iopub_socket, 'stream', stream_content)

            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payloads': [], 'user_expressions': {}}

        if code.strip() and store_history:
            self.hist_cache.append(code.strip())

        interrupted = False
        tfile_code = tempfile.NamedTemporaryFile(mode='w+t',dir=os.path.expanduser("~"))
        tfile_post = tempfile.NamedTemporaryFile(mode='w+t',dir=os.path.expanduser("~"))
        plot_dir = tempfile.mkdtemp(dir=os.path.expanduser("~"))
        plot_format = 'png'

        postcall = """
            device,window_state=winds_arefgij
            if !inline and total(winds_arefgij) ne 0 then begin
                w_CcjqL6MA = where(winds_arefgij ne 0,nw_CcjqL6MA)
                for i_KEv8eW6E=0,nw_CcjqL6MA-1 do begin
                    wset, w_CcjqL6MA[i_KEv8eW6E]
                    outfile_c5BXq4dV = '%(plot_dir)s/__fig'+strtrim(i_KEv8eW6E,2)+'.png'
                    ii_rsApk4JS = snapshot(outfile_c5BXq4dV)
                    wdelete
                endfor
	    endif
        end
        """ % locals()

        try:
            tfile_code.file.write(code.rstrip()+"\na_adfadfw=1\nend")
            tfile_code.file.close()
            tfile_post.file.write(postcall.rstrip())
            tfile_post.file.close()
            output = self.idlwrapper.run_command(".run "+tfile_code.name, timeout=None)
            self.idlwrapper.run_command(".run "+tfile_post.name,timeout=None)

            # IDL annoying prints out ".run tmp..." command this removes it
            if os.path.basename(self._executable) == 'idl':
                output = '\n'.join(output.splitlines()[1::])+'\n'

            # Publish images if there are any
            images = [open(imgfile, 'rb').read() for imgfile in glob("%s/*.png" % plot_dir)]

            display_data=[]

            for image in images:
                display_data.append({'image/png': b64encode(image).decode('ascii')})

            for data in display_data:
                self.send_response(self.iopub_socket, 'display_data',{'data':data,'metadata':{}})
        except KeyboardInterrupt:
            self.idlwrapper.child.sendintr()
            interrupted = True
            self.idlwrapper._expect_prompt()
            output = self.idlwrapper.child.before
        except EOF:
            output = self.idlwrapper.child.before + 'Restarting IDL'
            self._start_idl()
        finally:
            tfile_code.close()
            tfile_post.close()
            rmtree(plot_dir)

        if not silent:
            stream_content = {'name': 'stdout', 'text':output}
            self.send_response(self.iopub_socket, 'stream', stream_content)
        
        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}
        
        try:
            exitcode = int(self.run_command('print,0').rstrip())
        except Exception:
            exitcode = 1

        if exitcode:
            return {'status': 'error', 'execution_count': self.execution_count,
                    'ename': '', 'evalue': str(exitcode), 'traceback': []}
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payloads': [], 'user_expressions': {}}

    def do_history(self, hist_access_type, output, raw, session=None,
                   start=None, stop=None, n=None, pattern=None, unique=False):

        if not self.hist_file:
            return {'history': []}

        if not os.path.exists(self.hist_file):
            with open(self.hist_file, 'wb') as f:
                f.write('')

        with open(self.hist_file, 'rb') as f:
            history = f.readlines()

        history = history[:self.max_hist_cache]
        self.hist_cache = history
        self.log.debug('**HISTORY:')
        self.log.debug(history)
        history = [(None, None, h) for h in history]

        return {'history': history}

    def do_shutdown(self, restart):
        self.log.debug("**Shutting down")

        self.idlwrapper.child.kill(signal.SIGKILL)

        if self.hist_file:
            with open(self.hist_file,'wb') as f:
                data = '\n'.join(self.hist_cache[-self.max_hist_cache:])
                f.write(data.encode('utf-8'))

        return {'status':'ok', 'restart':restart}

if __name__ == '__main__':
    from IPython.kernel.zmq.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=IDLKernel)
