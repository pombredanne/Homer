#!/usr/bin/env python
#
# Copyright 2012 June Inc.
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
import uuid
from .differ import Differ
from .models import key, Model, UnIndexable, Reference
from .commons import String

__all__ = ["Map",]

"""
Map:
A Map is a collection that helps deal with associations
when you are using homer.

Differences between Map and Model:
1. Equality between two Maps test every key and value, Equality between Models test only keys.
"""
@key('id')
class Map(Model):
    '''An Eventually Consistent Hashtable that you can persist to Cassandra'''
    def __init__(self, key=object, value=object, default=None):
        assert isinstance(key, type) and isinstance(value, type), "key and value have to be classes"
        self.differ = Differ(self, exclude = ['differ','key', 'value'])
        if issubclass(key, Model):
            key = Reference(key)
        if issubclass(value, Model):
            value = Reference(value) 
        self.key, self.value = key, value
        if default:
            self.update(default)
        
    def save(self):
        '''Overriden to make sure each Map has an id before each save'''
        if not self.id:
            self.id = str(uuid.uuid4())
        super(Map, self).save()
    
    def update(self, other):
        '''Updates this Hashtable with key, values from the iterable "other" '''
        for k, v in other.iteritems():
            self[k] = v

    def __eq__(self, other):
        '''Checks if a Map is equal to another Map like object'''
        if self.keys() != other.keys():
            return False 
        for k in self.keys():
            if self[k] != other[k]:
                return False
        return True

    def __str__(self):
        '''String representation of a Property'''
        return "Map<%s, %s>" % (self.key.__name__, self.value.__name__)

    # Basic Properties for the collection.
    id = String(indexed=True)

    
