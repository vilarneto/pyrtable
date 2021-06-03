
# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


import os.path

readme = ''
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.rst')
if os.path.exists(readme_path):
    with open(readme_path, 'rb') as stream:
        readme = stream.read().decode('utf8')


setup(
    long_description=readme,
    name='pyrtable',
    version='0.7.13',
    description='Django-inspired library to interface with Airtable',
    python_requires='==3.*,>=3.8.0',
    project_urls={"documentation": "https://pyrtable.readthedocs.io/", "repository": "https://github.com/vilarneto/pyrtable"},
    author='Vilar da Camara Neto',
    author_email='vilarneto@gmail.com',
    license='MIT',
    classifiers=['Development Status :: 4 - Beta', 'Environment :: Console', 'Intended Audience :: Developers', 'License :: OSI Approved :: MIT License', 'Natural Language :: English', 'Operating System :: OS Independent', 'Programming Language :: Python', 'Programming Language :: Python :: 3.8', 'Programming Language :: Python :: 3.9', 'Programming Language :: Python :: Implementation :: CPython', 'Topic :: Software Development'],
    packages=['pyrtable', 'pyrtable.context', 'pyrtable.fields', 'pyrtable.filters'],
    package_dir={"": "src"},
    package_data={},
    install_requires=['deprecated', 'pytz', 'pyyaml==5.*,>=5.1.0', 'requests==2.*,>=2.22.0', 'simplejson==3.*,>=3.16.0'],
)
