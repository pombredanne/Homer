#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June Inc.

Description:
configuration options for Homer; This module was inspired by tornado.options...
An awesome example of how to use homer.core.commons in day to day development.
"""
# Standard Library Imports.
import os
import sys
import logging
import time
from threading import RLock, local

# Homer Related Importeds.
from homer.core.models import READONLY, Type
from homer.core.commons import *
from homer.core.builtins import object  

##                                                                                                  
# Cassandra Configuration Options.
##
class Strategy(object):
    '''Base class for all Strategy Types'''
    def __str__(self):
        return self.name
    
class NetworkTopologyStrategy(Strategy):
    name = String("NetworkTopologyStrategy", READONLY)
    factor = Integer(1)
    options = Map(String, Integer, default = None)

class OldNetworkTopologyStrategy(Strategy):
    '''Configuration options for the "OldNetworkTopologyStrategy" '''
    name = String("OldNetworkTopologyStrategy", READONLY)
    factor = Integer(1)
    
class SimpleStrategy(Strategy):
    '''A wrapper for configuration options for the "SimpleStrategy" '''
    name = String("SimpleStrategy", READONLY)
    factor = Integer(1)
    
class DataStoreOptions(object):
    '''Configuration options for Cassandra'''
    size = Integer(25)
    timeout = Float(30.0)
    recycle = Integer(8000)
    idle, retry = Integer(10),Integer(5)
    servers = Set(String,default = ["localhost:9160",])
    strategy = Type(type =Strategy,default = SimpleStrategy())
    username,password,keyspace = String(),String(),String("Test")
    
##
# Global Configuration Settings                                                                     
##    
class Settings(object):
    """ Specifies configuration for logging,"""
    debug = Boolean(True)
        
    def logger(self, name = "Default::Logger"):
        """Creates a new logger everytime from the attributes that are set in this logger"""
        log = logging.getLogger(name)
        handler = logging.StreamHandler() #Maybe we should create a ScribeHandler... :)
        log.addHandler(handler)
        if self.debug:
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)
        return log
      
##
# Storage Grouping
##     
class Namespace(object):
    '''Used for grouping Configurations for a Namespace'''
    name = String("Test")
    cassandra = Type(type=DataStoreOptions, default= DataStoreOptions())
    
    def __str__(self):
        return "[Namespace: %s]" % self.name
  

class Namespaces(object):
    '''An object that tracks namespaces'''
    def __init__(self):
        self.namespaces = {}
        self.lock = RLock()
        self.__default = Namespace()
    
    def __setdefault__(self, namespace):
        '''a setter for setting the default namespace'''
        if isinstance(namespace, Namespace):
            self.__default = namespace
        elif isinstance(namespace, str):
            if namespace in self.namespaces:
                self.__default = self.namespaces[namespace]
            else:
                raise ValueError("Could not find any \
                    Namespace with name: %s" % namespace)
        else:
            raise ValueError("An Instance of Namespace\
            or str is required")
    
    def __getdefault__(self):
        ''' A getter for return the default namespace '''
        return self.__default
    
    def add(self, namespace):
        """Adds this namespace to the list of known namespaces"""
        with self.lock:
            self.namespaces[namespace.name] = namespace
    
    def get(self, name):
        """Returns configuration for a particular namespace"""
        with self.lock:
            if not name or name == self.default.name:
                return self.default
            else:
                return self.namespaces[name]
                
    default = property(__getdefault__, __setdefault__)
            
"""Create a Singleton for Project Wide Configuration"""   
options = Settings()
namespaces = Namespaces()
