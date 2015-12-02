# coding: utf-8
from distutils.core import setup

setup(name='uscrape',
      version='0.3',
      description='A set of commonly used functions for small scrapers.',
      author=u'Gašper Žejn'.encode('utf-8'),
      author_email='zejn@owca.info',
      url='https://github.com/zejn/uscrape',
      packages=['uscrape'],
      install_requires=['requests', 'lxml'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          ]
     )
