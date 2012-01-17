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
from homer.core import *
from homer.backend import *
from .testdb import BaseTestCase


class TestModel(BaseTestCase):
    '''Tests if the persistence properties of a Model works'''
    
    def testSave(self):
        '''Shows that save works'''
        @key("id")
        class Profile(Model):
            id = String(required = True, indexed = True)
            fullname = String(indexed = True)
            bookmarks = Map(String, URL)
            
        cursor = self.connection
        profile = Profile(id = "1234", fullname = "Iroiso Ikpokonte")
        profile.bookmarks["google"] = "http://google.com"
        profile.bookmarks["twitter"] = "http://twitter.com"
        profile.save() # Save to the datastore
        cursor.execute("USE Test;")
        cursor.execute("SELECT id, fullname FROM Profile WHERE KEY=1234;")
        self.assertTrue(cursor.rowcount == 1)
        row = cursor.fetchone()
        self.assertTrue(row[0] == "1234" and row[1] == "Iroiso Ikpokonte")
        assert profile.key().complete() == True # Make sure the object has a complete Key
        assert profile.key().saved == True
    
    def testCount(self):
        '''Shows that Model counts work'''
        import time
        import uuid
        
        @key("id")
        class Profile(Model):
            id = String(required = True, indexed = True)
            fullname = String(indexed = True)
            bookmarks = Map(String, URL)   
        
        profile = Profile(id = str(uuid.uuid4()), fullname = "Iroiso Ikpokonte")
        profile.save()
       
        l = []
        for i in range(500):
            profile = Profile(id = str(i), fullname = "Iroiso Ikpokonte")
            profile.bookmarks["google"] = "http://google.com"
            profile.bookmarks["twitter"] = "http://twitter.com"
            l.append(profile)
        
        start = time.time()
        with Level.All:
            self.db.putbatch("Test",*l)
        self.assertTrue(Profile.count() == 501)
                  
    def testDelete(self):
        '''Shows that deletes work as expected'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
        
        book = Book(name = "Pride", author="Anne Rice")
        book.save()
        cursor = self.connection
        cursor.execute("USE Test")
        cursor.execute("SELECT name, author FROM Book WHERE KEY=Pride")
        # print cursor.description
        row = cursor.fetchone()
        self.assertTrue(row[0] == "Pride")
        Book.delete('Pride')
        cursor.execute("SELECT name FROM Book WHERE KEY=Pride")
        row = cursor.fetchone()
        print "Deleted row: %s" % row
        self.assertTrue(row[0] == None)

    def testRead(self):
        '''Shows that reads work'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
            isbn = String(indexed = True)
            titles = Map(String, Integer)
        
        book = Book(name="Lord of the Rings", author="J.R.R Tolkein", isbn="12345")
        book.titles["Fellowship of the Rings"] = 10000000000 #Sold a gazillion copies
        book.save()
       
        b = Book.read('Lord of the Rings')
        assert isinstance(b, Book)
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
        print b.name
        print b.author
        print b.isbn
        self.assertTrue(b == book)
        self.assertTrue(b.name == "Lord of the Rings")
        self.assertTrue(b.author == "J.R.R Tolkein")
        self.assertTrue(b.isbn == "12345")
        self.assertTrue(b.titles["Fellowship of the Rings"] == 10000000000)
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    
    def testQuery(self):
        '''Shows that CQL Queries work'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
            isbn = String(indexed = True)
            titles = Map(String, Integer)
        
        book = Book(name="Lord of the Rings", author="J.R.R Tolkein", isbn="12345")
        book.titles["Fellowship of the Rings"] = 10000000000 #Sold a gazillion copies
        book.save()
       
        b = Book.query('WHERE author=:author', author='J.R.R Tolkein').fetchone()
        assert isinstance(b, Book)
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
        print b.name
        print b.author
        print b.isbn
        self.assertTrue(b == book)
        self.assertTrue(b.name == "Lord of the Rings")
        self.assertTrue(b.author == "J.R.R Tolkein")
        self.assertTrue(b.isbn == "12345")
        self.assertTrue(b.titles["Fellowship of the Rings"] == 10000000000)
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"

