#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

VERSION = '0.2.0'

requirements = ['Click>=7.0', 'openai>=0.27.0']

test_requirements = ['pytest>=3', 'unittest']

setup(
    author="Rex Wang",
    author_email='1073853456@qq.com',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    description="A short wrapper of the OpenAI api call.",
    entry_points={
        'console_scripts': [
            'openai_api_call=openai_api_call.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='openai_api_call',
    name='openai_api_call',
    packages=find_packages(include=['openai_api_call', 'openai_api_call.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/RexWzh/openai_api_call',
    version=VERSION,
    zip_safe=False,
)
