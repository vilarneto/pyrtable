from setuptools import setup, find_packages


with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='pyrtable',
    version='0.7.3',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/vilarneto/pyrtable.git',
    license='MIT',
    author='Vilar da Camara Neto',
    author_email='vilarneto@gmail.com',
    description='Django-inspired library to interface with Airtable',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
    install_requires=[
        "deprecated",
        "requests>=2.22.0",
        "simplejson>=3.16.0",
    ],
    extras_require={
        "pytz": ["pytz"],
        "yaml": ["pyyaml>=5.1"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development",
    ],
)
