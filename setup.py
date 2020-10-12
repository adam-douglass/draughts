import os
from setuptools import setup, find_packages
from pkg_resources import parse_version

setup(
    name="draughts",
    version=str(parse_version(os.environ.get('GITHUB_REF', "0.0.0").lstrip('refs/tags/v'))),
    packages=find_packages(),
    
    # metadata to display on PyPI
    author="Adam Douglass",
    author_email="douglass@malloc.ca",
    description="Generates boilerplate for data objects.",
    long_description=open(os.path.join(os.path.dirname(__file__), 'readme.md')).read(),
    long_description_content_type='text/markdown',
    keywords="utility typechecking",
    url="https://github.com/adam-douglass/draughts/",
    extras_require={
        'test': ['pytest', 'pytest-subtests']
    },
)
