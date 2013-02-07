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
import re
import time
import atexit
import codecs
import binascii
import logging
import itertools
import cPickle as pickle
from copy import deepcopy
from functools import wraps
from traceback import print_exc
from contextlib import contextmanager as Context
from threading import Thread, local, RLock
from Queue import Queue, Empty, Full

from thrift import Thrift
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

from cql.cursor import Cursor
from cql.cassandra import Cassandra
from cql.cassandra.ttypes import *

from homer.core.builtins import fields
from homer.core.models import Type, Property, Schema
from homer.options import CONFIG, Settings

# MODULE EXCEPTIONS
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

class InvalidNamespaceError(Exception):
    '''Thrown to show that there is a problem with the current Namespace in use'''
    pass

class ConfigurationError(Exception):
    '''Thrown to signal that Homer was not configured properly'''
    pass

# SHARED STATE
LOCK = RLock()
POOLS = dict()
KEYSPACES = set()
COLUMNFAMILIES = set()


# CONSTANTS
__all__ = ["CqlQuery", "Lisa", "Level", "FetchMode", "RoundRobinPool",\
                "Connection", "ConnectionDisposedError", "store"]
POOLED, CHECKEDOUT, DISPOSED = 0, 1, 2
RETRY = 3
FETCHSIZE = 2000000000 #AT MOST THE DB MODULE WILL TRY TO READ ALL THE COLUMNS
encoder = codecs.getencoder('utf-8')
encode = lambda content: encoder(content)[0]


# UTILITIES AND HELPER FUNCTIONS
def redo(function):
    '''Retries a particular operation for a fixed number of times until it fails'''
    @wraps(function)
    def do(*arguments, **keywords):
        attempts = 1
        while True:
            try:
                logging.debug('Calling: %s; count: %s' % (function.__name__, attempts))
                return function(*arguments, **keywords)
            except Exception, e:
                if not attempts < RETRY:
                    raise e
                attempts += 1
    return do


"""
optionsFor:
This returns a configuration option for a namespace if it exists
or else it returns the options for the default namespace. If there
is no default namespace then it throws a ConfigurationError
"""
def optionsFor(namespace):
    '''Returns configuration for a namespace or the default'''
    found = None
    if namespace not in CONFIG.NAMESPACES:
        found = CONFIG.NAMESPACES.get(CONFIG.DEFAULT_NAMESPACE, None)
        found = deepcopy(found)
        found['keyspace'] = namespace
    else:
        found = CONFIG.NAMESPACES[namespace]
    if not found:
        raise ConfigurationError("No default namespace configured")
    return found

def poolFor(namespace):
    '''Returns or creates a new ConnectionPool for this namespace'''
    pool = None
    if namespace not in POOLS:
        found = optionsFor(namespace)             
        pool = RoundRobinPool(found)
        with LOCK:
            POOLS[namespace] = pool
    else:
        with LOCK:
            pool = POOLS[namespace]
    return pool   


# CONTROLLING CONSISTENCY   
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
        self.previous = Lisa.consistency
        Lisa.consistency = self.level
        
    def __exit__(self, *arguments, **kwds):
        '''Revert the global consistency to the previous setting.'''
        Lisa.consistency = self.previous

'''
Level:
Allows you to Manage the Global Consistency Level of the Module,
Consistency levels are threadlocal, which makes sense.
i.e.

with Level.Quorum:
    # Do some stuff here.
    
with Level.All:
    # Do some highly consistent thing here.
    
'''
class Level(local):
    '''Manages Different Consistency Levels'''
    Any = Consistency(ConsistencyLevel.ANY)
    All = Consistency(ConsistencyLevel.ALL)
    Quorum = Consistency(ConsistencyLevel.QUORUM)
    One = Consistency(ConsistencyLevel.ONE)
    Two = Consistency(ConsistencyLevel.TWO)
    Three = Consistency(ConsistencyLevel.THREE)
    LocalQuorum = Consistency(ConsistencyLevel.LOCAL_QUORUM)
    EachQuorum = Consistency(ConsistencyLevel.EACH_QUORUM)


# CONNECTIONS AND POOLING   
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
        self.maxConnections = options['size']
        self.queue = Queue(options['size'])
        self.keyspace = options['keyspace']
        self.maxIdle = options['idle']
        self.timeout = options['timeout']
        self.evictionDelay = options['recycle']
        self.servers = options['servers']
        self.username = options['username']
        self.password = options['password']
        self.evictionThread = EvictionThread(self, self.maxIdle, self.evictionDelay)
        self.cycle = None
        self.lock = RLock()
        atexit.register(self.disposeAll)
        
    def get(self):
        '''Yields a valid connection to this Keyspace, in a Thread safe way'''
        with self.lock:
            try:
                return self.queue.get(False)
            except Empty:
                #IF WE ARE UNDER QUOTA JUST CREATE A NEW CONNECTION
                if self.count < self.maxConnections:  
                    addr = self.__address().next()
                    logging.info("Creating a new connection to address: %s" % addr)
                    connection = Connection(self, addr, \
                        self.keyspace, self.username, self.password)
                    self.count += 1
                    return connection
                # IF WE ARE OVER QUOTA FORCE THE REQUEST TO WAIT FOR @self.timeout
                else:  
                    try:
                        return self.queue.get(True, self.timeout)
                    except Empty: raise TimedOutException("Sorry, your request has Timed Out")
          
    def __address(self):
        '''Returns an address from this servers pool in a round robin fashion'''
        # THIS CALL IS NOT THREADSAFE, IT IS FOR INTERNAL USE ONLY.
        if not self.cycle:
            self.cycle = itertools.cycle(self.servers)
        for addr in self.cycle:
            yield addr
          
    def put(self, connection):
        """Returns a Connection to the pool in a threadsafe way"""
        with self.lock:
            try:
                if connection.state == CHECKEDOUT:
                    self.queue.put(connection)
                    connection.state == POOLED       
            except Full:
                connection.dispose()
    
    def disposeAll(self):
        '''Disposes all the Connections in the Pool, typically called at System Exit'''
        with self.lock:
            logging.info("Pool Shutdown: Disposing: the %s remaining Connections" % self.queue.qsize())
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
class Connection(local):
    """A convenient wrapper around the thrift client interface"""
    def __init__(self, pool, address, keyspace = None, username = None, password = None):
        '''Creates a Cassandra Client internally and initializes it'''
        from homer.options import Settings as options
        host, port = address.split(":")
        socket = TSocket.TSocket(host, int(port))
        socket.setTimeout(pool.timeout * 1000.0)
        # Local Variables
        self.transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocolAccelerated(self.transport)
        self.pipe = Cassandra.Client(protocol)
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
            return self.pipe
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
        from homer.options import Settings as options
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
                self.log.info("Evicting Idle Connections, Queue Size: %s" % self.pool.queue.qsize())
                connection = self.pool.queue.get(False)
                connection.dispose()
                time.sleep(self.delay/1000)

###
# Cassandra Mapping Section;
###

"""
FetchMode:
Specifies how you want read behavior to be
"""
class FetchMode(object):
    Property, All = 1, 2

####
# CQL Query Support
####
"""
CqlQuery:
A CqlQuery wraps CQL queries in Cassandra 1.0.+, However it
provides a very distinguishing feature, it automatically
returns query results as models.
"""
class CqlQuery(object):
    """ A very nice wrapper around the CQL query interface """
    pattern = re.compile(r'COUNT\(.+\)', re.IGNORECASE | re.DOTALL) #

    def __init__(self, kind, query, **keywords):
        '''Initialize constructor parameters '''
        from homer.core.models import key, BaseModel
        assert isinstance(kind, type), "%s must be a class" % kind
        assert issubclass(kind, BaseModel), "%s must be a subclass of BaseModel" % kind
        self.kind = kind
        self.convert = False
        self.keyspace = None
        self.query = query
        self.keywords = keywords
        self.cursor = None
        self.count = False
    
    def parse(self, keywords):
        '''Uses the descriptors in the Model to convert keywords'''
        if not self.convert:
            return keywords

        converted = {}
        props = fields(self.kind, Property)
        for name, value in keywords.items():
            converter = props.get(name, None)
            if converter:
                value = converter.convert(value)
                if not isinstance(value, basestring):
                    value = str(value)
                converted[name] = encode(value)
            else:
                T, V = self.kind.default
                value = V.convert(value)
                if not isinstance(value, basestring):
                    value = str(value)
                converted[name] = encode(value)
        return converted

    def execute(self):
        '''Executes @self.query in self.keyspace and returns a cursor'''
        # FIGURE OUT WHICH KEYSPACE THE MODEL BELONGS TO
        if not self.keyspace:
            found = Schema.Get(self.kind)[0]
            self.keyspace = found
        
        logging.info("Executing Query: %s in %s" % (self.query, self.keyspace))
        if not self.kind.__name__ in COLUMNFAMILIES and Settings.DEBUG:
            logging.info("Creating new Column Family: %s " % self.kind.__name__)
            Lisa.create(self.kind())
               
        pool = poolFor(self.keyspace)
        with using(pool) as conn:
            logging.info("Executing %s" % self)
            conn.client.set_keyspace(self.keyspace)
            cursor = conn.cursor()
            
            keywords = self.keywords
            if self.convert:
                logging.info("Converting parameters for query: %s" % self.query)
                keywords = self.parse(keywords)
            cursor.execute(self.query, dict(keywords))
            self.cursor = cursor
          
    def __iter__(self):
        '''Execute your queries and converts data to python data models'''
        # EXECUTE THE QUERY IF IT HASN'T BEEN EXECUTED
        try:
            if self.cursor is None: 
                self.execute() 
        except Exception as e:
            logging.exception("Something wen't wrong when executing the query: %s, error: %s" % self, str(e))

        # FOR SOME ODD REASON CASSANDRA 1.0.0 ALWAYS RETURNS CqlResultType.ROWS, 
        # SO TO FIGURE OUT COUNTS I MANUALLY SEARCH THE QUERY WITH A REGEX

        if re.search(self.pattern, self.query):
            logging.info("Count expression found;")
            yield self.cursor.fetchone()[0]
        else:
            logging.info("Deciphering rows as usual")
            cursor = self.cursor
            description = self.cursor.description
            if not description:
                raise StopIteration
            names = [tuple[0] for tuple in description]
            row = cursor.fetchone()
            while row:
                model = self.kind()
                descs = fields(model, Property)
                values = {}
                for name, value in zip(names, row):
                    if not value: continue
                    if name == "KEY": continue #Ignore the KEY attribute
                    prop = descs.get(name, None)
                    if prop:
                        found = prop.deconvert(value)
                        model[name] = found
                    else:
                        k, v = model.default
                        k = k() if isinstance(k, type) else k
                        v = v() if isinstance(v, type) else v
                        name = k.deconvert(value)
                        value = v.deconvert(value)
                        model[name] = value
                yield model
                row = cursor.fetchone()
    
    def fetchone(self):
        '''Returns just one result'''
        try:
            return iter(self).next()
        except:
            return None
                             
    def __str__(self):
        '''String representation of a CQLQuery.'''
        return "CqlQuery: %s" % self.query
    
'''
Lisa:
A Smarter, Neater and Simpler way to Use Cassandra.

#PROPERTY
albert = Key("June", "Staff", "albert")
name = Lisa.readColumn(String, albert, "name")
print "Just fetched the name property: %s" % name

with Level.One:
    Lisa.saveColumn(String, key, "surname", "dumbledore")
    print "Finished Writing Successfully

gbodi = Key("June", "Staff", "gbodi")
arguments = [(String, albert, "surname"), (Integer, gbodi, "age")]
results = Lisa.readManyColumns(arguments) # Read albert's surname and gbodi's age
print "Albert's surname is: %s and Gbodi's age is: %s" % results[0], results[1]

# MODEL OBJECTS.
'''
class Lisa(local):
    '''A Neater and simpler interface to Cassandra'''
    consistency = ConsistencyLevel.ONE #Consistency level for this copy of Lisa.

    @staticmethod
    def create(model):
        """Creates a new ColumnFamily from this Model"""
        from homer.core.models import key, Model
        global KEYSPACES, COLUMNFAMILIES
        model = model if isinstance(model, type) else model.__class__
        assert issubclass(model, Model),"%s must inherit from Model" % model
        info = Schema.Get(model) 
        namespace = info[0]
        kind = info[1]
        meta = MetaModel(model)
        pool = poolFor(namespace)
        try:
            with using(pool) as conn:
                if namespace not in KEYSPACES:
                    logging.info("Trying to create keyspace: %s" % meta.namespace)
                    meta.makeKeySpace(conn)
                    with LOCK:
                        logging.info("Adding keyspace: %s to global records" % namespace)
                        KEYSPACES.add(namespace)
                if kind not in COLUMNFAMILIES:
                    meta.makeColumnFamily(conn) 
                    meta.makeIndexes(conn)
                    with LOCK:
                        COLUMNFAMILIES.add(kind)
        except:
            print_exc();

    @classmethod
    def readColumn(clasz, key, name):
        '''Read a particular property to the column specified via @key'''
        assert key.iscomplete(), "Your key must be complete, before you can do reads"
        pool = poolFor(key.namespace)
        path = ColumnPath(column_family=key.kind, column=name)
        cosc = None
        with using(pool) as conn:
            conn.client.set_keyspace(key.namespace)
            cosc = conn.client.get(key.id, path, clasz.consistency)
        column = cosc.column
        return column.value
        
    
    @classmethod
    def saveColumn(clasz, key, name, value, ttl=None):
        '''Write a particular property to the column specified via @key'''
        assert key.iscomplete(), "Your key must be complete before you can do writes"
        pool = poolFor(key.namespace)
        timestamp = time.time()
        parent = ColumnParent(column_family=key.kind)
        column = Column(name=name, value=value, timestamp=timestamp)
        if ttl:
            column.ttl = ttl
        cosc = None
        with using(pool) as conn:
            conn.client.set_keyspace(key.namespace)
            conn.client.insert(key.id, parent, column, clasz.consistency)
        

    @classmethod
    def deleteColumn(clasz, key, name):
        '''Delete the property specified by @key'''
        assert key.iscomplete(), "Your key must be complete before you can do writes"
        pool = poolFor(key.namespace)
        timestamp = time.time()
        path = ColumnPath(column_family=key.kind, column=name)
        with using(pool) as conn:
            conn.client.set_keyspace(key.namespace)
            cosc = conn.client.remove(key.id, path, timestamp, clasz.consistency)
     

    @classmethod
    def readManyColumns(clasz, namespace, kind, id, *arguments):
        '''Read various properties from one Model arguments: [name, name, name]'''
        assert namespace and kind and id, "specify namespace, kind, id"
        assert namespace and kind, "You must specify; namespace, kind"
        pool = poolFor(namespace)
        predicate = SlicePredicate(column_names=arguments)
        parent = ColumnParent(column_family=kind)
        result = None
        with using(pool) as conn:
            conn.client.set_keyspace(namespace)
            results = conn.client.get_slice(id, parent, predicate, clasz.consistency)
        for cosc in results:
            column = cosc.column
            yield column.name, column.value
      

    @classmethod
    def saveManyColumns(clasz, namespace, kind, id, *arguments):
        '''Write a lot of properties in one batch, arguments: [(name, value)]'''
        # See Page 151 and Page 78 in the Cassandra Guide.
        assert namespace and kind and id, 'specify arguments namespace, kind, id'
        mutations = { kind : [] }
        for tuple in arguments:
            column = Column()
            column.name = tuple[0]
            column.value = tuple[1]
            column.timestamp = time.time()
            cosc = ColumnOrSuperColumn()
            cosc.column = column
            mutation = Mutation()
            mutation.column_or_supercolumn = cosc
            mutations[kind].append(mutation)
        changes = {id : mutations}
        pool = poolFor(namespace)
        with using(pool) as conn:
            conn.client.set_keyspace(namespace)
            conn.client.batch_mutate(changes, clasz.consistency)
        

    @classmethod
    def deleteManyColumns(clasz, namespace, kind, id, *arguments):
        '''Delete a lot of properties in one batch, arguments: ["name", "name"]'''
        assert namespace and kind and id, 'specify arguments namespace, kind, id'
        mutations = { kind : [] }
        deletion = Deletion()
        deletion.timestamp = int(time.time())
        predicate = SlicePredicate()
        predicate.column_names = arguments
        deletion.predicate = predicate
        deletions = Mutation()
        deletions.deletion = deletion
        mutations[kind].append(deletions)
        changes = {id : mutations}
        pool = poolFor(namespace)
        with using(pool) as conn:
            conn.client.set_keyspace(namespace)
            conn.client.batch_mutate(changes, clasz.consistency)

   
    @classmethod
    def read(clasz, key, fetchmode=FetchMode.Property):
        '''Read a Model from Cassandra'''
        assert key and fetchmode, "specify key and fetchmode"
        assert key.complete(), "your key has to be complete"
        parent = ColumnParent(column_family = key.kind)
        predicate = None
        if fetchmode == FetchMode.Property:
            if key.columns:
                predicate = SlicePredicate(column_names = key.columns)
            else:
                type = Schema.ClassForModel(key.namespace, key.kind)
                names = fields(type, Property).keys() 
                columns = list(names)
                predicate = SlicePredicate(column_names = columns)
        elif fetchmode == FetchMode.All:
            range = SliceRange(start='', finish='', count = FETCHSIZE )
            predicate = SlicePredicate(slice_range=range)       
        found = None
        pool = poolFor(key.namespace)
        with using(pool) as conn:
            conn.client.set_keyspace(key.namespace)
            coscs = conn.client.get_slice(key.id, parent, predicate, clasz.consistency)
            found = MetaModel.load(key, coscs)
        return found    

    
    @classmethod
    def save(clasz, model):
        '''Write one Model to Cassandra'''
        from homer.core.models import key, BaseModel
        # PUT PERSISTS ALL CHANGES IN A MODEL IN A SINGLE BATCH
        def commit(namespace, mutations):
            '''Stores all the mutations in one batch operation'''
            pool = poolFor(namespace)
            with using(pool) as conn:
                conn.client.set_keyspace(namespace)
                conn.client.batch_mutate(mutations, clasz.consistency)    
        assert issubclass(model.__class__, BaseModel), "%s must inherit from BaseModel" % model
        info = Schema.Get(model)
        namespace = info[0]
        kind = info[1]
        if kind not in COLUMNFAMILIES and Settings.DEBUG:
            Lisa.create(model)
        meta = MetaModel(model)
        changes = { meta.id() : meta.mutations() }
        commit(namespace, changes)
        key = model.key()
        key.saved = True
            
    @classmethod
    def delete(clasz, *keys):
        '''Deletes a List of keys which represents Models'''
        for key in keys:
            assert key.complete(), "Your Key has to be complete to a delete"
            path = ColumnPath(column_family = key.kind)
            clock = time.time()
            pool = poolFor(key.namespace)
            with using(pool) as conn:
                logging.info("DELETING %s FROM CASSANDRA" % key )
                conn.client.set_keyspace(key.namespace)
                conn.client.remove(key.id, path, clock, clasz.consistency)

    
    @classmethod
    def saveMany(clasz, namespace, *models):
        '''Write a Lot of Models in one batch, They must all belong to one keyspace'''
        from homer.core.models import key, BaseModel
        # PERSISTS ALL CHANGES IN *MODELS IN A SINGLE BATCH
        def commit(namespace, mutations):
            '''Stores all the mutations in one batch operation'''
            pool = poolFor(namespace)
            with using(pool) as conn:
                conn.client.set_keyspace(namespace)
                conn.client.batch_mutate(mutations, clasz.consistency)    
        # BATCH ALL THE INDIVIDUAL CHANGES IN ONE TRANSFER
        mutations = {}
        for model in models:
            assert issubclass(model.__class__, BaseModel), "parameter model:\
                %s must inherit from BaseModel" % model
            info = Schema.Get(model)
            keyspace = info[0]
            assert namespace == keyspace, "All the Models should belong to %s" % namespace
            kind = info[1]
            if kind not in COLUMNFAMILIES and Settings.DEBUG:
                Lisa.create(model)
            meta = MetaModel(model)
            key = model.key()
            key.saved = True
            mutations[meta.id()] = meta.mutations()
        commit(keyspace,mutations)    
  
    @staticmethod
    def clear():
        '''Clears internal state of @this'''
        logging.info('Clearing internal state of the Datastore Mapper')
        with LOCK:
            KEYSPACES.clear()
            COLUMNFAMILIES.clear()
            POOLS.clear()
            
##
# MetaModel:
# A Helper class that transforms BaseModel to Cassandra's data model.
##
class MetaModel(object):
    '''Changes a BaseModel to Cassandra's DataModel..'''
    def __init__(self, model):
        '''Creates a Transform for this BaseModel'''
        info = Schema.Get(model)
        self.model = model
        self.namespace = info[0]
        self.kind = info[1]
        self.key = info[2]
        self.comment = self.kind.__doc__
        self.fields = fields(model, Property)
    
    def id(self):
        '''Returns the appropriate representation of the key of self.model'''
        val = self.model.key().id
        if not isinstance(val, basestring):
            val = str(val)
        return encode(val)
    
    @redo   
    def makeKeySpace(self, connection):
        '''Creates a new keyspace from the namespace property of this BaseModel'''
        try:
            connection.client.system_add_keyspace(self.asKeySpace())
        except Exception as e:
            pass
    
    @redo       
    def makeColumnFamily(self, connection):
        '''Creates a new column family from the 'kind' property of this BaseModel'''
        options = optionsFor(self.namespace)
        try:
            connection.client.set_keyspace(options["keyspace"])
            connection.client.system_add_column_family(self.asColumnFamily())
            self.wait(connection)
        except InvalidRequestException as e:
            pass #raise DuplicateError("Another Keyspace with this name seems to exist")
    
    @redo
    def makeIndexes(self, connection):
        '''Creates Indices for all the indexed properties in the model'''
        try:
            options = optionsFor(self.namespace)
            query = 'CREATE INDEX ON {kind}({name});'
            for name, property in self.fields.items():
                if property.saveable() and property.indexed():
                    logging.info("Creating index on: %s" % property)
                    cursor = connection.cursor()
                    formatted = query.format(kind = self.kind, name= property.name)
                    cursor.execute("USE %s;" % options['keyspace'])
                    cursor.execute(formatted)
                else:
                    logging.info("Cannot index: %s" % property)
                    pass
            self.wait(connection)
        except Exception as e:
            pass
                    
    def asKeySpace(self):
        '''Returns the native keyspace definition for this object;'''
        options = optionsFor(self.namespace)
        assert options is not None, "No configuration options for this keyspace"
        name = options['keyspace']
        strategy = options['strategy']['name']
        package = 'org.apache.cassandra.locator.%s' % strategy
        replication = options['strategy']['factor']
        if strategy == 'NetworkTopologyStrategy':
            strategyOptions = options['strategy']['options']
            return KsDef(name, package, strategyOptions, replication, [])
        else:
            return KsDef(name, package, None, replication, [])
      
    def asColumnFamily(self):
        '''Returns the native column family definition for this @BaseModel'''
        options = optionsFor(self.namespace)
        assert options is not None, "No configuration options for this keyspace"
        namespace = options['keyspace']
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
            if prop.saveable():
                column = ColumnDef()
                column.name = name
                column.validation_class = expand(self.defaultType())
                columns.append(column)
        return columns
           
    def keyType(self):
        '''Returns the Comparator type of the Key Descriptor of this BaseModel'''
        return "UTF8Type"
    
    def defaultType(self):
        '''Returns the default validation class for a particular BaseModel'''
        return "UTF8Type"
    
    def wait(self, conn):
        '''Waits for schema agreement accross the entire cluster'''
        while True:
            versions = conn.client.describe_schema_versions()
            if len(versions) == 1:
                break
            time.sleep(0.10) 
    
    def getColumn(self, name, value):
        '''Returns a Native Column from a property with this name'''
        column = Column()
        if name in self.fields:
            column.name = name
            property = self.fields[name]
            column.value = property.convert(value)  
            ttl = property.ttl
            if ttl: column.ttl = ttl
        else:
            k, v = self.model.default
            k = k() if isinstance(k, type) else k
            v = v() if isinstance(v, type) else v
            name = k.convert(name)
            value = v.convert(value)
            column.name = name
            column.value = value # Just pickle it over the wire
        column.timestamp = int(time.time())
        return column
    
    @classmethod
    def load(self, key, coscs):
        '''Creates a Model from an iterable of ColumnOrSuperColumns'''
        if not coscs: return None
        cls = Schema.ClassForModel(key.namespace, key.kind)
        info = Schema.Get(cls)
        model = cls()
        descriptors = fields(cls, Property)
        for cosc in coscs:
            name = cosc.column.name  
            if name in descriptors:  # Deconvert static properties first.
                prop = descriptors[name]
                deconverted = prop.deconvert(cosc.column.value)
                model[name] = deconverted 
            else: # Deconvert dynamic properties, this deconverts column names, and column values
                k, v = model.default
                k = k() if isinstance(k, type) else k
                v = v() if isinstance(v, type) else v
                name = k.deconvert(cosc.column.name)
                value = v.deconvert(cosc.column.value)
                model[name] = value
        keyname = info[2]
        setattr(model, keyname, key.id) #Make sure the newly returned model has the same key
        key = model.key()
        key.saved = True
        return model
         
    def mutations(self):
        '''Returns a {} of mutations that have occurred since last commit'''
        # See Page 151 and Page 78 in the Cassandra Guide.
        logging.info("Batching mutations")
        mutations = { self.kind : [] }
        differ = self.model.differ
        
        logging.info('Marshalling additions')
        for name in differ.added():
            column = self.getColumn(name, self.model[name]) #=> Fetch the Column for this name
            cosc = ColumnOrSuperColumn()
            cosc.column = column
            mutation = Mutation()
            mutation.column_or_supercolumn = cosc
            mutations[self.kind].append(mutation)
        logging.info('Marshalling modifications')
        for name in differ.modified():
            column = self.getColumn(name, self.model[name]) #=> Fetch the Column for this name
            cosc = ColumnOrSuperColumn()
            cosc.column = column
            mutation = Mutation()
            mutation.column_or_supercolumn = cosc
            mutations[self.kind].append(mutation)  
        # Remove all the deleted columns
        logging.info('Marshalling deletions')
        deletion = Deletion()
        deletion.timestamp = int(time.time())
        predicate = SlicePredicate()
        predicate.column_names = list(differ.deleted())
        deletion.predicate = predicate
        deletions = Mutation()
        deletions.deletion = deletion
        mutations[self.kind].append(deletions) 
        return mutations

# Global Variables
store = Lisa()       
