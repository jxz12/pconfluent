from setuptools import setup, find_packages
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
    headers=["pconfluent/pgd.hpp"],
    sources=["pconfluent/pgd.cpp", "pconfluent/swig/pgd_wrap.cxx"],
    extra_compile_args=["-std=c++11"],
    include_dirs=[numpy_include]
)

setup(
    name="pconfluent",
    version="0.4",
    author="Jonathan Zheng",
    author_email="jxz12@ic.ac.uk",
    url="https://www.github.com/jxz12/pconfluent",
    description="A package for producing power-confluent drawings (arXiv:1810.09948)",
    install_requires=['numpy'],
    py_modules=find_packages(),
    ext_modules=[_pgd]
)
