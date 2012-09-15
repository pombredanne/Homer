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
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June Inc.

Description:
configuration options for Homer; This module was inspired by tornado.options...
An awesome example of how to use homer.core.commons in day to day development.
"""
# Standard library imports.
import os
import sys
import logging
import time
from threading import RLock, local

# BASIC CONCURRENCY PRIMITIVE
LOCAL = local()

# OPTIONS THAT ARE USED TO CONNECT TO A CASSANDRA CLUSTER BY DEFAULT,
# WHEN NO OTHER CONFIGURATION IS AVAILABLE

DEFAULT_OPTIONS = LOCAL.DEFAULT_OPTIONS = {
                        "size" : 25, "timeout" : 30.0, "recycle" : 8000,
                        "idle" : 10, "retry" : 5, "servers" : ["localhost:9160",],
                        "username" : "", "password": "", "keyspace": "Test",
                        "strategy" : {
                               "name": "SimpleStrategy", "factor": 1,
                        },

                   }

# THE DEFAULT NAMESPACE USED FOR CONNECTING TO CASSANDRA WHEN NO NAMESPACE IS SPECIFIED
DEFAULT_NAMESPACE = LOCAL.DEFAULT_NAMESPACE = { "name": "Test", "options": DEFAULT_OPTIONS, }

# ALL THE NAMESPACES THAT HOMER KNOWS ABOUT.
NAMESPACES =  LOCAL.NAMESPACES = { }
    
##
# Global Configuration Settings                                                                     
##    
class Settings(object):
    """ Specifies configuration for logging,"""
    debug = True
    
    @classmethod
    def logger(self, name = "Default::Logger"):
        """Creates a new logger everytime from the attributes that are set in this logger"""
        log = logging.getLogger(name)
        handler = logging.StreamHandler() #Maybe we should create a ScribeHandler... :)
        log.addHandler(handler)
        if self.debug:
            log.setLevel(logging.DEBUG)
        else: log.setLevel(logging.INFO)
        return log
