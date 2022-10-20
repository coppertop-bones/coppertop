from setuptools import setup, find_packages
import bones.meta

# read the contents of README.md file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

version = bones.meta.version

# print(find_packages())


setup(
  name='coppertop-bones',
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
    'dm',
    'dm._core',
    'dm.core',
  ],
  # package_dir = {'': 'core'},
  # namespace_packages=['coppertop_'],
  version=version,
  python_requires='>=3.9',
  license='BSD',
  description = 'Partial functions, multi-dispatch and pipeline style for Python',
  long_description_content_type='text/markdown',
  long_description=long_description,
  author = 'David Briant',
  author_email = 'dangermouseb@forwarding.cc',
  url = 'https://github.com/coppertop-bones/coppertop-bones',
  download_url = '',
  # download_url = f'https://github.com/DangerMouseB/coppertop-bones/archive/{version}.tar.gz',
  keywords = ['piping', 'pipeline', 'pipe', 'functional'],
  install_requires=[],
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
  ],
  zip_safe=False,
)

# https://autopilot-docs.readthedocs.io/en/latest/license_list.html
# https://pypi.org/classifiers/
