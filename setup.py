from setuptools import setup
from setuptools.extension import Extension

# Third-party modules - we depend on numpy for everything
import numpy
# Obtain the numpy include directory.  This logic works across numpy versions.
try:
    numpy_include = numpy.get_include()
except AttributeError:
    numpy_include = numpy.get_numpy_include()

_pgd = Extension(
    name="_pgd",
    sources=["pgd_wrap.cxx", "pgd.cpp"],
    extra_compile_args=["-std=c++11"],
    include_dirs=[numpy_include]
)

setup(
    name="pconfluent",
    version="0.1",
    author="Jonathan Zheng",
    author_email="jxz12@ic.ac.uk",
    description="A package for...",
    install_requires=['numpy'],
    setup_requires=['numpy'],
    #py_modules=['pconfuent'],
    ext_modules=[_pgd]
)

