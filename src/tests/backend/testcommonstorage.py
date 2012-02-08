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
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Common descriptors for day to day usage
"""
from datetime import datetime, time
from homer.core import *
from homer.backend import *
from .testdb import BaseTestCase
from unittest import TestCase, skip

class TestDateTypes(BaseTestCase):
    '''Unittests that check if DateTime types serialize properly'''
    
    def testDateTime(self):
        '''Tests for the DateTime Property'''
        @key("name")
        class Person(Model):
            name = String()
            date = DateTime()
            
        person = Person(name = "lob", date = datetime.now())
        person.save()
        
        found = Person.read('lob')
        self.assertEquals(person, found)
        self.assertEquals(person.date, found.date)
        
    def testTime(self):
        '''Tests for the Time Property'''
        @key("name")
        class Person(Model):
            name = String()
            time = Time()
            
        person = Person(name = "lob", time = datetime.now().time())
        person.save()
        
        found = Person.read('lob')
        self.assertEquals(person, found)
        self.assertEquals(person.time, found.time)
        
    
