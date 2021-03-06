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
import copy
from threading import Lock

"""
Differ:
The differ module contains utilities that helps homer to diff objects
and retrieve properties that have changed. This is helpful because it
reduces the payload of thrift requests to cassandra.
"""

class DiffError(Exception):
    """Represents any exception that gets thrown during diffing"""
    pass
    

class Differ(object):
    """A class that knows how to calculate changes in an object"""
    def __init__(self, instance, exclude):
        '''Inserts all the objects in @args to this differ'''
        from homer.core.models import Model
        assert isinstance(instance, Model), "Differs only work on Models"
        self.excluded = exclude
        self.replica = copy.deepcopy(instance.__store__)
        self.model = instance.__store__
        self.instance = instance
    
    def forbidden(self, name):
        '''Excludes names in provided in self.excluded'''
        return name in self.excluded
              
    def added(self):
        '''Yields the names of the attributes that were recently added to this model'''
        # I used getattr(), because properties will return their default values or None by default
        dict = self.model
        for name in dict:
            if not self.replica.get(name, None):
                if not self.forbidden(name):
                    yield name
            
    def deleted(self):
        '''Yields the names of the attributes that were deleted from this model'''
        dict = self.replica
        for name in dict:
            if name not in self.model:
                if not self.forbidden(name):
                    yield name
    
    def modified(self):
        '''Return all the attributes that were modified in any way in this model'''
        dict = self.replica
        for name in dict:
            if name in self.model:
                if dict[name] != self.model[name]:
                    if not self.forbidden(name):
                        yield name
        
    def commit(self):
        '''Make the current state the default state for this Differ'''
        self.replica = copy.deepcopy(self.instance.__store__)
   
    def revert(self):
        '''Reverts @self.model to the previous commit state'''
        # This method will be used to implement a rollback feature for Models
        clean = self.replica
        dirty = self.model
        dispose = [v for v in dirty if v not in clean]
        # Revert all known attributes
        for name in clean:
            self.instance[name] = clean[name]
        # Delete all new attributes
        for name in dispose: 
            delattr(self.model, name)
        self.commit()
   
    
    
    
    
