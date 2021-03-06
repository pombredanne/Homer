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
import cql
from datetime import datetime, time
from homer.core.commons import String, Map, URL, List, Set
from homer.core.models import Model, key, Schema
from homer.backend.db import store
from .testdb import BaseTestCase
from unittest import TestCase, skip

################### MODULE SET UP AND TEARDOWN CODE ############################
def setUpModule():
    '''Remove the side effects of previous modules in homer'''
    try:
        global connection
        connection = cql.connect("localhost", 9160).cursor()
        connection.execute("DROP KEYSPACE Test;")
    except Exception as e:
        print e


def tearDownModule():
    '''Remove this side effects of this module from homer'''
    try:
        global connection
        store.clear()
        Schema.clear()
        connection.execute("DROP KEYSPACE Test;")
        connection.close()
    except Exception as e:
        print e

#################################################################################

########################## TEST DATA MODELS #####################################
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

@key('id')
class User(Model):
    id = String()
    books = List(Book)

@key('id')
class House(Model):
    id = String()
    books = Set(Book)


#################################################################################

############################# UNIT TESTS PROPER #################################
@skip("Passes but requires isolation")
class TestMap(TestCase):
    """Tests for the Map() descriptor"""

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

@skip("Passes but requires isolation")
class TestList(TestCase):
    '''Unittests for the List type'''

    def testAutoModelConversion(self):
        '''Tests that List does auto conversion for Models'''
        user = User(id="1")
        user.books = []
        for i in range(10):
            b = Book(id=i, name=i)
            b.save()
            user.books.append(b)

        user.save()
        found = User.read("1")
        for i in found.books:
            self.assertTrue(isinstance(i,Book))
        self.assertTrue(len(found.books) == 10)
        print user.books

@skip("Passes but requires isolation")
class TestSet(TestCase):
    '''Unittests for the Set type'''
    
    def testAutoModelConversion(self):
        '''Tests that Set does auto conversion for Models'''
        house = House(id="1")
        house.books = set()
        
        for i in range(10):
            b = Book(id=i, name=i)
            b.save()
            house.books.add(b)

        house.save()
        found = House.read("1")
        for i in found.books:
            self.assertTrue(isinstance(i, Book))
        self.assertTrue(len(found.books) == 10)
        print found.books








