"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='clear-skies',
    version='0.3.16',
    description='A microframework for building microservices in the cloud',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cmancone/clearskies',
    author='Conor Mancone',
    author_email='cmancone@gmail.com',
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='setuptools development microservices',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.6",
)
