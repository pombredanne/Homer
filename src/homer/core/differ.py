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
---------------------------------------------------------------------
Differ:
The differ module contains utilities that helps homer to diff objects
and retrieve properties that have changed. This is helpful because it
reduces the payload of thrift/redis protocol requests.
----------------------------------------------------------------------
"""

"""
DiffError:
Represents any exception that gets thrown during diffing
"""
class DiffError(Exception):
    pass
    

class Differ(object):
    """A class that knows how to calculate changes in an object"""
    
    def __init__(self, model):
        '''Inserts all the objects in @args to this differ'''
        self.replica = copy.deepcopy(model)
        self.model = model
              
    def added(self):
        '''Yields the names of the attributes that were recently added to this model'''
        dict = self.model.__dict__
        for name in dict:
            if not hasattr(self.replica, name):
                yield name
            
    def commit(self):
        '''Make the current state the default state for this Differ'''
        self.replica = copy.deepcopy(self.model)
        
    def deleted(self):
        '''Yields the names of the attributes that were deleted from this model'''
        dict = self.replica.__dict__
        for name in dict:
            if not hasattr(self.model, name):
                yield name
    
    def modified(self):
        '''Return all the attributes that were modified in any way in this model'''
        dict = self.replica.__dict__
        for name in dict:
            if hasattr(self.model, name):
                if dict[name] != getattr(self.model, name):
                    yield name
        

   
    
    
    
    
