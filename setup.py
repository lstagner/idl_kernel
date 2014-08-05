from distutils.core import setup
from distutils.command.install import install
import sys

class install_with_kernelspec(install):
    def run(self):
        install.run(self)
        from IPython.kernel.kernelspec import install_kernel_spec
        install_kernel_spec('kernelspec', 'IDL', replace=True)

with open('README.md') as f:
    readme = f.read()

svem_flag = '--single-version-externally-managed'
if svem_flag in sys.argv:
    sys.argv.remove(svem_flag)

setup(name='IDL_kernel',
      version='0.1',
      description='A IDL kernel for IPython',
      long_description=readme,
      author='Luke Stagner',
      py_modules=['idl_kernel'],
      cmdclass={'install': install_with_kernelspec},
      install_requires=['pexpect>=3.3'],
      classifiers = [
          'Framework :: Jupyter',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Shells',
      ]
)
