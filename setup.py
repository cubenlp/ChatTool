#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

VERSION = '2.0.0'

requirements = [
    'Click>=7.0', 'requests>=2.20', "responses>=0.23",
    'tqdm>=4.60', 'aiohttp>=3.8', 'tiktoken>=0.4.0']
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
    description="A short wrapper of the Chatapi Toolkit.",
    entry_points={
        'console_scripts': [
            'chatapi_toolkit=chatapi_toolkit.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='chatapi_toolkit',
    name='chatapi_toolkit',
    packages=find_packages(include=['chatapi_toolkit', 'chatapi_toolkit.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/cubenlp/chatapi_toolkit',
    version=VERSION,
    zip_safe=False,
)
