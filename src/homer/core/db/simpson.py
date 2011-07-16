"""
Author : Iroiso .I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Provides a very nice abstraction around the storage layer of
the June infrastructure.

"""

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
Simpson: as in Homer Simpson :)
Simpson provides a simple and efficient wrapper over Cassandra
and Memcached. It automatically implements the store and cache
pattern to make fetches lightning fast.

"""
class Simpson(object):
    '''The current incarnation of the Homer SDK'''
    
    def Put(cls, instance, cache = False, cacheExpiry = -1):
        '''Stores this object in Cassandra and Memcached if cache is True'''
        pass
    
    def Get(cls, cache = False, *keys):
        '''Tries to get these Keys from the datastore; if cache check Memcached first'''
        pass
    
    def Delete(cls, cache = False, *keys):
        '''Tries to remove these keys from the Datastore and the Cache'''
        pass
    

class RoundRobinPool(object):
    '''Implements Load balancing for a cluster of cassandra services'''
    def get(self):
        """Returns a Connection from the pool"""
        pass


class Connection(object):
    """A convenient wrapper around the thrift client interface"""
    def __init__(self, address, port, debug = True):
        '''Creates a Cassandra Client internally and initializes it'''
        pass
