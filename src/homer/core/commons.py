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
Common descriptors for day to day usage
"""
import re
import uuid
import datetime
import urlparse
from contextlib import closing
from homer.util import Size
from .types import phone, blob, TypedMap, TypedSet, TypedList, TypedCounter
from .models import READWRITE, Basic, Type, BadValueError, Property, UnIndexable, UnIndexedType
from .models import Converter as blank

maxsize = 1024 * 1024 * 512
__all__ = [
            "Integer","String","Blob","Boolean","URL", 
            "Time","DateTime","Phone","Date","Float", "Map", 
            "Set", "List", "UUID",
]

"""
Phone:
A descriptor that stores phone objects,
"""
class Phone(Type):
    '''An descriptor that contains phone objects'''
    type = phone
    
    def convert(self, value):
        '''Yields the datastore representation of its value'''
        value = self.validate(value)
        return repr(value)
    
    def deconvert(self, value):
        '''Converts a value from the datastore to a native python object'''
        result = eval(value)
        assert isinstance(result, phone), "Got unexpected type after serialization"
        return result
                
"""
UUID:
Generates Type 4 UUIDs on the fly when they are requested for; this is
useful for creating UUID's for Models.
"""
class UUID(Basic):
    '''A type 4 UUID Property'''
    
    def __init__(self, default = uuid.uuid4(), indexed=True, **keywords):
        '''Simply makes sure that a UUID Property is READWRITE'''
        super(UUID,self).__init__(default=default, type=str, indexed=indexed, 
            mode=READWRITE, **keywords)
    
    def validate(self, value):
        '''Validates UUID objects.'''
        try:
            if isinstance(value, uuid.UUID): return value
            coerced = uuid.UUID(value)
            return coerced
        except Exception:
            raise BadValueError("Could not convert %s to a Type 4 UUID" % (value,))
           
    def __get__(self,instance,owner):
        """Generates a new UUID if this attribute is None."""
        if self.name is None : self.name = UUID.search(instance, owner,self)
        if self.name is not None:
            value = instance.__dict__.get(self.name, None)
            if value is None:
                value = uuid.uuid4()
                self.__set__(instance, value)
            return value
        else:
            raise AttributeError("Cannot find any property named %s in: %s" % 
                (self.name, owner))
              
"""
Float:
A data descriptor for modeling Floats in your 'things'. It coerces like the normal
python float

# ... snippet ...
class Circle(object):
    pi = Float(3.142)
    
"""
class Float(Basic):
    """ A float descriptor """
    type = float
    
"""
Integer:
A data descriptor that is used to create properties for longs and ints in 
your models. All integers are represented as longs within. Integers behave
like normal python ints and long and they coerce values.

# .. snippet ...
class Balls(object)
    number = Integer(choices = range(1,5))
    sold = Integer()
    
"""
class Integer(Basic):
    """Data descriptor for an Integer"""
    type = long

   
"""
String:
The String descriptor is used to create String Properties in your models.
The following snippet shows various usecases for String; 
class Story(object):
    '''Models a Story Object'''
    channel = String("BBC World News", pattern= r'COUNT\(.+\)')
    reporter = String(length = 30)
"""
class String(Basic):
    """A data descriptor that wraps Strings"""
    def __init__(self,default="", length = 500, **arguments):
        """ Construct property """
        if length <= 0:
            raise ValueError("Length must be greater than zero")
        super(String,self).__init__(default = default, type = str,**arguments)
        self.length = length
   
    def validate(self,value):
        """Validate length here"""
        # TODO: Add support for regex based validation.
        assert value is not None, "Value must not be None"
        value = super(String,self).validate(value)
        assert len(value) <= self.length,"String longer than expected,\
            required : %s , got : %s" % (self.length, len(value))
        return value
        
    
"""
Blob:
Blob is Data descriptor for modeling blobs, it provides useful features like size
monitoring, and static methods for creating Blobs from a path and a filelike object.
Blob descriptors are not indexable
e.g.

class Person(object):
    '''A simple person model'''
    headshot = Blob(path = "./headshot.jpg",size = 1024*50)

The line above says create a blob from path: ./headshot.jpg, but make sure the blob
is not greater than 50kb. If you specify size as -1; It basically says read everything
from the filesystem.
You can also create blobs from stream with a class method like thus:

avatar = Blob.fromFile(filelike)

....
"""   
class Blob(Basic):
    """Store Blobs"""
    def __init__(self, default= "", size = maxsize, **arguments):
        """
        Creates a Blob
        @size: Represents the maximum size in bytes this Blob can store, -1 or less
               means it can store anysize.
        """
        assert "choices" not in arguments,"Choices do not mean anything in Blobs"
        self.__size = size
        super(Blob,self).__init__(type = str, default = default, **arguments)
    

    def indexed(self):
        '''Blobs cannot be indexed'''
        return False;
             
    @property
    def size(self):
        """Whatever you store in this Blob MUST not be larger than the size property"""
        return self.__size
    
    def validate(self,value):
        """Makes sure that whatever you are putting, does not exceed size"""
        value = super(Blob,self).validate(value)
        if self.size <= -1:
            return value
        inBytes = Size.inBytes(value)
        if not inBytes <= self.size :
            raise BadValueError("Your blob size must be less than:\
                %s , got: %s" % self.size, inBytes )
        if not isinstance(value, blob):
            value = blob(str(value))
        return value
    
    def convert(self, value):
        '''Every blob type knows how to convert itself to a JSON representation on repr'''
        value = self.validate(value)
        return repr(value)
    
    def deconvert(self, value):
        '''Change a JSON repr of a blob stored in the datastore to a python object'''
        new = blob()
        loaded = json.loads(value)
        for name, value in loaded.items():
            setattr(new, name, value)
        return new                             

"""
Boolean:
A descriptor that coerces any value set to it to a boolean. it behaves like 
the python bool builtin function. Boolean uses pythonic truth. so beware!!!.
e.g.
class Person(object):
    married = Boolean()

person = Person()
person.married = "Married"
assert person.married == True
person.married = True
assert person.married == True

"""        
class Boolean(Basic):
    """Stores Boolean values, It coerces values like normal python bools"""
    type = bool
        
"""
URL:
A URL descriptor that validates strings to make sure they are valid URLs.
It inherits String, so you can use it like a string.It uses a Strings default
length of 500 chars, If you need a longer URL, modify its length property.
e.g.

class Person(object):
    website = URL("http://harem.tumblr.com")
       
"""        
class URL(Basic):
    """Makes sure that a string you are creating is a valid URL"""
    type = str
    
    def empty(self, value):
        '''What does it mean for a URL to be empty'''
        return value is None or bool(value.strip())
        
    def validate(self,value):
        """Uses urlsplit to validate urls"""
        value = super(URL,self).validate(value)
        if value is not None and value.strip():
            parsed = urlparse.urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                raise BadValueError('Property %s must be a full URL (\'%s\')' %
                    (self.name, value))
        return value

"""
DateTime:
A descriptor that stores a datetime. It implements autonow keyword which makes sure
that the the attribute always return the current value from the datetime module
...
class Person(object):
    birthdate = DateTime()
    modified = DateTime(autonow = True)
"""
class DateTime(Type):
    """Base class of all date time properties"""
    def __init__(self,default = None,autonow = False, **arguments):
        self.autonow = autonow
        super(DateTime,self).__init__(default = default,type = datetime.datetime, 
            **arguments)
    
    def __get__(self,instance,owner):
        """Overrides get to implement autonow"""
        if self.autonow:
            return self.now()
        return super(DateTime,self).__get__(instance,owner)
    
    def convert(self, value):
        '''Yields the datastore representation of its value'''
        value = self.validate(value)
        return repr(value)
    
    def deconvert(self, value):
        '''Converts a value from the datastore to a native python object'''
        return eval(value)
        
    def empty(value):
        '''DateTime's are empty when they are none'''
        return value is None
        
    def now(self):
        """Helper to return a datetime representing now"""
        return datetime.datetime.now()
         
"""
Time:
Descriptor for storing Times, It stores the time part of a datetime sample usage:

class BreakingNews(object):
    headline = Story()
    time = Time()
"""
class Time(DateTime):
    """Stores only the time part of a datetime"""
    type = datetime.time
    
    def now(self):
        return datetime.datetime.now().time()

"""
Date:
Descriptor for storing Dates, It stores the date part of a datetime
e.g.

class BreakingNews(object):
    headline = Story()
    time = Date()
"""
class Date(DateTime):
    """Stores the Date part of a datetime"""
    type = datetime.date
        
    def now(self):
        return datetime.datetime.now().date()

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
    def __init__(self, cls=blank,default=set(),**arguments):
        """The type keyword here has a different meaning"""
        self.cls = cls
        set = TypedSet(T=cls, data=default)
        super(Set, self).__init__(set, **arguments)
    
    def validate(self,value):
        """Validates the type you are setting and its contents"""
        value = super(Set,self).validate(value)
        if value is None:
            return None
            
        if not isinstance(value, set):
            try: value = set(value)
            except:
                raise BadValueError("This property has to be set, got a : %s" % type(value))
        coerced = TypedSet(T=self.cls, data=value)
        return coerced
"""
List:
A descriptor that stores homogeneous lists, it works like the Set descriptor except
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
    def __init__(self,cls=blank, default = [], **arguments ):    
        self.cls = cls
        list = TypedList(T=cls, data=default)
        super(List, self).__init__(list, **arguments)
     
    def validate(self,value):
        """Validates a list and all its contents"""
        value = super(List,self).validate(value)
        if value is None:
            return None
        if not isinstance(value, list):
            try: value = list(value)
            except:
                raise BadValueError("This property has to be set, got a : %s" % type(value))
        created = TypedList(T=self.cls, data=value)
        return created  
"""
Map:
A descriptor for dict-like objects;

class Person(object):
    bookmarks = Map(String, URL)
"""
class Map(UnIndexable):
    def __init__(self, key=blank, value=blank, default = {}, **arguments):
        self.key, self.value = key, value
        map = TypedMap(key, value, data=default)
        super(Map, self).__init__(map, **arguments)
      
    def validate(self, value):
        '''Simply does type checking'''
        value = super(Map, self).validate(value)
        if value is None:
            return None
        if not isinstance(value, dict):
            try: value = dict(value)
            except:
                raise BadValueError("This property has to be set, got a : %s" % type(value))
        coerced = TypedMap(self.key, self.value, data=value)
        return coerced
        

