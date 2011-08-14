#!/usr/bin/env python
#
# Copyright 2011 June Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Author : Iroiso .I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Provides a very nice abstraction around Memcache.

"""
######
# CACHING IMPLEMENTATION
#######
"""
Memcache:
An object oriented interface to Redis that speaks
homer Models, Memcache's interface is very similar
to GAE's memcache.
"""
class Memcached(object):
    '''An 'Model' Oriented Interface to Memcached;'''
    @classmethod
    def Set(cls, *objects):
        '''Put these models in Memcache'''
        pass

