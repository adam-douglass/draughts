import os
from setuptools import setup, find_packages
from pkg_resources import parse_version

modules = None
try:
    from Cython.Build import cythonize
    modules = cythonize([
        'draughts/*.py',
        'draughts/*/*.py'
    ], language_level=3)
    print("Using cython")
except ImportError:
    cythonize = None
    print("Using pure python")


version_string = os.environ.get('DRAUGHTS_VERSION', os.environ.get('GITHUB_REF', "0.0.0").lstrip('refs/tags/v'))
version_string = str(parse_version(version_string))
print("Building version ", version_string)

try:
    readme = open(os.path.join(os.path.dirname(__file__), 'readme.md')).read()
except FileNotFoundError:
    readme = None

setup(
    name="draughts",
    version=version_string,
    packages=find_packages(exclude='test'),
    ext_modules=modules,
    
    # metadata to display on PyPI
    author="Adam Douglass",
    author_email="douglass@malloc.ca",
    description="Generates boilerplate for data objects.",
    long_description=readme,
    long_description_content_type='text/markdown',
    keywords="utility typechecking",
    url="https://github.com/adam-douglass/draughts/",
    install_requires=[
        'rstr',
        'arrow'
    ],
    extras_require={
        'test': ['pytest', 'pytest-subtests'],
        'speedup': ['cython']
    }
)
