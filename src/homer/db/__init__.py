"""
Author : Iroiso .I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Provides a very nice abstraction around the storage layer of
the June infrastructure.

"""
import time
import itertools
from threading import Thread
from Queue import Queue, Empty, Full

from thrift import Thrift
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

from cql.cursor import Cursor
from cql.cassandra import Cassandra
from cql.cassandra.ttypes import AuthenticationRequest
from homer.options import options

__all__ = ["CqlQuery", "Simpson", "Memcache"]

POOLED, CHECKEDOUT, DISPOSED = 0, 1, 2

# Module Exceptions
class ConnectionDisposedError(Exception):
    """A Error that is thrown if you try to use a Connection that has been disposed"""
    pass

class TimedOutException(Exception):
    '''Thrown when requests for new connections timeout'''
    pass

class AllServersUnAvailableError(Exception):
    '''Thrown when all the servers in a particular pool are unavailable'''
    pass


"""
Simpson:
Provides a very simple way to use Cassandra from python; It does load balancing,
auto failover, connection pooling and its clever enough to batch calls so it
has very low latency. And one more thing... It automatically implements the
the store and cache pattern, So Gets are lightning fast...
"""
class Simpson(object):
    '''An 'Model' Oriented Interface to Cassandra;'''
    @classmethod
    def Put(cls, *objects ):
        '''Persists @objects to the datastore, put a copy in the cache if cache = True'''
        pass
    
    @classmethod
    def Get(cls, keys ):
        '''Retreives @keys from the Backend, check Memcached if cache is True'''
        pass
    
    @classmethod
    def Delete(cls, *objects):
        '''Deletes @objects from the datastore, remove copy in cache if cache is True'''
        pass
    
"""
Memcache:
An object oriented interface to Memcache that speaks
homer Models, Memcache's interface is very similar
to GAE's memcache.
"""
class Memcached(object):
    '''An 'Model' Oriented Interface to Memcached;'''
    @classmethod
    def Set(cls, *objects):
        '''Put these models in Memcache'''
        pass
    
    
    
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

"""
Consistency:
A Generic Context Manager for dealing with Cassandra's consistency;
It changes the way the Singleton to Cassandra behaves
"""
class Consistency(object):
    '''Generic Context Manager for Simpson'''
    def __init__(self, level):
        self.level = level
        self.previous = None
        
    def __enter__(self):
        '''Changes the current consistency to self.level'''
        pass 
        
    def __exit__(self):
        '''Revert the global consistency to the previous setting.'''
        pass 

#####
# Connection and Pooling 
#####    
"""
Pool:
A pool provides autofailover and loadbalancing automatically
for keyspaces.
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
            if self.count < self.maxConnections:  # If we are under quota just create a new connection
                addr = self.address().next()
                print "Creating a new connection to address: %s" % addr
                connection = Connection(self, addr, self.keyspace, self.username, self.password)
                self.count += 1
                return connection
            else:  # If we are over quota force the request to wait for @self.timeout
                try:
                    return self.queue.get(True, self.timeout)
                except Empty: raise TimedOutException("Sorry, your request has TimedOut")
      
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
                
"""
Connection:
A Wrapper around Cassandra.Client which supports connection pooling, debug
tracing and context managers.
"""
class Connection(object):
    """A convenient wrapper around the thrift client interface"""
    def __init__(self, pool, address, keyspace = None, username = None, password = None, timeout = 3*1000):
        '''Creates a Cassandra Client internally and initializes it'''
        host, port = address.split(":")
        socket = TSocket.TSocket(host, int(port))
        socket.setTimeout(timeout)
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
        self.pipe.set_keyspace(keyspace)
        if username and password:
            request = AuthenticationRequest(credentials = {"username": username, "password": password})
            self.pipe.login(request)
    
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
            self.state = DISPOSED
            self.open = False
    
