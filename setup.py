"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='zendesk-downloader',
    version='1.0.0',
    description='Download attachments from Zendesk cases',
    long_description=long_description,
    url='https://github.com/nmitchell-cumulus/zendesk-downloader',
    author='Nick Mitchell',
    author_email='nmitchell@cumulusnetworks.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='zendesk download',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['docopt', 'PyYAML', 'requests'],
)
