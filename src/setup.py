import os, sys, setuptools

parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
python_include_dir = os.path.abspath(os.path.join(sys.executable, 'include'))

# read the contents of README.md file
with open(os.path.join(parent_folder, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

version = '2024.03.09.1'

setuptools.setup(
    name='coppertop',
    packages=[
        'bones',
        'bones.core',
        'bones.ipykernel',
        'bones.kernel',
        'bones.lang',
        'coppertop',
    ],
    ext_modules=[
        setuptools.Extension(
            "bones.jones",
            [os.path.join(parent_folder, "bk/src/jones/mod_jones.c")],
            include_dirs=[python_include_dir],
        ),
        setuptools.Extension(
            "bones.qu",
            [os.path.join(parent_folder, "bk/src/jones/mod_qu.c")],
            include_dirs=[python_include_dir],
        ),
    ],
    # package_dir = {'': 'core'},
    # namespace_packages=['coppertop_'],
    version=version,
    python_requires='>=3.11',
    license='Apache',
    description = 'Multiple-dispatch, partial functions and pipeline operator for Python',
    long_description_content_type='text/markdown',
    long_description=long_description,
    author = 'David Briant',
    author_email = 'dangermouseb@forwarding.cc',
    url = 'https://github.com/coppertop-bones/coppertop',
    download_url = '',
    keywords = [
        'multiple', 'dispatch', 'piping', 'pipeline', 'pipe', 'functional', 'multimethods', 'multidispatch',
        'functools', 'lambda', 'curry', 'currying'
    ],
    install_requires=['numpy >= 1.17.3'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.11',
    ],
    zip_safe=False,
)
