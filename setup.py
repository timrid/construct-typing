#!/usr/bin/env python
from setuptools import setup

version_string = "?.?.?"
exec(open("./construct_typed/version.py").read())

setup(
    name="construct-typing",
    version=version_string,
    packages=["construct-stubs", "construct_typed"],
    package_data={
        "construct-stubs": ["*.pyi", "lib/*.pyi"],
        "construct_typed": ["py.typed"],
    },
    license="MIT",
    license_files=("LICENSE",),
    description="Extension for the python package 'construct' that adds typing features",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    platforms=["POSIX", "Windows"],
    url="https://github.com/timrid/construct-typing",
    author="Tim Riddermann",
    python_requires=">=3.7",
    install_requires=[
        "construct==2.10.70",
        "typing_extensions>=4.6.0"
    ],
    keywords=[
        "construct",
        "kaitai",
        "declarative",
        "data structure",
        "struct",
        "binary",
        "symmetric",
        "parser",
        "builder",
        "parsing",
        "building",
        "pack",
        "unpack",
        "packer",
        "unpacker",
        "bitstring",
        "bytestring",
        "annotation",
        "type hint",
        "typing",
        "typed",
        "bitstruct",
        "PEP 561",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Code Generators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Typing :: Typed",
    ],
)
