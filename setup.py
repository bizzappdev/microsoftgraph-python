from __future__ import absolute_import
import os
from setuptools import setup
from io import open


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name=u'microsoftgraph-python',
      version=u'0.1.3',
      description=u'API wrapper for Microsoft Graph written in Python',
      long_description=read(u'README.md'),
      url=u'https://github.com/GearPlug/microsoftgraph-python',
      author=u'Miguel Ferrer, Nerio Rincon, Yordy Gelvez',
      author_email=u'ingferrermiguel@gmail.com',
      license=u'GPL',
      packages=['microsoftgraph'],
      install_requires=[
          u'requests',
      ],
      zip_safe=False)
