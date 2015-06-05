#!/usr/bin/env python
from setuptools import setup

setup(
    name="Vagrant Pooler",
    version="0.0.1",
    author="Britt Gresham",
    author_email="brittcgresham@gmail.com",
    description=("Like the vmpooler but using vagrant instead"),
    license="MIT",
    install_requires=[
        'flask',
        'python-vagrant',
    ],
)

