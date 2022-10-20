from distutils.core import setup, Extension

# https://stackoverflow.com/questions/27281785/python-setup-py-how-to-set-the-path-for-the-generated-so

setup(
    name="jones",
    version="2022.11.05",
    ext_modules=[Extension("bones.jones", ["./bones/c/jones/__jones.c"])]
)

