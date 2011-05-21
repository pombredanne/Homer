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


options = Options()
"""
Options:
Uses "commons" to specify the configuration options for Homer
"""
class Options(object):
    """ Specifies configuration for logging, """
    logFile = String()
    logFileSize = Integer(10 * 1024 * 1024)
    output = String("stdout", choices = ["stdout", "stderr", "file", ])
    logging = String("info", choices = ["info", "warning", "error", "none",])
    
    def define(self, name, value):
        """ Helper to define options you want to share """
        pass
    
    @property
    def logger(self):
        """Creates a logger from the attributes that are set in this logger"""
        raise NotImplementedError("Sorry...")
    
