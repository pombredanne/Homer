#!/usr/bin/python

#       Copyright 2011, June.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup
from os.path import abspath, join, dirname

setup(
    name="homer",
    version="0.9.4",
    description="A Beautiful Python Object Non-Relational Mapper for Cassandra",
    long_description=open(abspath(join(dirname(__file__), 'README.md'))).read(),
    maintainer='Iroiso Ikpokonte',
    maintainer_email='iroiso@live.com',
    package_dir = {'': 'src',},
    url="http://github.com/Junery/Homer.git",
    packages=["homer",],
    provides=["homer"],
    install_requires =["cql==1.0.6", "thrift"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Database :: Front-Ends",
    ],
)
