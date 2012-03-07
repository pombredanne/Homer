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
Copyright 2011, June inc.

Description:
An eventually consistent Cassandra based implementation of 
common containers types implemented as descriptors;
e.g. [List, Map, Set..]
"""
import re
import urlparse
from homer.util import Size
from homer.core.models import Basic, Type, BadValueError, Property, UnIndexable, UnIndexedType
"""
Set:
A descriptor that describes python sets, They are heterogenous by default. 
If you need homogeneous sets; just use Set(Blog). It provides a useful default
an empty set. e.g.
...
class Person(object):
    spouses = Set(User)

"""
class Set(UnIndexable):
    """A data descriptor for storing sets"""
    
    def __set__(self, instance, value):
        """Put @value in @instance's class dictionary"""
        # This will overwrites the underlying model.
        pass
    
    def __get__(self, instance, owner):
        """Read the value of this property"""
        # Returns the a dict-like View that people can interact with.
        pass
           
    def __delete__(self, instance):
        """ Delete this Property from @instance """
        # Deletes the underlying Model from the datastore, maintaining integrity.
        pass
        
    def convert(self, instance, name, value):
        '''Persists the underlying MapModel, and returns its key'''
        pass
    
    def deconvert(self, instance, name, value):
        '''Reads the key of the MapModel, and fills the MapModel'''
        pass
        
    def validate(self, value):
        '''Does type checking and coercion'''
        return None
"""
List:
A descriptor that stores homogeneous types, it works like the Set descriptor except
that Lists can accept duplicates. by default it is an empty list.
sample.

class Person(object):
    name = String()
    harem = List(String)

person = Person()
person.harem.extend(["Aisha","Halima","Safia",])

"""
class List(UnIndexable):
    """Stores a List of objects,You can specify the type of the objects this list contains"""
    def __init__(self,cls = Basic):
        assert issubclass(cls, Converter), "@key must be a subclass of Basic"
        self.cls = cls
        super(List, self).__init__(default, **arguments)
    
    def __set__(self, instance, value):
        """Put @value in @instance's class dictionary"""
        # This will overwrites the underlying model.
        pass
    
    def __get__(self, instance, owner):
        """Read the value of this property"""
        # Returns the a dict-like View that people can interact with.
        pass
           
    def __delete__(self, instance):
        """ Delete this Property from @instance """
        # Deletes the underlying Model from the datastore, maintaining integrity.
        pass
   
    def convert(self, instance, name, value):
        '''Persists the underlying MapModel, and returns its key'''
        pass
    
    def deconvert(self, instance, name, value):
        '''Reads the key of the MapModel, and fills the MapModel'''
        pass
        
    def validate(self, value):
        '''Does type checking and coercion'''
        pass
          
"""
Map:
A descriptor for dict-like objects;

class Person(object):
    bookmarks = Map(String, URL)
"""
class Map(UnIndexable):
    def __init__(self, key=Basic, value=Basic):
        """Creates an instance of this Map..."""
        assert issubclass(key, Converter), "@key must be a subclass of Basic"
        assert issubclass(value, Converter), "@value must be a subclass of Basic"
        self.key, self.value = key, value
        super(Map, self).__init__(default, **arguments)

    def __set__(self, instance, value):
        """Put @value in @instance's class dictionary"""
        # This will overwrites the underlying model.
        pass
    
    def __get__(self, instance, owner):
        """Read the value of this property"""
        # Returns the a dict-like View that people can interact with.
        pass
           
    def __delete__(self, instance):
        """ Delete this Property from @instance """
        # Deletes the underlying Model from the datastore, maintaining integrity.
        pass
   
    def convert(self, instance, name, value):
        '''Persists the underlying Model, and returns its key'''
        pass
    
    def deconvert(self, instance, name, value):
        '''Reads the key of the Model which is @value, and fills up the View.'''
        pass
        
    def validate(self, value):
        '''Does type checking and coercion'''
        pass

