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
from functools import update_wrapper

from thrift import Thrift
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

from homer.rpc import Cassandra
from homer.core.options import options

__all__ = ["CqlQuery", "Simpson"]

Pooled, CheckedOut, Disposed = 0, 1, 2

# Module Exceptions
class DisposedError(Exception):
    """A Error that is thrown if you try to use a Connection that has been disposed"""
    pass



class Memcache(object):
    '''A Memcache interface that knows Homer Models'''
    pass
    
"""
CqlQuery:
A CqlQuery wraps CQL queries in Cassandra 0.8.+, However it
provides a very distinguishing feature, it automatically
returns query results as Model instances.
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
Pool:
An abstract class that all pools must implement
"""
class Pool(object):
    '''Implements Load balancing for a Cluster'''
    
    def get(self, keyspace):
        '''Yields a valid connection to this Keyspace'''
        raise NotImplementedError
        
    def addToPool(self):
        """Returns a Connection from the pool"""
        raise NotImplementedError
    
    def dispose(self, conn):
        '''Detaches this conn from the Pool'''
        raise NotImplementedError

"""
RoundRobinPool:
This provides threadsafe client side load balancing for a Cassandra cluster, 
is created it reads configuration from the options and creates a pool of open 
connections which it reuses.
e.g.
pool = RoundRobinPool(size = 10)
db = pool.get() #
db.client.put("iroiso", "name", 10)


"""
class RoundRobinPool(Pool):
    '''Implements Load balancing for a Cluster'''
    def get(self, keyspace):
        '''Yields a valid connection to this Keyspace'''
        pass
        
    def addToPool(self):
        """Returns a Connection from the pool"""
        pass
    
    def dispose(self, conn):
        '''Detaches this conn from the Pool'''
        pass


"""
Connection:
A convenient wrapper around an Ordinary Cassandra.Client which
that can be pooled, I also speak in homer Models.
"""
class Connection(object):
    """A convenient wrapper around the thrift client interface"""
    def __init__(self, pool, address, debug = True, timeout = 3*1000, auth = {}):
        '''Creates a Cassandra Client internally and initializes it'''
        Client = DebugTraceClient if debug else Cassandra.Client
        host, post = address.split(":")
        socket = TSocket(host, port)
        socket.setTimeout(timeout)
        # Local Variables
        self.transport = TFramedTransport(socket)
        self.pipe = Client(TBinaryProtocolAccelerated(transport))
        setattr(self.pipe, 'host', host)
        setattr(self.pipe, 'port', port)
        self.address = address
        self.state = CheckedOut
        self.pool = pool
        self.log = options.logger("Connection for Address: %s" % self.address)
        self.transport.open()
        if auth:
            request = AuthenticationRequest(credentials = auth)
            self.pipe.login(request)
        if keyspace:
            self.pipe.set_keyspace(keyspace)
    
    @property      
    def client(self):
        '''Returns the Cassandra.Client Connection that I have'''
        if self.state != Disposed
            return self.pipe
        raise DisposedError("This Connection has already been Disposed")
          
    def close(self):
        '''Closes the underlying thrift connection'''
        self.transport.close()
        self.dispose()
    
    def toPool(self):
        '''Return this Connection to the Pool where it came from'''
        try:
            self.pool.addToPool(self)
        except e:
            self.log.error("Exception occurred when adding to Pool: %s " % str(e))
    
    def dispose(self):
        '''Close this connection and mark it as DISPOSED'''
        if self.state == Pooled:
            self.pool.dispose(self)
        self.state = Disposed
    

"""
__TraceFactory__:
is a metaclass that decorates all the callable functions in
Cassandra.Client instance for debug tracing
"""
class __TraceFactory__(type):
    '''Decorates all the methods in the @client,to trace and time calls'''
    def __init__(cls, name, bases, dict):
        '''Wraps all the callables in @cls for tracing'''
        # I lifted some of this from the lazyboy. Those guys are awesome :)
        for name in dir(cls):
            attr = getattr(cls, name)
            if not callable(attr) or name.startswith("__") or \
                name.startswith("send_") or name.startswith("recv_"):
                continue
            def trace(func):
                '''A new wrapper function is created everytime'''
                def __trace__(self, *args, **kwds):
                    start = time.time()
                    try: result = func(*args, **kwds)
                    except e:
                        self.log.error("Caught exception %s during invocation at %s" % (str(e), self.address))
                        raise e
                    endtime = time.time()
                    elapsed = (endtime - start) * 1000
                    self.log.info("Duration for %s to address: %s was %s" % (name, self.address, elapsed))
                    if elapsed > self.threshold:
                        self.log.warning("Function: %s 's invocation passed SLOW THRESHOLD" % name)
                    return result
                update_wrapper(__trace__, func)
                return __trace__
            print "Wrapping Function: %s " % name
            setattr(cls, name, trace(attr))
               
            
"""
DebugTraceClient:
This Extends the Cassandra Client to add tracing and timing to every 
call. Useful for debugging :)
""" 
class DebugTraceClient(Cassandra.Client):
    """A client that traces all calls through it and benchmarks them"""
    __metaclass__ = __TraceFactory__
    def __init__(self, *args, **kwds):
        self.threshold = kwds.get('threshold', 100)
        del kwds['threshold']
        super(DebugTraceClient, self).__init__(*args, **kwds)
        self.log = options.logger("DebugTraceClient: %s " % self.address)
    
    @property
    def address(self):
        return self.host + ":" + self.port
