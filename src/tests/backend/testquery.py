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
import time
import binascii
from homer.core import *
from homer.backend import *
from .testdb import BaseTestCase

class TestCqlQuery(BaseTestCase):
    '''Unittests for CQL Queries'''
 
    def testSanity(self):
        '''Checks if the normal usecase for CQL works as planned'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
        
        book = Book(name = "Pride", author="Anne Rice")
        book.save()
        query = CqlQuery(Book, "SELECT * FROM Book WHERE KEY= :name; ", name="Pride")
        found = query.fetchone()
        self.assertTrue(book == found)
    
    def testMulitpleRows(self):
        '''Checks if CQL repeatedly yields multiple rows'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
        
        for i in range(500):
            book = Book(name = i, author="Anne Rice")
            book.save()
 
        #query = CqlQuery(Book, "SELECT * FROM Book")
        query = CqlQuery(Book, "SELECT * FROM Book WHERE author= :author; ", author=binascii.hexlify("Anne Rice"))
        results = list(query)
        assert(len(results) == 500)
        print "Found Total Results: " , len(results)
 
    def testCount(self):
        '''Shows that count based queries work'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
        
        for i in range(500):
            book = Book(name = i, author="Anne Rice")
            book.save()
 
        query = CqlQuery(Book, "SELECT COUNT(*) FROM Book;")
        result = query.fetchone()
        self.connection.execute("USE Test;")
        self.connection.execute("SELECT COUNT(*) FROM Book;")
        correct = self.connection.fetchone()[0]
        print "Results: ", (result, correct)
        self.assertTrue(result == correct) 

    def testCountForNonExistentModel(self):
        '''Show that counts work for Models that have not been saved'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
 
        query = CqlQuery(Book, "SELECT COUNT(*) FROM Book;")
        result = query.fetchone()
        self.connection.execute("USE Test;")
        self.connection.execute("SELECT COUNT(*) FROM Book;")
        correct = self.connection.fetchone()[0]
        self.assertTrue(result == correct) 
        
   
