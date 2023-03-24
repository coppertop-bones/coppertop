from setuptools import setup, find_packages
from distutils.core import Extension
import coppertop.pipe

# read the contents of README.md file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

version = coppertop.__version__

# print(find_packages())
# https://stackoverflow.com/questions/27281785/python-setup-py-how-to-set-the-path-for-the-generated-so

setup(
  name='coppertop',
  packages=[
    'bones',
    'bones.c',
    'bones.c.jones',
    'bones.c.jones.other',
    'bones.core',
    'bones.ipykernel',
    'bones.kernel',
    'bones.lang',
    'coppertop',
  ],
  ext_modules=[Extension("bones.jones", ["./bones/c/jones/__jones.c"])],
  # package_dir = {'': 'core'},
  # namespace_packages=['coppertop_'],
  version=version,
  python_requires='>=3.9',
  license='Apache',
  description = 'Multiple-dispatch, partial functions and pipeline operator for Python',
  long_description_content_type='text/markdown',
  long_description=long_description,
  author = 'David Briant',
  author_email = 'dangermouseb@forwarding.cc',
  url = 'https://github.com/coppertop-bones/coppertop',
  download_url = '',
  keywords = ['multiple', 'dispatch', 'piping', 'pipeline', 'pipe', 'functional', 'multimethods', 'multidispatch',
    'functools', 'lambda', 'curry', 'currying'],
  install_requires=['numpy >= 1.17.3'],
  include_package_data=True,
  classifiers=[
    'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Science/Research',
    'Topic :: Utilities',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
  ],
  zip_safe=False,
)

# https://autopilot-docs.readthedocs.io/en/latest/license_list.html
# https://pypi.org/classifiers/
