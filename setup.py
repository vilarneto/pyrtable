# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme = ''

setup(
    long_description=readme,
    name='pyrtable',
    version='0.7.3',
    description='Django-inspired library to interface with Airtable',
    python_requires='==3.*,>=3.8.0',
    author='Vilar da Camara Neto',
    author_email='vilarneto@gmail.com',
    license='MIT',
    packages=[
        'pyrtable', 'pyrtable.context', 'pyrtable.fields', 'pyrtable.filters'
    ],
    package_dir={"": "src"},
    package_data={},
    install_requires=[
        'deprecated', 'pytz', 'pyyaml==5.*,>=5.1.0', 'requests==2.*,>=2.22.0',
        'simplejson==3.*,>=3.16.0'
    ],
    extras_require={
        "dev": [
            "click==7.*,>=7.1.2", "ipython", "sphinx==3.*,>=3.0.3",
            "twine==3.*,>=3.3.0"
        ]
    },
)
