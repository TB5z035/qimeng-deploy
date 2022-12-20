#!/usr/bin/env python

from distutils.core import setup, Extension

setup(
    name='pymvsdk',
    version='1.0',
    description='MindVision Camera SDK',
    packages=['mvsdk'],
    ext_modules=[Extension(
        'mvsdk', [],
        include_dirs=['include'],
        runtime_library_dirs=['lib'],
    )],
)
