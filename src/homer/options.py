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
This module is used to configure the global behavior of Homer.
"""
import os
import sys
import time
import yaml
import copy
import logging.config
from threading import local

# EXCEPTIONS
class ConfigurationError(Exception):
    '''Thrown to signal a problem with Homer's current configuration...'''
    pass
    
# FALL BACK CONFIGURATION OPTIONS USED BY DEFAULT, WHEN NO OTHER CONFIGURATION IS AVAILABLE
__DEFAULT__ = {
    "debug" : True,
    "default" : "Homer",
    
    # All the Namespaces that Homer would use and their respective configurations.
    "namespaces" : {
        "Homer" : {
              "size" : 10, 
              "timeout" : 30.0, 
              "recycle" : 8000,
              "idle" : 10, 
              "servers" : ["localhost:9160",],
              "username" : "", 
              "password" : "", 
              "keyspace" : "Homer",
              "strategy" : {
                       "name" : "SimpleStrategy", 
                       "factor" : 1,
               },
        }
    },
}
    
##
# An object that allows you to configure Homer, and query its
# configuration and settings.                                                                   
##    
class Settings(local):
    """ Specifies configuration for logging,"""
    __configuration__ = __DEFAULT__
   
    @classmethod
    def debug(self):
        '''Is Homer in debug mode or not ?'''
        return self.__configuration__.get("debug", False)
        
    @classmethod
    def __initialize__(self):
        '''Setup the configuration module'''
        # Configure logging if available
        if "logging" in self.__configuration__:
            dictionary = self.__configuration__["logging"]
            logging.config.dictConfig(dictionary)
               
    @classmethod
    def configure(self, file=None, dict=None):
        """Configures Homer's behavior globally with the options in @dictionary"""
        if not file and not dict:
            raise ConfigurationError("You have to pass in a configuration file or dictionary")
        if file:
            with open(file) as f:
                string = f.read()
                try:
                     # PRAGMA: NO COVER; I assume that the {} loaded here properly configured - @Iroiso
                    self.__configuration__ = yaml.load(string)["Homer"]
                    self.__initialize__()
                except KeyError:
                    raise ConfigurationError("Couldn't find any configuration for Homer in : %s" % file)
        elif dict:
            # PRAGMA: NO COVER HERE; I assume that the dictionary that is loaded is properly configured - @Iroiso
            try:
                self.__configuration__ = dict["Homer"]
                self.__initialize__()
            except KeyError:
                raise ConfigurationError("Couldn't find any configuration for Homer in : %s" % file)
            
    @classmethod
    def namespaces(self):
        """Returns a copy of all the namespaces that have been configured for Homer"""
        try:
            value = self.__configuration__["namespaces"]
            return copy.deepcopy(value)
        except KeyError:
            raise ConfigurationError("Homer hasn't been properly configured, It can't find the Namespaces dictionary")
            
    @classmethod
    def default(self):
        """Returns the configuration for the default namespace for Homer"""
        found = self.__configuration__.get("default", None)
        if not found:
            raise ConfigurationError("You haven't configured any default keyspace yet.")
        else:
            return found