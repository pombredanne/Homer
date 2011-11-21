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
Provides a very nice abstraction around Cassandra; 
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

@Context
def using(Pool):
    '''Fetches an Connection using @Pool and returns after use'''
    connection = Pool.get()
    yield connection
    Pool.put(connection)   

"""
RoundRobinPool:
This provides threadsafe client side load balancing for a Cassandra cluster, 
It reuses addresses that are preconfigured in a round robin fashion.
"""
class RoundRobinPool(Pool):
    '''Implements Load balancing for a Cluster'''
    def __init__(self, options):
        '''Configures a RoundRobinPool with a PoolOption object'''
        self.count = 0
        self.maxConnections = options.size
        self.queue = Queue(options.size)
        self.keyspace = options.keyspace
        self.maxIdle = options.idle
        self.timeout = options.timeout
        self.evictionDelay = options.recycle
        self.servers = options.servers
        self.username = options.username
        self.password = options.password
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
    
###
# Connection:
# A ThreadSafe wrapper around Cassandra.Client which supports connection pooling.
###
class Connection(object):
    """A convenient wrapper around the thrift client interface"""
    def __init__(self, pool, address, keyspace = None, username = None, password = None):
        '''Creates a Cassandra Client internally and initializes it'''
        from homer.options import options
        self.local = local()
        host, port = address.split(":")
        socket = TSocket.TSocket(host, int(port))
        socket.setTimeout(pool.timeout)
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

"""
EvictionThread:
A Thread that periodically looks in a Connection Pool to Evict
excess Idle connections.
"""
class EvictionThread(Thread):
    """Periodically evicts idle connections from the connection pool"""
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
# Cassandra Mapping Section;
###
import time
from homer.core.models import StorageSchema
from cql.cassandra.ttypes import Mutation, Deletion, SlicePredicate, ColumnOrSuperColumn, Column,\
     InvalidRequestException


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
    keyspaces, columnfamilies, pools = set(), set(), dict()
    
    @classmethod
    def create(cls, model):
        from homer.options import Settings
        info = StorageSchema.Get(model) #=> StorageSchema returns meta information.
        namespace = info[0]
        kind = info[1]
        # Create a new keyspace if necessary
        if namespace not in keyspaces:
            print 'Creating Keyspace: %s' % namespace
#           found = Settings.Homer.Pool[namespace]                                  
            pool = RoundRobinPool(found)
            print 'Connecting to Cassandra :)'
            with using(pool) as conn:
                MetaModel(model).makeKeySpace(conn)
            cls.pools[namespace] = pool
            cls.keyspaces.add(namespace)
        # Create a new column family if necessary    
        if kind not in columfamilies:
            print 'Creating ColumnFamily: %s' % kind
            pool = cls.pools[namespace]
            with using(pool) as conn:
                MetaModel(model).makeColumnFamily(conn) #MetaModels should be designed to be disposable.
            cls.columnfamilies.add(kind)
        #Create a indexes if necessary..
           
    @classmethod
    def read(cls, *Keys):
        '''Reads @keys from the Datastore; if @cache check Memcache first'''
        pass
        
    @classmethod
    def put(cls, period, *Models):
        '''Persists @objects to the datastore, put a copy in the cache if cache = True'''
        pass
    
    @classmethod
    def update(cls, *Models):
        '''Updates @Models with values from the DataStore'''
        pass
    
    @classmethod
    def delete(cls, *Models):
        '''Deletes @objects from the datastore, remove copy in cache if cache is True'''
        pass  

##
# MetaModel:
# Transforms {@link Model} instances to Cassandra's native Data Model.
# 'A mix of CQL and Thrift as I see fit...'
##
class MetaModel(object):
    '''Changes a Model to Cassandra's DataModel..'''
    def __init__(self, model):
        '''Creates a Transform for this Model'''
        info = StorageSchema.Get(model)
        self.model = Model
        self.namespace = info[0]
        self.kind = info[1]
        self.keyProperty = info[2]
        self.validity = info[3]
        self.comment = self.kind.__doc__
    
    def makeKeySpace(self, connection):
        '''Creates a new keyspace from the namespace property of this Model'''
        try:
            connection.client.system_add_keyspace(self.asKeySpace())
        except InvalidRequestException:
            pass #Log invalid requests; They mean that there is a duplicate
            
    def makeColumnFamily(self, connection):
        '''Creates a new column family from the 'kind' property of this Model'''
        try:
            connection.client.system_add_column_family(self.asColumnFamily())
        except InvalidRequestException:
            pass #Do nothing about invalid requests; They mean that there is a duplicate
    
    def makeIndices(self, connection):
        '''Creates Indices for all the indexed properties in the model'''
        # This call should work by flipping bits. If Property.indexed == True, index it else unindex it
        pass
        
    def asKeySpace(self):
        '''Returns the native keyspace definition for this object;'''
        result = KsDef(name= self.namespace)
        return result
    
    def asColumnFamily(self):
        '''Returns the native column family definition for this @Model'''
        result = CfDef(keyspace=self.namespace, name= self.model.kind())
        result.comment = self.comment
        return result
    
    def keyType(self):
        '''Returns the Comparator type of the Key Descriptor of this Model'''
        return "UTF8Type"
         
    @property
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
