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


"""
Options:
Uses "commons" to specify the configuration options for Homer;
Todo:

"""
class Options(object):
    """ Specifies configuration for logging, """
    
    def logger(self, name = "Default::Logger"):
        """Creates a new logger everytime from the attributes that are set in this logger"""
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)
        log.addHandler(logging.NullHandler())
        return log
       
        
        
"""# Module Singletons """   
options = Options() 
