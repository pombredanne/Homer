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
An Cassandra based implementation of common containers, 
[List, Map, Set..]
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
    def __init__(self, cls = object,default = set(),**arguments):
        """The type keyword here has a different meaning"""
        self.cls = cls
        super(Set, self).__init__(default, **arguments)
    
    def validate(self,value):
        """Validates the type you are setting and its contents"""
        value = super(Set,self).validate(value)
        if value is None:
            return None
            
        if not isinstance(value, set):
            try: value = set(value)
            except:
                raise BadValueError("This property has to be set, got a : %s" % type(value))
        coerced = set()
        # Coercion is all or nothing. if any fails the entire operation fails
        name = self.cls.__name__
        if name in defaults: # Check if cls is a common descriptor.
            validate = defaults[name] # Retrieve a singleton to deal with this.
            for i in value:  # Normally Common descriptors take care of 'Nones'
                coerced.add(validate(i))
            return coerced        
        else: # Do normal type coercion, third party devs should make sure their Descriptors are callable
            for i in value: 
                if isinstance(i, self.cls):
                    coerced.append(i)
                    continue
                try:
                    if isinstance(i, list): i = self.cls(*i)
                    elif isinstance(i, dict): i = self.cls(**i)
                    else: i = self.cls(i)
                    coerced.append(i)       
                except: 
                    raise BadValueError("Cannot coerce: %s to %s"% (i, self.cls)) 
            return coerced
"""
List:
A descriptor that stores homogeneous types, it works like the Set descriptor except
that Lists can accept duplicates. by default it is an empty list.
sample.

class Person(object):
    name = String()
    harem = List(String())

person = Person()
person.harem.extend(["Aisha","Halima","Safia",])

"""
class List(UnIndexable):
    """Stores a List of objects,You can specify the type of the objects this list contains"""
    def __init__(self,cls = object, default = [], **arguments ):    
        self.cls = cls
        super(List, self).__init__(default, **arguments)
     
    def validate(self,value):
        """Validates a list and all its contents"""
        value = super(List,self).validate(value)
        if value is None:
            return None
        if not isinstance(value, list):
            try: value = list(value)
            except:
                raise BadValueError("This property has to be set, got a : %s" % type(value))
        coerced = []
        # COERCION IS AN ALL OR NOTHING OPERATION. IF ANY FAILS THE ENTIRE OPERATION FAILS
        name = self.cls.__name__
        if name in defaults: # CHECK IF CLS IS A COMMON DESCRIPTOR.
            validate = defaults[name] # RETRIEVE A SINGLETON TO DEAL WITH THIS.
            for i in value:  # NORMALLY COMMON DESCRIPTORS TAKE CARE OF 'NONES'
                coerced.append(validate(i))
            return coerced        
        else: # DO NORMAL TYPE COERCION, THIRD PARTY DEVS SHOULD MAKE SURE THEIR DESCRIPTORS ARE CALLABLE
            for i in value: 
                if isinstance(i, self.cls):
                    coerced.append(i)
                    continue
                try:
                    if isinstance(i, list): i = self.cls(*i)
                    elif isinstance(i, dict): i = self.cls(**i)
                    else: i = self.cls(i)
                    coerced.append(i)   
                except: 
                    raise BadValueError("Cannot coerce: %s to %s"% (i, self.cls))        
            return coerced      
          
"""
Map:
A descriptor for dict-like objects;

class Person(object):
    bookmarks = Map(String, URL)
"""
class Map(UnIndexable):
    ''' A descriptor for dict-like objects '''
    def __init__(self, key=object, value=object, default = {}, **arguments):
        self.key, self.value = key, value
        super(Map, self).__init__(default, **arguments)
    
    def validate(self, value):
        '''Simply does type checking'''
        value = super(Map, self).validate(value)
        if value is None:
            return None
        if not isinstance(value, dict):
            try: value = dict(value)
            except:
                raise BadValueError("This property has to be set, got a : %s" % type(value))
        coerced = {}
        keyVal, valueVal = None, None
       
        if isinstance(self.key, type):
            name = self.key.__name__
            keyVal = defaults[name] if name in defaults else self.key
        if isinstance(self.value, type):
            val = self.value.__name__
            valueVal = defaults[val] if val in defaults else self.value    
        for k,v in value.items(): 
            key = keyVal(k) 
            value = valueVal(v)
            coerced[key] = value
        return coerced

