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
from homer.core.commons import String, Map, URL
from homer.core.models import Model, key
from .testdb import BaseTestCase
from unittest import TestCase, skip

@key('id')
class Book(Model):
    id = String()
    name = String()

@key('id')
class Person(Model):
    id = String()
    bookmarks = Map(String, URL)
    kbookmarks = Map(Book, URL)
    vbookmarks = Map(String, Book)

class TestMap(TestCase):
    """Tests for the Map() descriptor"""
        
    def testMapSanity(self):
        '''Makes sure that Maps are sane'''
        test = Person(id="Hello")
        map = {"Google": "http://google.com", 234: "http://234next.com", 1.345: "http://base.com"}
        test.bookmarks = map
        self.assertTrue(test.bookmarks == {"Google": "http://google.com", 
            "234": "http://234next.com", "1.345": "http://base.com"}
        )
        test.save()
        found = Person.read(str(test.id))
        self.assertTrue(found.bookmarks == {"Google": "http://google.com", 
            "234": "http://234next.com", "1.345": "http://base.com"}
        )

    def testMapDoesValidation(self):
        """Makes sure that Maps do validation"""
        test = Person(id="Hello")
        with self.assertRaises(Exception):
            test.bookmarks["hello"] = 1
            Person.bookmarks.convert(test)

    def testAutoKeyConversion(self):
        '''Checks if automatic conversion works'''
        book = Book(id="book1", name="hello world")
        book.save()

        person = Person(id="1", kbookmarks=dict())
        person.kbookmarks[book] = "http://book1.com"
        person.save()

        found = Person.read("1")
        self.assertEquals(found.kbookmarks, person.kbookmarks)

    def testAutoValueConversion(self):
        '''Checks if automatic conversion works'''
        book = Book(id="book2", name="hello world")
        book.save()

        person = Person(id="1", vbookmarks=dict())
        person.vbookmarks["Hello"] = book
        person.save()

        found = Person.read("1")
        self.assertEquals(found.vbookmarks, person.vbookmarks)
        print "FOUND " +  str(found.vbookmarks)
        self.assertTrue(isinstance(person.vbookmarks['Hello'], Book))


