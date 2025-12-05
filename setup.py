#!/usr/bin/env python3
"""
SMS Monitor Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# README lesen
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

setup(
    name='sms-monitor',
    version='1.0.0',
    description='SMS-Empfang über USB 4G/LTE Modems mit ModemManager',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='deCASHme',
    author_email='',
    url='https://github.com/deCASHme/opt',
    license='MIT',

    packages=find_packages(),

    python_requires='>=3.7',

    install_requires=[
        'PyGObject>=3.36.0',
    ],

    extras_require={
        'webhooks': ['requests>=2.25.0'],
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.10',
            'black>=21.0',
            'flake8>=3.8',
        ],
    },

    entry_points={
        'console_scripts': [
            'sms-monitor=sms_monitor.cli:main',
        ],
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Communications',
        'Topic :: System :: Hardware',
        'Topic :: Utilities',
    ],

    keywords='sms modem usb lte 4g modemmanager simcom',

    project_urls={
        'Bug Reports': 'https://github.com/deCASHme/opt/issues',
        'Source': 'https://github.com/deCASHme/opt',
    },
)
