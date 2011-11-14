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
import os
import sys
import logging
import time
from homer.core.models import READONLY, Type
from homer.core.commons import *
from homer.core.builtins import object  

##                                                                                                  
# Cassandra Configuration Options.
##
class Strategy(object):
    '''Base class for all Strategy Types'''
    pass
    
class NetworkTopologyStrategy(Strategy):
    name = String("NetworkTopologyStrategy", READONLY)
    factor = Integer(1)
    options = Map(String, Integer)

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
    timeout = Float(0.5)
    recycle = Integer(8000)
    idle, retry = Integer(10),Integer(5)
    servers = Set(String,default = ["localhost:9160",])
    strategy = Type(type =Strategy,default = SimpleStrategy())
    username,password,keyspace = String(),String(),String("Test")
    
##                                                                                                  
# Memcache Configuration Settings
##
class CacheOptions(object):
    pass
    
##
# Global Configuration Settings
##    
"""
Options:
Uses "commons" to specify the system wide configuration options for Homer;

"""
class Settings(object):
    """ Specifies configuration for logging, """
    debug = Boolean(True)
    
    def add(self, namespace):
        """Adds this namespace to the list of known namespaces"""
        pass
    
    def load(self, config, file = None):
        """Reads configuration options from config or from file, but not from both"""
        pass
        
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

             
"""Create a Singleton for Project Wide Configuration"""   
options = Settings()
