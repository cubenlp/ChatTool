#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

VERSION = '3.1.7'

requirements = [
    'Click>=7.0', 'requests>=2.20', "responses>=0.23", 'aiohttp>=3.8',
    'tqdm>=4.60', 'docstring_parser>=0.10', "python-dotenv>=0.17.0"]
test_requirements = ['pytest>=3', 'unittest']

setup(
    author="Rex Wang",
    author_email='1073853456@qq.com',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    description="Toolkit for Chat API",
    entry_points={
        'console_scripts': [
            'chattool=chattool.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='chattool',
    name='chattool',
    packages=find_packages(include=['chattool', 'chattool.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/cubenlp/chattool',
    version=VERSION,
    zip_safe=False,
)
