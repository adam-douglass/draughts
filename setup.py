from setuptools import setup, find_packages
setup(
    name="draughts",
    version="0.0",
    packages=find_packages(),
    
    # metadata to display on PyPI
    author="Adam Douglass",
    author_email="douglass@malloc.ca",
    description="Generates boilerplate for data objects.",
    keywords="utility typechecking",
    url="https://github.com/adam-douglass/draughts/",
    extras_require={
        'test': ['pytest', 'pytest-subtests']
    },
)
