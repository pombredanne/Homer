#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Common descriptors for day to day usage
"""
import struct
import urlparse
import datetime
from contextlib import closing
from collections import Hashable
from homer.util import Size
from homer.core.models import Type, BadValueError, Property, UnIndexable, UnIndexedType

# TODO: Add common types; MD5, SHA512, SHA256, Email, Tuple, Rating
__all__ = [
            "Integer","String","Blob","Set","Boolean","List","URL", "Time", "DateTime",
            "Date","Float", "Map",
]

            
"""
Float:
A data descriptor for modeling Floats in your 'things'. It coerces like the normal
python float

# ... snippet ...
class Circle(object):
    pi = Float(3.142)
    
"""
class Float(Type):
    """ A float descriptor """
    type = float
    
"""
Integer:
A data descriptor that is used to create properties that for longs and ints in 
your models.All integers are represented as longs within. Integers behave
like normal python ints and long and they coerce values.

# .. snippet ...
class Balls(object)
    number = Integer(choices = range(1,5))
    sold = Integer()
    
"""
class Integer(Type):
    """Data descriptor for an Integer"""
    type = long

   
"""
String:
The String data descriptor, is used to create String Properties in your models.
e.g. The following snippet shows various usecases for String()

from things.commons import String
from things.core import READONLY

class Story(object):
    '''Models a Story Object'''
    headline = String("Barcelona FC meats Real Madrid in UEFA Champs Final")
    anchor = String("Zeinab Badawi")
    channel = String("BBC World News")
    reporter = String(length = 30)
    
"""
class String(Type):
    """A data descriptor that wraps Strings"""
    def __init__(self,default = "", length = 500, **arguments):
        """ Construct property """
        if length <= 0:
            raise ValueError("Length must be greater than zero")
        super(String,self).__init__(default = default, type = str,**arguments)
        self.length = length
    
    def validate(self,value):
        """Validate length here"""
        value = super(String,self).validate(value)
        assert len(value) <= self.length,"String longer than expected,\
            required : %s , got : %s" % (self.length, len(value))
        return value
        
    
"""
Blob:
Blob is Data descriptor for modeling blobs, it provides useful features like size
monitoring, and static methods for creating Blobs from a path and a filelike object.
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
class Blob(UnIndexedType):
    """Store Blobs"""
    def __init__(self, default= "", size = -1, path = None, **arguments):
        """
        Creates a Blob
        @size: Represents the maximum size in bytes this Blob can store, -1 
               means it can store anysize.
        @file: This is a convenience method that allows hackers to 
               create a blob from any stream or file like object.
        """
        assert "choices" not in arguments,"Choices do not mean anything in Blobs"
        if path and default:
            raise ValueError("You cannot use keyword arguments 'path'\
                and 'default' together")
        self.__size = size
        if path is not None:
            file = open(path,'rb')
            default = self.read(file)
        super(Blob,self).__init__(type = str, default = default, **arguments)
          
    @property
    def size(self):
        """
        Whatever you store in this Blob MUST not be larger than the 
        size property
        """
        return self.__size
    
    def indexed(self):
        '''Blobs cannot be indexed'''
        return False
        
    def validate(self,value):
        """Makes sure that whatever you are putting, does not exceed size"""
        value = super(Blob,self).validate(value)
        if self.size <= -1:
            return value
        inBytes = Size.inBytes(value)
        if not inBytes <= self.size :
            raise BadValueError("Your blob size must be less than:\
                %s , got: %s" % self.size, inBytes )
        return value
    
    def read(self,file):
        """
        Internal helper method that allows a blob a read a file, if the 
        file size if greater than the size of the Blob, the rest of the 
        contents of the file is ignored. i.e the blob only stores the number
        of bytes in self.size
        """
        with closing(file):
            data = file.read(self.size)
            return data
                     
    @staticmethod
    def fromFile(file, size = -1,**arguments):
        """
        Creates a Blob from this Stream or Filelike object. 
        It automatically closes the file after it is done. Be careful. 
        If you open a very large file, your memory will suffer !.
        """
        with closing(file):
            data = file.read(size)
            blob = Blob(size = size , default = data,**arguments)
            return blob
            
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
    
    def indexed(self):
        '''Blobs cannot be indexed'''
        return False
        
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
        if name in __defaults__: # Check if cls is a common descriptor.
            validate = __defaults__[name] # Retrieve a singleton to deal with this.
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
        raise BadValueError("Validation could not complete successfully, Please contact the mailing\
                             list or file a bug report, Thanks.")    

"""
List:
A descriptor that stores homogeneous lists, it works like the Set descriptor except
that Lists can accept duplicates. by default it is an empty list.
sample.

class Person(object):
    name = String()
    harem = List(Women)

person = Person()
person.harem.extend(["Aisha","Halima","Safia",])

"""
class List(UnIndexable):
    """Stores a List of objects,You can specify the type of the objects this list contains"""
    def __init__(self,cls = object, default = [], **arguments ):    
        self.cls = cls
        super(List, self).__init__(default, **arguments)
    
    def indexed(self):
        '''Lists cannot be indexed'''
        return False
        
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
        # Coercion is all or nothing. if any fails the entire operation fails
        name = self.cls.__name__
        if name in __defaults__: # Check if cls is a common descriptor.
            validate = __defaults__[name] # Retrieve a singleton to deal with this.
            for i in value:  # Normally Common descriptors take care of 'Nones'
                coerced.append(validate(i))
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
        raise BadValueError("Validation could not complete successfully, Please contact the mailing\
                             list or file a bug report, Thanks.")
                          
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
    
    def indexed(self):
        '''Blobs cannot be indexed'''
        return False
        
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
            keyVal = __defaults__[name] if name in __defaults__ else self.key
        if isinstance(self.value, type):
            val = self.value.__name__
            valueVal = __defaults__[val] if val in __defaults__ else self.value
            
        for k,v in value.items(): 
            key = keyVal(k) 
            value = valueVal(v)
            coerced[key] = value
        return coerced

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
class Boolean(Type):
    """Stores Boolean values, It coerces values like normal python bools"""
    type = bool


        
"""
URL:
A URL descriptor that validates strings to make sure they are valid URLs.
It inherits String, so you can use it like a string.It uses a Strings default length
of 500 chars, If you need a longer URL, modify its length property.

e.g.

class Person(object):
    name = String()
    harem = Set(Women)
    website = URL("http://harem.tumblr.com")
       
"""        
class URL(String):
    """Makes sure that a string you are creating is a valid URL"""
    
    def validate(self,value):
        """Uses urlsplit to validate urls"""
        value = super(URL,self).validate(value)
        if value is not None:
            scheme,domain,path,params,query,fragment = urlparse.urlparse(value)
            if not scheme or not domain:
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
    def __init__(self,default = None,autoNow = False, **arguments):
        self.autoNow = autoNow
        super(DateTime,self).__init__(default = default,type = datetime.datetime, 
            **arguments)
    
    def __get__(self,instance,owner):
        """Overrides get to implement autonow"""
        if self.autoNow:
            return self.now()
        return super(DateTime,self).__get__(instance,owner)
    
    def empty(value):
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
        
# __names__ are useful for getting supported common types
__names__ = {
               "Integer": Integer, "String": String, "Blob": Blob,
               "Set": Set, "Boolean": Boolean, "List": List, "URL": URL,
               "Time": Time, "DateTime": DateTime, "Date": Date, "Float": Float, "Map": Map
}             

## Common Singletons
__defaults__ = { name : value() for name, value in __names__.items() }  

