from setuptools import setup
from pip.req import parse_requirements

setup(name='falconjsonio',
      version='0.1',
      description='JSON-Schema input and output for Falcon',
      long_description='Declare the input requirements and output specifications of your API using JSON-Schema.',
      url='https://bitbucket.org/garymonson/falcon-json-io',
      author='Gary Monson',
      author_email='gary.monson@gmail.com',
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
      ],
      keywords='json schema falcon',
      packages=['falconjsonio'],
      install_requires=[str(ir.req) for ir in parse_requirements('requirements.txt')],
      zip_safe=False)
