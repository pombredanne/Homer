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
from homer.backend import RoundRobinPool, Connection, ConnectionDisposedError, Simpson
from unittest import TestCase, skip

class TestRoundRobinPool(TestCase):
    '''Tests a RoundRobin Pool...'''
    
    def setUp(self):
        print "Creating a Pool with the default connections"
        self.pool = RoundRobinPool(DataStoreOptions())
    
    def tearDown(self):
        self.pool.disposeAll()
        
    def testGet(self):
        '''Yields a valid connection to this Keyspace'''
        connection = self.pool.get()
        self.assertTrue(connection is not None)
        self.assertTrue(connection.client is not None)
        self.assertTrue(connection.open)
      
    def testAddress(self):
        '''Returns an address from this servers pool in a round robin fashion'''
        for i in range(5):
            assert self.pool.address().next() == "localhost:9160"
          
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
from homer.core.models import key, Model
from homer.core.commons import *
from homer.options import *

class TestSimpson(TestCase):
    '''Behavioural contract for Simpson'''
    
    def setUp(self):
        '''Create the Simpson instance, we all know and love'''
        self.db = Simpson()
        self.connection = cql.connect("localhost", 9160).cursor()
        
    
    def tearDown(self):
        '''Release resources that have been allocated'''
        try:
            self.connection.execute("DROP KEYSPACE Test;")
            self.connection.close()
        except:
            pass
    
    def testSimpsonOnlyAcceptsModel(self):
        '''Checks if Simpson accepts non models'''
        class Person(object):
            '''An ordinary new-style class'''
            pass
        self.assertRaises(AssertionError, lambda: self.db.create(Person))   
        
    def testCreate(self):
        '''Tests if Simpson.create() actually creates a Keyspace and ColumnFamily in Cassandra'''
        instances = ["localhost:9160",]
        c = DataStoreOptions(servers=instances, username="", password="")
        namespace = Namespace(name= "Test", cassandra= c)
        namespaces.add(namespace)
        namespaces.default = "Test"
        
        @key("name")
        class Person(Model):
            '''An ordinary netizen'''
            name = String("Homer Simpson", indexed = True)
            twitter = URL("http://twitter.com/homer", indexed = True)
            
        self.db.create(Person); #Quantum Leap.
        with self.assertRaises(Exception): # Try to create the wanted keyspace to see if it doesn't exist.
            self.connection.execute("CREATE KEYSPACE Test;"); 
            self.connection.execute("CREATE COLUMNFAMILY Person;");
        
    
