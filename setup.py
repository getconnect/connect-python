# -*- coding: utf-8 -*-

from setuptools import setup
import os

setup_path = os.path.dirname(__file__)
reqs_file = open(os.path.join(setup_path, 'requirements.txt'), 'r')
reqs = reqs_file.readlines()
reqs_file.close()

setup(
    name='connect-client',
    version='0.1.1',
    description='Python client for getconnect.io',
    long_description=open("README.rst").read(),
    url='https://github.com/getconnect/connect-python',
    author='getconnect.io',
    author_email='hello@getconnect.io',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',        
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ],
    keywords='getconnect.io analytics connect',
    packages=['connect'],
    install_requires=reqs
)    