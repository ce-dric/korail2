# -*- coding: utf-8 -*-
"""
Korail2 -- Korail (www.letskorail.com) wrapper for Python.
==========================================================

Fork of korail2 with N-card discount support.
"""
from __future__ import with_statement

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

# detect the current version
version = '0.4.0'

import codecs

with codecs.open('README.md', 'r', encoding='utf8') as f:
    long_desc = f.read()

setup(
    name='korail2',
    packages=['korail2'],
    version=version,
    description='Korail(www.letskorail.com) wrapper for Python (fork with N-card discount support)',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    license='BSD License',
    author='Changwoo Song',
    author_email='',
    url='https://github.com/ce-dric/korail2',
    keywords=['Korail', 'KTX', 'N-card'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'requests',
        'six',
        'pycryptodome'
    ],
)
