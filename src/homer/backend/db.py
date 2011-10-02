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
Provides a very nice abstraction around Cassandra

"""
import time
import itertools
from contextlib import contextmanager as Context
from threading import Thread, local
from Queue import Queue, Empty, Full

from thrift import Thrift
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

from cql.cursor import Cursor
from cql.cassandra import Cassandra
from cql.cassandra.ttypes import AuthenticationRequest, ConsistencyLevel

__all__ = ["CqlQuery", "Simpson", "Level", ]

POOLED, CHECKEDOUT, DISPOSED = 0, 1, 2

####
# Module Exceptions
####
class ConnectionDisposedError(Exception):
    """A Error that is thrown if you try to use a Connection that has been disposed"""
    pass

class TimedOutException(Exception):
    '''Thrown when requests for new connections timeout'''
    pass

class AllServersUnAvailableError(Exception):
    '''Thrown when all the servers in a particular pool are unavailable'''
    pass

####
# CQL Query Support
####
"""
CqlQuery:
A CqlQuery wraps CQL queries in Cassandra 0.8.+, However it
provides a very distinguishing feature, it automatically
returns query results as Model instances or python types
"""
class CqlQuery(object):
    """ A very nice wrapper around the CQL Query Interface """
    def __init__(self, query, *args, **kwds):
        '''Basic stub'''
        pass
    
    def run(self):
        '''Executes this query, normally this is called automatically'''
        pass
    
    def fetchOne(self):
        '''Returns one result from the query'''
        pass
        
    def __iter__(self):
        '''Yields objects from the query results'''
        pass

####
# Simpson Implementation
####  
"""
Simpson:
Provides a very simple way to use cassandra from python; It provides load balancing,
auto failover, connection pooling and its clever enough to batch calls so it
has very low latency. And one more thing... It automatically implements the
the store and cache pattern, So Gets are lightning fast...
"""
class Simpson(object):
    '''An 'Model' Oriented Interface to Cassandra;'''
    consistency = ConsistencyLevel.ONE
    
    @classmethod
    def create(cls, Model):
        '''Creates Cassandra Equivalent for this Model'''
        pass
    
    @classmethod
    def read(cls, cache, *Keys):
        '''Reads @keys from the Datastore; if @cache check Memcache first'''
        pass
        
    @classmethod
    def put(cls, cache, period, *Models):
        '''Persists @objects to the datastore, put a copy in the cache if cache = True'''
        pass
    
    @classmethod
    def update(cls, *Models):
        '''Updates @Models with values from the DataStore'''
        pass
    
    @classmethod
    def delete(cls, cache, *Models):
        '''Deletes @objects from the datastore, remove copy in cache if cache is True'''
        pass


@Context
def Using(Pool):
    '''Fetches an Connection from @Pool and returns after use'''
    connection = Pool.get()
    yield connection
    Pool.put(connection)   


####
# Controlling Consistency
####     
"""
Consistency:
A Generic Context Manager for dealing with Cassandra's consistency;
It changes the way the Singleton to Cassandra behaves
"""
class Consistency(object):
    '''Generic Context Manager for Simpson'''
    def __init__(self, level):
        '''Basic initialization...'''
        self.level = level
        self.previous = None
        
    def __enter__(self):
        '''Changes the current consistency to self.level'''
        self.previous = Simpson.consistency
        Simpson.consistency = self.level
        
    def __exit__(self, *arguments, **kwds):
        '''Revert the global consistency to the previous setting.'''
        Simpson.consistency = self.previous

'''
Level:
Allows you to Manage the Global Consistency Level of the Module.
i.e.

with Level.Quorum:
    # Do some stuff here.
    
with Level.All:
    # Do some highly consistent thing here.
    
'''
class Level(object):
    '''Manages Different Consistency Levels'''
    Any = Consistency(ConsistencyLevel.ANY)
    All = Consistency(ConsistencyLevel.ALL)
    Quorum = Consistency(ConsistencyLevel.QUORUM)
    One = Consistency(ConsistencyLevel.ONE)
    Two = Consistency(ConsistencyLevel.TWO)
    Three = Consistency(ConsistencyLevel.THREE)
    LocalQuorum = Consistency(ConsistencyLevel.LOCAL_QUORUM)
    EachQuorum = Consistency(ConsistencyLevel.EACH_QUORUM)

#####
# Connection and Pooling 
#####    
"""
Pool:
A pool provides autofailover and loadbalancing automatically
for connections to the db or the cache.
"""
class Pool(object):
    '''Implements Load balancing for a Cluster'''
    
    def get(self):
        '''Yields a valid connection to this Keyspace'''
        raise NotImplementedError
        
    def put(self, connection):
        """Returns a Connection from the pool"""
        raise NotImplementedError
    
    def disposeAll(self):
        '''Clears all the connections in this Pool'''
        raise NotImplementedError


"""
RoundRobinPool:
This provides threadsafe client side load balancing for a Cassandra cluster, 
is created it reads configuration from the options and creates a pool of open 
connections which it reuses;

"""
class RoundRobinPool(Pool):
    '''Implements Load balancing for a Cluster'''
    def __init__(self, options):
        '''Configures a RoundRobinPool with a PoolOption object'''
        self.count = 0
        self.maxConnections = options.Size
        self.queue = Queue(options.Size)
        self.keyspace = options.Namespace
        self.maxIdle = options.MaxIdle
        self.timeout = options.Timeout
        self.evictionDelay = options.EvictionDelay
        self.servers = options.Servers
        self.username = options.Username
        self.password = options.Password
        self.evictionThread = EvictionThread(self, self.maxIdle, self.evictionDelay)
        
    def get(self):
        '''Yields a valid connection to this Keyspace'''
        try:
            return self.queue.get(False)
        except Empty:
            if self.count < self.maxConnections:  #If we are under quota just create a new connection
                addr = self.address().next()
                print "Creating a new connection to address: %s" % addr
                connection = Connection(self, addr, self.keyspace, self.username, self.password)
                self.count += 1
                return connection
            else:  # If we are over quota force the request to wait for @self.timeout
                try:
                    return self.queue.get(True, self.timeout)
                except Empty: raise TimedOutException("Sorry, your request has Timed Out")
      
    def address(self):
        '''Returns an address from this servers pool in a round robin fashion'''
        for addr in itertools.cycle(self.servers):
            yield addr
          
    def put(self, connection):
        """Returns a Connection to the pool"""
        try:
            if connection.state == CHECKEDOUT:
                self.queue.put(connection)
                connection.state == POOLED       
        except Full:
            connection.dispose()
    
    def disposeAll(self):
        '''Disposes all the Connections in the Pool, typically called at System Exit'''
        while True:
            try:
                connection = self.queue.get(False)
                connection.dispose()
            except Empty:
                break
    
"""
EvictionThread:
A Thread that periodically looks in a Connection Pool to Evict
excess Idle connections.
"""
class EvictionThread(Thread):
    def __init__(self, pool, maxIdle, delay):
        from homer.options import options
        super(EvictionThread, self).__init__()
        self.pool = pool
        self.maxIdle = maxIdle
        self.delay = delay
        self.name = "EVICTION-THREAD: %s" % pool.keyspace
        self.log = options.logger(self.name)
        self.daemon = True
        self.start()
        
    def run(self):
        """Evicts Idle Connections periodically from a Connection Pool"""
        while True:
            if not self.pool.queue.qsize() <= self.maxIdle:
                self.log.info("Evicting Idle Connections")
                connection = self.pool.queue.get(False)
                connection.dispose()
                time.sleep(self.delay/1000)
                

###
# Connection:
# A ThreadSafe wrapper around Cassandra.Client which 
# supports connection pooling.
###
class Connection(object):
    """A convenient wrapper around the thrift client interface"""
    def __init__(self, pool, address, keyspace = None, username = None, password = None, timeout = 3*1000):
        '''Creates a Cassandra Client internally and initializes it'''
        from homer.options import options
        self.local = local()
        host, port = address.split(":")
        socket = TSocket.TSocket(host, int(port))
        socket.setTimeout(timeout)
        # Local Variables
        self.transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocolAccelerated(self.transport)
        self.local.pipe = Cassandra.Client(protocol)
        self.address = address
        self.state = CHECKEDOUT
        self.pool = pool
        self.log = options.logger("Connection for Address: %s" % self.address)
        self.transport.open()
        self.open = True
        self.keyspace = keyspace
        self.client.set_keyspace(keyspace)
        if username and password:
            request = AuthenticationRequest(credentials = {"username": username, "password": password})
            self.client.login(request)
    
    @property      
    def client(self):
        '''Returns the Cassandra.Client Connection that I have'''
        if self.state == CHECKEDOUT and self.open:
            return self.local.pipe
        raise ConnectionDisposedError("This Connection has already been Disposed")
    
    def cursor(self):
        '''Returns a low level CQL cursor'''
        return Cursor(self)
            
    def toPool(self):
        '''Return this Connection to the Pool where it came from'''
        try:
            self.pool.put(self)
        except e:
            self.log.error("Exception occurred when adding to Pool: %s " % str(e))
           
    def dispose(self):
        '''Close this connection and mark it as DISPOSED'''
        if self.open:
            self.transport.close()
            self.pool.count -= 1
            self.state = DISPOSED
            self.open = False

###
# Cassandra Mapping Section;
###
import time
from cql.cassandra.ttypes import Mutation, Deletion, SlicePredicate, ColumnOrSuperColumn, Column     

##
# MetaModel:
# Transforms Models to the Cassandra's Data Model.
##
class MetaModel(object):
    '''Changes a Model to Cassandra's DataModel..'''
    
    def __init__(self, Model):
        '''Creates a Transform for this Model'''
        self.model = Model
    
    def mutations(self):
        '''Creates Mutations from the changes that has occurred to this Model since the last commit'''
        ## Expected Results and Constants ##
        mutations = {}
        key = self.key(); name = self.name(); when = time.time()
        differ = self.model.differ
        mutations[key] = { name : [] }
        mutationList =  mutations[key][name]
        ## Marshal Deletions from the Differ ##
        print "Marshalling Deletions from the Model"
        affectedColumns = list(differ.deleted)
        pred = SlicePredicate(column_names = affectedColumns)
        deletes = Mutation(deletion = Deletion(timestamp = when, predicate = pred))
        mutationList.append(deletes)
        ## Marshal Modifications from the Differ ##
        print "Marshalling Modifications from the Model"
        for name in differ.modified:
            column = self.toColumn(name)
            cosc = ColumnOrSuperColumn(column= column)
            mutation = Mutation(column_or_supercolumn = cosc)
            mutationList.append(mutation)
        ## Marshall Additions
        print "Marshalling Additions from the Model"
        for name in differ.added:
            column = self.toColumn(name)
            cosc = ColumnOrSuperColumn(column= column)
            mutation = Mutation(column_or_supercolumn = cosc)
            mutationList.append(mutation)
        return mutations 
