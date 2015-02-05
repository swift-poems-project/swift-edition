#!/usr/bin/env python

from setuptools import setup, find_packages

setup(

    name='LafayetteCollegeLibraries-SwiftDiff',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'py.test',
        'flask',
        'lxml2',
        'nltk',
        'networkx'
        ],
    author='jrgriffiniii',
    author_email='griffinj@lafayette.edu',
    url='https://github.com/LafayetteCollegeLibraries/swift-diff',
    description='Textual analysis web service for the [Swift Poems Project](http://swift.lafayette.edu)',
    keywords=[],
    zip_safe=False
    )

