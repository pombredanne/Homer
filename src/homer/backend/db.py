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
import atexit
import itertools
import cPickle as pickle
from contextlib import contextmanager as Context
from threading import Thread, local
from Queue import Queue, Empty, Full

from thrift import Thrift
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

from cql.cursor import Cursor
from cassandra import Cassandra
from cassandra.ttypes import *

from homer.core.builtins import fields
from homer.core.models import Type, Property, Schema

####
# Module Exceptions
####
class ConnectionDisposedError(Exception):
    """A Error that is thrown if you try to use a Connection that has been disposed"""
    pass

class DuplicateError(Exception):
    '''An Exception that is thrown when a duplicate keyspace or column family is detected'''
    pass

class TimedOutException(Exception):
    '''Thrown when requests for new connections timeout'''
    pass

class AllServersUnAvailableError(Exception):
    '''Thrown when all the servers in a particular pool are unavailable'''
    pass
    
####
# Constants
####
__all__ = ["CqlQuery", "Simpson", "Level", ]
POOLED, CHECKEDOUT, DISPOSED = 0, 1, 2
RETRY = 3

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
    
    def fetchone(self):
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
        atexit.register(self.disposeAll)
        
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
        print "Pool Shutdown: Disposing off all the remaining Connections"
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
        socket.setTimeout(pool.timeout * 1000.0)
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
# Utilities
###
def redo(function):
    '''Retries a particular operation for a fixed number of times until it fails'''
    def do(*arguments, **keywords):
        attempts = 1
        while True:
            try:
                print 'Calling: %s; count: %s' % (function.__name__, attempts)
                return function(*arguments, **keywords)
            except Exception, e:
                if not attempts < RETRY:
                    raise e
                attempts += 1
    return do

###
# Cassandra Mapping Section;
###
"""
Simpson:
Provides a **very** simple way to use cassandra from python; It provides 
load balancing, auto failover, connection pooling and its clever enough to 
batch calls so it has very low latency. 
"""
class Simpson(object):
    '''An 'Model' Oriented Interface to Cassandra;'''
    consistency = ConsistencyLevel.ONE
    keyspaces, columnfamilies, pools = set(), set(), dict()
    
    @classmethod
    def create(cls, model):
        """Creates a new ColumnFamily from this Model"""
        from homer.options import namespaces
        from homer.core.models import key, Model
        # OUR GOAL HERE IS TO CREATE CASSANDRA DATA MODELS FROM
        # METADATA GLEANED FROM THESE THE INSTANCE PASSED IN TO
        # THIS METHOD
        assert issubclass(model.__class__, Model),"parameter model: %s must inherit from model" % model
        info = Schema.Get(model) 
        namespace = info[0]
        kind = info[1]
        meta = MetaModel(model)
        pool = cls.pool(namespace)
        with using(pool) as conn:
            meta.makeKeySpace(conn)
            cls.pools[namespace] = pool
            cls.keyspaces.add(namespace)
            meta.makeColumnFamily(conn) 
            meta.makeIndexes(conn)
            cls.columnfamilies.add(kind)
             
    @classmethod
    def put(cls, *Models):
        '''Persists @Models to the datastore, Puts are idempotent'''
        from homer.options import namespaces
        from homer.core.models import key, Model
        # PUT PERSISTS ALL CHANGES IN A MODEL IN A SINGLE BATCH
        # THIS ISOLATES THE FAILURES IN ANY WRITE
        def commit(namespace, mutations):
            '''Stores all the mutations in one batch operation'''
            pool = cls.pool(namespace)
            print 'Committing a single model batch to Cassandra'
            with using(pool) as conn:
                conn.client.set_keyspace(namespace)
                conn.client.batch_mutate(mutations, cls.consistency)    
        # ITERATE THROUGH ALL THE BATCH ALL THE INDIVIDUAL CHANGES.
        for model in Models:
            assert issubclass(model.__class__, Model), "parameter model:\
                %s must inherit from Model" % model
            info = Schema.Get(model)
            namespace = namespaces.get(info[0]).name
            kind = info[1]
            if kind not in cls.columnfamilies:
                cls.create(model)
            meta = MetaModel(model)
            changes = { meta.id() : meta.mutations() }
            commit(namespace, changes)
            model.key().namespace = namespace
            model.key().saved = True
            assert model.key().complete()
           
    @classmethod
    def read(cls, *keys):
        '''Reads @keys from the Datastore;'''
        from homer.options import namespaces
        from homer.core.models import key, Model
        results = []
        # READ HAPPENS KEY BY KEY HERE.
        for key in keys:
            assert key.complete(), "Your key has to be complete"
            print "Reading %s from Cassandra" % key
            id = key.id
            parent = ColumnParent(column_family = key.kind)
            # THE GOAL HERE IS TOO AVOID PULLING ALL THE CONTENTS OF WIDE ROWS
            # OVER THE WIRE WHEN DOING A READ. IF THE CALLER DOES NOT EXPLICITLY
            # SPECIFY THE COLUMNS HE WANTS TO RETREIVE VIA KEY.COLUMNS, SIMPSON
            # SETS IT FOR HIM BY READING ONLY THE DESCRIPTORS THAT THE MODEL
            # CONTAINS BY DEFAULT.
            predicate = None
            if key.columns:
                predicate = SlicePredicate(column_names = key.columns)
            else:
                type = Schema.ClassForModel(key.namespace, key.kind)
                names = fields(type, Property).keys() 
                columns = list(names)
                predicate = SlicePredicate(column_names = columns)
            pool = cls.pool(key.namespace)
            with using(pool) as conn:
                conn.client.set_keyspace(key.namespace)
                coscs = conn.client.get_slice(id, parent, predicate, cls.consistency)
                results.append(MetaModel.fromColumns(key, coscs))
        return results
    
    @classmethod
    def pool(cls, namespace):
        '''Returns or creates a pool for this namespace'''
        from homer.options import namespaces
        from homer.core.models import key, Model
        pool = None
        if namespace not in cls.keyspaces:  
            found = namespaces.get(namespace)                    
            pool = RoundRobinPool(found.cassandra)
            cls.pools[namespace] = pool
        else:
            pool = cls.pools[namespace]
        return pool
        
    @classmethod
    def delete(cls, *keys):
        '''Deletes objects with these keys from the datastore'''
        # A DELETE IS USED FOR DELETING AN INSTANCE OF A CLASS FROM CASSANDRA
        for key in keys:
            assert key.complete(), "Your Key has to be complete to a delete"
            path = ColumnPath(column_family = key.kind)
            clock = int(time.time())
            pool = cls.pool(key.namespace)
            with using(pool) as conn:
                print "DELETING %s FROM CASSANDRA" % key 
                conn.client.set_keyspace(key.namespace)
                conn.client.remove(key.id, path, clock, cls.consistency)
              
    @classmethod
    def clear(cls):
        '''Clears internal state of @this'''
        print 'Clearing internal state of the Datastore Mapper'
        cls.keyspaces.clear()
        cls.columnfamilies.clear()
        cls.pools.clear()
            
##
# MetaModel:
# Transforms {@link Model} instances to Cassandra's native Data Model.
# 'A mix of CQL and Thrift as I see fit...', It is a disposable helper
# class that allows me to mix and match homer's and cassandra datamodel
##
class MetaModel(object):
    '''Changes a Model to Cassandra's DataModel..'''
    def __init__(self, model):
        '''Creates a Transform for this Model'''
        info = Schema.Get(model)
        self.model = model
        self.namespace = info[0]
        self.kind = info[1]
        self.key = info[2]
        self.comment = self.kind.__doc__
        self.fields = model.fields()
    
    def id(self):
        '''Returns the appropriate representation of the key of self.model'''
        return str(self.model.key().id)
    
    @redo   
    def makeKeySpace(self, connection):
        '''Creates a new keyspace from the namespace property of this Model'''
        try:
            connection.client.system_add_keyspace(self.asKeySpace())
        except InvalidRequestException:
            pass #raise DuplicateError("Another Keyspace with this name seems to exist")
    
    @redo       
    def makeColumnFamily(self, connection):
        '''Creates a new column family from the 'kind' property of this Model'''
        from homer.options import namespaces, NetworkTopologyStrategy
        options = namespaces.get(self.namespace)
        try:
            connection.client.set_keyspace(options.name)
            connection.client.system_add_column_family(self.asColumnFamily())
            self.wait(connection)
        except InvalidRequestException as e:
            pass #raise DuplicateError("Another Keyspace with this name seems to exist")
    
    def makeIndexes(self, connection):
        '''Creates Indices for all the indexed properties in the model'''
        from homer.options import namespaces
        options = namespaces.get(self.namespace)
        query = 'CREATE INDEX ON {kind}({name});'
        for name, property in self.fields.items():
            if property.indexed():
                print "Creating index on: %s" % property
                cursor = connection.cursor()
                formatted = query.format(kind = self.kind, name= property.name)
                print formatted
                cursor.execute("USE %s;" % options.name)
                cursor.execute(formatted)
            else:
                print "Cannot index: %s" % property
        self.wait(connection)
                
    def asKeySpace(self):
        '''Returns the native keyspace definition for this object;'''
        from homer.options import namespaces, NetworkTopologyStrategy
        options = namespaces.get(self.namespace)
        assert options is not None, "No configuration options for this keyspace"
        name = options.name
        strategy = options.cassandra.strategy
        package = 'org.apache.cassandra.locator.%s' % strategy
        replication = strategy.factor
        if isinstance(strategy, NetworkTopologyStrategy):
            print "Creating keyspace with %s, %s, %s" % (name, package, strategy.options)
            return KsDef(name, package, strategy.options, replication, [])
        else:
            print "Creating keyspace with %s, %s, " % (name, package)
            return KsDef(name, package, None, replication, [])
      
    def asColumnFamily(self):
        '''Returns the native column family definition for this @Model'''
        from homer.options import namespaces, NetworkTopologyStrategy
        options = namespaces.get(self.namespace)
        assert options is not None, "No configuration options for this keyspace"
        namespace = options.name
        CF = CfDef()
        CF.keyspace = namespace
        CF.name = self.kind
        CF.comment = self.model.__doc__
        def expand(value):
            '''An inline function used to expand db package names'''
            return 'org.apache.cassandra.db.marshal.%s' % value
        CF.comparator_type = expand(self.keyType())
        CF.default_validation_class = expand(self.defaultType())
        CF.key_validation_class = expand(self.keyType())  
        columns = self.getColumnDefinitions()
        CF.column_metadata = columns
        return CF
    
    def getColumnDefinitions(self):
        '''Returns a set of column definitions for each descriptor in this model'''
        def expand(value):
            '''An inline function used to expand db package names'''
            return 'org.apache.cassandra.db.marshal.%s' % value   
        columns = []
        for name,prop in self.fields.items():
            column = ColumnDef()
            column.name = name
            column.validation_class = expand(self.defaultType())
            columns.append(column)
        return columns
           
    def keyType(self):
        '''Returns the Comparator type of the Key Descriptor of this Model'''
        return "UTF8Type"
    
    def defaultType(self):
        '''Returns the default validation class for a particular Model'''
        return "UTF8Type"
    
    def wait(self, conn):
        '''Waits for schema agreement accross the entire cluster'''
        while True:
            versions = conn.client.describe_schema_versions()
            if len(versions) == 1:
                break
            time.sleep(0.10) 
    
    def getColumn(self, name):
        '''Returns a Native Column from a property with this name'''
        column = Column()
        column.name = name
        if name in self.fields:
            property = self.fields[name]
            column.value = property.convert(self.model)  
            ttl = property.ttl
            if ttl:
                column.ttl = ttl
        else: 
            column.value = pickle.dumps(self.model[name]) # Just pickle it over the wire
        column.timestamp = int(time.time())
        return column
    
    @classmethod
    def fromColumns(self, key, coscs):
        '''Creates a Model from a lists of ColumnOrSuperColumns'''
        cls = Schema.ClassForModel(key.namespace, key.kind)
        model = cls()
        for cosc in coscs:
            name = cosc.column.name
            if name in model.fields():
                prop = model.fields()[name]
                prop.deconvert(model, cosc.column.value)
            else:
                value = pickle.loads(cosc.column.value)
                model[name] = value
        return model
         
    def mutations(self):
        '''Returns a {} of mutations that have occurred since last commit'''
        # See Page 151 and Page 78 in the Cassandra Guide.
        mutations = { self.kind : [] }
        differ = self.model.differ
        # Marshalling additions
        print 'Marshalling additions'
        for name in differ.added():
            column = self.getColumn(name) #=> Fetch the Column for this name
            cosc = ColumnOrSuperColumn()
            cosc.column = column
            mutation = Mutation()
            mutation.column_or_supercolumn = cosc
            print mutation
            mutations[self.kind].append(mutation)
        # Marshalling modifications
        for name in differ.modified():
            column = self.getColumn(name) #=> Fetch the Column for this name
            cosc = ColumnOrSuperColumn()
            cosc.column = column
            mutation = Mutation()
            mutation.column_or_supercolumn = cosc
            mutations[self.kind].append(mutation)  
        # Remove all the deleted columns
        print 'Marshalling deletions'
        deletion = Deletion()
        deletion.timestamp = int(time.time())
        predicate = SlicePredicate()
        predicate.column_names = list(differ.deleted())
        deletion.predicate = predicate
        deletions = Mutation()
        deletions.deletion = deletion
        mutations[self.kind].append(deletions) 
        return mutations
        
