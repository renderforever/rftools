#!/usr/bin/env python
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

version = '1.0.0'

setup(name='RFTools',
      version=version,
      description="Set of unix commanline utilities to handle filesequences",
      long_description=README,
      classifiers=[
       
      ],
      keywords='',
      author='renderforever',
      packages=['rftools'],
      scripts = ['bin/rfpack', 'bin/rfunpack', 'bin/rfedit', 'bin/rfformat', 'bin/rfbuild']

)