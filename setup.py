from setuptools import setup
from pip.req import parse_requirements
from pip.download import PipSession

version = '1.0.1'

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    long_description = open('README.md').read()

setup(name='falconjsonio',
      version=version,
      description='JSON-Schema input and output for Falcon',
      long_description=long_description,
      url='https://bitbucket.org/garymonson/falcon-json-io',
      author='Gary Monson',
      author_email='gary.monson@gmail.com',
      license='MIT',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
      ],
      keywords='json schema falcon',
      packages=['falconjsonio'],
      install_requires=[str(ir.req) for ir in parse_requirements('requirements.txt', session=PipSession())],
      zip_safe=False)
