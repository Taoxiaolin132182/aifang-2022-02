from distutils.core import setup
from Cython.Build import cythonize

setup(name='Test Cython App',
      ext_modules=cythonize("test_cython.pyx", language_level=3, language="c++"))


