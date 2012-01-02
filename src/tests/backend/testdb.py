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
Tests for the the db module.
"""
import time
from homer.options import options, DataStoreOptions
from homer.backend import RoundRobinPool, Connection, ConnectionDisposedError, Simpson, Level
from unittest import TestCase, skip

class TestRoundRobinPool(TestCase):
    '''Tests a RoundRobin Pool...'''
    
    def setUp(self):
        '''Create the Pool'''
        print "Creating a Pool with the default connections"
        self.pool = RoundRobinPool(DataStoreOptions())
    
    def tearDown(self):
        '''Dispose all alive connections in the Pool'''
        self.pool.disposeAll()
        
    def testGet(self):
        '''Yields a valid connection to this Keyspace'''
        connection = self.pool.get()
        self.assertTrue(connection is not None)
        self.assertTrue(connection.client is not None)
        self.assertTrue(connection.open)
           
    def testPut(self):
        """Returns a Connection to the pool"""
        connection = self.pool.get()
        self.pool.put(connection)
        assert self.pool.queue.qsize() == 1
    
    def testDisposeAll(self):
        '''Disposes all the Connections in the Pool, typically called at System Exit'''
        cons = []
        for i in range(5):
            conn = self.pool.get()
            cons.append(conn)
        for i in cons:
            self.pool.put(i)
        print self.pool.queue.qsize()
        self.pool.disposeAll()
        assert self.pool.queue.qsize() == 0
    
    @skip("Takes to Long to Run..")
    def testEviction(self):
        '''Checks if Idle connections are eventually evicted from the Connection Pool'''
        cons = []
        for i in range(15):
            conn = self.pool.get()
            cons.append(conn)
        for i in cons:
            self.pool.put(i)
        time.sleep(45)
        print self.pool.queue.qsize()
        assert self.pool.queue.qsize() == self.pool.maxIdle

class TestConnection(TestCase):
    '''Integration Tests for Connection'''
    
    def setUp(self):
        self.pool = RoundRobinPool(DataStoreOptions())
    
    def tearDown(self):
        self.pool.disposeAll()
        
    def testClient(self):
        '''Returns the Cassandra.Client Connection that I have'''
        connection = self.pool.get()
        self.assertTrue(connection is not None)
        self.assertTrue(connection.client is not None)
        self.assertTrue(connection.open)
    
    def testCursor(self):
        '''Returns a low level CQL cursor'''
        connection = self.pool.get()
        cursor = connection.cursor()
        self.assertTrue(cursor is not None)
        connection.dispose()
        
    def testToPool(self):
        '''Return this Connection to the Pool where it came from'''
        connection = self.pool.get()
        poolSize = self.pool.queue.qsize()
        connection.toPool()
        self.assertTrue(self.pool.queue.qsize() > poolSize)
       
    def testDispose(self):
        '''Close this connection and mark it as DISPOSED'''
        connection = self.pool.get()
        connection.dispose()
        with self.assertRaises(ConnectionDisposedError):
            connection.client

###
# Tests that use cql to confirm the behaviour of Cassandra.
###

import cql
from homer.core.models import key, Model, Schema, Key, Reference    
from homer.core.commons import *
from homer.options import *

class TestSimpson(TestCase):
    '''Behavioural contract for Simpson'''
    
    def setUp(self):
        '''Create the Simpson instance, we all know and love'''
        self.db = Simpson()
        self.connection = cql.connect("localhost", 9160).cursor()
        # Do Datastore configuration, setup stuff like namespaces and etcetera
        c = DataStoreOptions(servers=["localhost:9160",], username="", password="")
        namespace = Namespace(name= "Test", cassandra= c)
        namespaces.add(namespace)
        namespaces.default = "Test"
          
    def tearDown(self):
        '''Release resources that have been allocated'''
        try:
            self.db.clear()
            Schema.clear()
            self.connection.execute("DROP KEYSPACE Test;")
            self.connection.close()
        except Exception as e:
            print e
    
    def testSimpsonOnlyAcceptsModel(self):
        '''Checks if Simpson accepts non models'''
        class Person(object):
            '''An ordinary new-style class'''
            pass
        self.assertRaises(AssertionError, lambda: self.db.create(Person()))   
      
    def testCreate(self):
        '''Tests if Simpson.create() actually creates a Keyspace and ColumnFamily in Cassandra'''
        @key("name")
        class Person(Model):
            name = String("Homer Simpson", indexed = True)
            twitter = URL("http://twitter.com/homer", indexed = True)
        
        self.db.create(Person()); #=> Quantum Leap; This was the first time I tested my assumptions on Homer
        self.assertRaises(Exception, lambda : self.connection.execute("CREATE KEYSPACE Test;"))
        self.assertRaises(Exception, lambda : self.connection.execute("CREATE COLUMNFAMILY Person;"))
        self.assertRaises(Exception, lambda : self.connection.execute("CREATE INDEX ON Person(twitter);"))
        self.assertRaises(Exception, lambda : self.connection.execute("CREATE INDEX ON Person(name);"))
     
    def testPut(self):
        '''Tests if Simpson.put() actually stores the model to Cassandra'''
        @key("id")
        class Profile(Model):
            id = String(required = True, indexed = True)
            fullname = String(indexed = True)
            bookmarks = Map(String, URL)
            
        cursor = self.connection
        profile = Profile(id = "1234", fullname = "Iroiso Ikpokonte")
        profile.bookmarks["google"] = "http://google.com"
        profile.bookmarks["twitter"] = "http://twitter.com"
        self.db.put(profile)
        cursor.execute("USE Test;")
        cursor.execute("SELECT id, fullname FROM Profile WHERE KEY=1234;")
        self.assertTrue(cursor.rowcount == 1)
        row = cursor.fetchone()
        self.assertTrue(row[0] == "1234" and row[1] == "Iroiso Ikpokonte")
        assert profile.key().complete() == True # Make sure the object has a complete Key
        assert profile.key().saved
    
    def testOtherCommonTypeKeyWork(self):
        '''Shows that keys of other common types work'''
        @key("id")
        class Message(Model):
            id = Integer(indexed = True)
            message = String(indexed = True)
        
        cursor = self.connection
        self.db.put(Message(id=1, message="Something broke damn"))
        cursor.execute("USE Test;")
        cursor.execute("SELECT id, message FROM Message WHERE KEY='1'")
        self.assertTrue(cursor.rowcount == 1)
        row = cursor.fetchone()
        print(row)
        self.assertTrue(row[0] == '1' and row[1] == "Something broke damn")
    
    def testTTL(self):
        '''Tests if put() supports ttl in columns'''
        import time
        
        @key("id")
        class House(Model):
            id = String(required = True, indexed = True)
            fullname = String(indexed = True, ttl = 2)
        
        cursor = self.connection
        profile = House(id = "1234", fullname = "Iroiso Ikpokonte")
        self.db.put(profile)
        time.sleep(3) #=> Sleep for 3 secs and see if you can still find it in the datastore
        cursor.execute("USE Test;")
        cursor.execute("SELECT fullname FROM House WHERE KEY=1234;")
        row = cursor.fetchone()
        self.assertTrue(row[0] == None)
       
    def testRead(self):
        '''Tests if Simpson.read() behaves as usual'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
            isbn = String(indexed = True)
            titles = Map(String, Integer)
        
        book = Book(name="Lord of the Rings", author="J.R.R Tolkein", isbn="12345")
        book.titles["Fellowship of the Rings"] = 10000000000 #Sold a gazillion copies
        self.db.put(book)
        
        k = Key("Test", "Book", "Lord of the Rings")
        #k.columns = ["name", "author", "isbn", "titles"] #We'll specify the columns manually for now
        b = self.db.read(k)[0]
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

    def testDelete(self):
        '''Tests if Simpson.delete() works well'''
        @key("name")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = String(indexed = True)
        
        book = Book(name = "Pride", author="Anne Rice")
        self.db.put(book)
        cursor = self.connection
        cursor.execute("USE Test")
        cursor.execute("SELECT name, author FROM Book WHERE KEY=Pride")
        #print cursor.description
        row = cursor.fetchone()
        self.assertTrue(row[0] == "Pride")
        k = Key('Test', 'Book', 'Pride')
        self.db.delete(k)
        cursor.execute("SELECT name FROM Book WHERE KEY=Pride")
        row = cursor.fetchone()
        print "Deleted row: %s" % row
        self.assertTrue(row[0] == None)

class TestReference(TestCase):
    '''Tests for the Reference Property'''
    
    def setUp(self):
        '''Create the Simpson instance, we all know and love'''
        self.db = Simpson()
        self.connection = cql.connect("localhost", 9160).cursor()
        # Do Datastore configuration, setup stuff like namespaces and etcetera
        b = DataStoreOptions(servers=["localhost:9160",], username="", password="")
        namespace = Namespace(name= "Host", cassandra= b)
        namespaces.add(namespace)
        namespaces.default = "Host"
        
    def tearDown(self):
        '''Release resources that have been allocated'''
        try:
            self.db.clear()
            Schema.clear()
            self.connection.execute("DROP KEYSPACE Host;")
            self.connection.close()
        except:
            pass
            
    def testSanity(self):
        '''Tests the sanity of Reference Property'''
        from homer.core.commons import String
        print "######## Creating Models ################"
        @key("name", namespace = "Host")    
        class Person(Model):
            name = String(required = True)
            
        @key("name", namespace = "Host")
        class Book(Model):
            name = String(required = True, indexed = True)
            author = Reference(Person)
        
        print "Persisting Person"
        person = Person(name = "sasuke")
        self.db.put(person)
        print "Persisting Book"
        book = Book(name = "Pride", author = person)
        self.db.put(book)
        
        print "Checking Conversion Routine"
        k = eval(Book.author.convert(book))
        self.assertTrue(k == Key("Host","Person","sasuke"))
        with self.assertRaises(Exception):
            book.author = "Hello"
        
        with self.assertRaises(Exception):
            author = Person(name = "iroiso")
            book.author = author #Allows only saved keys
        
        print "Checking Automatic Reference Read"
        id = Key("Host","Book","Pride")
        id.columns = ["name", "author"]
        found = self.db.read(id)[0]
        self.assertTrue(found.author.name == "sasuke")
        self.assertTrue(found.author == person)

class TestCqlQuery(TestCase):
    '''Unittests for CQL Queries'''
    def setUp(self):
        '''Create the Simpson instance, we all know and love'''
        self.db = Simpson()
        self.connection = cql.connect("localhost", 9160).cursor()
        # Do Datastore configuration, setup stuff like namespaces and etcetera
        c = DataStoreOptions(servers=["localhost:9160",], username="", password="")
        namespace = Namespace(name= "Test", cassandra= c)
        namespaces.add(namespace)
        namespaces.default = "Test"
             
    def tearDown(self):
        '''Release resources that have been allocated'''
        try:
            self.db.clear()
            Schema.clear()
            self.connection.execute("DROP KEYSPACE Test;")
            self.connection.close()
        except Exception as e:
            print e

    
            
