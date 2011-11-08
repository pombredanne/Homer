#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
configuration options for Homer; This module was inspired by tornado.options...
An awesome example of how to use homer.core.commons in day to day development.
"""
import os
import sys
import logging
import time
from homer.core.commons import *

'''
PoolOption:
Pool specific configuration options
'''
class PoolOption(object):
    '''Configuration options for a Pool'''
    Size = Integer(25)
    Timeout = Float(0.5)
    MaxIdle = Integer(10)
    Namespace = String("Test")
    EvictionDelay = Integer(10000)
    Username, Password = String(), String()
    Servers = Set(String, default = ["localhost:9160",])
    
"""
Options:
Uses "commons" to specify the system wide configuration options for Homer;

"""
class Options(object):
    """ Specifies configuration for logging, """
    from homer.core.models import READONLY, Type
    debug = Boolean(True)
    maxRetries = Integer(5)
    optionsFor = Map(String, PoolOption)
    caches = Set(String, default = ["localhost:11211",]) # each host uses the format address:port
    defaultOptions = Type(type = PoolOption, default = PoolOption(), mode = READONLY)
    
    def load(self, config, file = None):
        """Reads configuration options from config or from file, but not from both"""
        pass
        
    def logger(self, name = "Default::Logger"):
        """Creates a new logger everytime from the attributes that are set in this logger"""
        log = logging.getLogger(name)
        handler = logging.StreamHandler()
        log.addHandler(handler)
        if self.debug:
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)
        return log
            
"""Create a Singleton for Project Wide Configuration"""   
options = Options()
