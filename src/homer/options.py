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
from homer.core.commons import Map, Boolean, Set, String

"""
Options:
Uses "commons" to specify the system wide configuration options for Homer;

"""
class Options(object):
    """ Specifies configuration for logging, """
    debug = Boolean(True)
    auth = Map(String, String )
    namespace = String(default = "June")
    dbs = Set(String, default = ["localhost:9160",])
    caches = Set(String, default = ["localhost:11211",]) # each host uses the format address:port
    
    
    def logger(self, name = "Default::Logger"):
        """Creates a new logger everytime from the attributes that are set in this logger"""
        log = logging.getLogger(name)
        if self.debug:
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)
        return log
       
        
        
"""# Module Singletons """   
options = Options() 
