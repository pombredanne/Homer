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
Contains Model, Key and @key
"""
import copy
import datetime
from threading import Lock
from functools import update_wrapper as update
from contextlib import contextmanager as context

from homer.util import Validation
from homer.core.options import options
from homer.core.differ import Differ, DiffError


__all__ = ["Model", "key", ]

"""Module Variables """
log = options.logger("homer.core.models")
READWRITE, READONLY = 1, 2


"""Exceptions """
class BadKeyError(Exception):
    """An Exception that shows that something is wrong with your key"""
    pass

class BadValueError(Exception):
    """An exception that signifies that a validation error has occurred"""
    pass

class BadModelError(Exception):
    """Signifies that a Model was not decorated with @key"""
    pass
    
class UnDeclaredPropertyError(Exception):
    """An exception that is thrown if you try to set an attribute that in declared in a Model"""
    pass
        
"""
@key:
This decorator automatically configures your Model and creates
a key entry for it within the SDK. If you pass in an object
that is not a Model a BadKeyError is raised.

@key("link", namespace = "June")
class Profile(Model):
    link = URL("http://twitter.com")
    
  
"""
def key(name, namespace = "June"):
    """The @key decorator""" 
    def inner(cls):
        if issubclass(cls, Model):
            if hasattr(cls, name):
                KindMap.put(namespace, cls, name)
                return cls
            else:
                raise BadKeyError("There is no attribute with this name in %s" % cls)
        else:
            raise TypeError("You must pass in a subclass of  Model not: %s" % cls)
    return inner

"""
@cache:
This decorator is used to Signal that the decorated Model should only be
put in Redis only. i.e. This Model should not be put in Cassandra at all

@cache
@key("link")
class Profile(Model):
    link = URL("http://twitter.com")
"""
def cache(timeToLive = -1):
    """Mark this Model as one that you cache"""
    def inner(cls):
        pass
    return inner

"""
StoragePolicy:
This is class that affects how storage is actually done for a Model
i.e.
if cache and db is true instances will be put in Redis and Cassandra.
if cache is true and db is False instances will be put in only Redis, 
if db is True and cache is false instances will be put in only Cass-
andra; the timeToLive attribute directly affects the expiry times of
the object in Redis and Cassandra. Every model has a storage policy.

[Future additions to StoragePolicy may include ConsistencyLevel]
"""
class StoragePolicy(object):
    """An object that dictates how an object should be stored"""
    cache, db, timetoLive = True, True, -1

"""
KindMap(implementation detail):
A class that maps classes to their key attributes in a thread safe manner; 
This is an impl detail that may go away in subsequent releases.
"""
class KindMap(object):
    """Maps classes to attributes which will store their keys"""
    keyMap, typeMap = {}, {}
   
    @classmethod
    def put(cls, namespace, kind, key ):
        """Thread safe class that maps kind to key and namespace""" 
        assert isinstance(kind, type), "Kind has to be a class; Got: %s instead" % kind
        name = kind.__name__
        cls.keyMap[name] = namespace, key
        cls.typeMap[name] = kind
    
    @classmethod
    def get(cls, kind):
        """Returns a tuple (namespace, key) for this kind """
        name = kind.__class__.__name__
        if name in cls.keyMap:
            return cls.keyMap.get(name)
        else:
            raise BadModelError("Class %s is was not decorated with @key" % kind)
            
        
    @classmethod
    def classForKind(cls, name):
        """Returns the class object for this name"""
        return cls.typeMap.get(name, None)

"""
Key:
A GUID for Model objects. A Key contains all the information 
required to retreive a Model from Cassandra or Redis
Key is serialized to this String format:
"key: {namespace}, {kind}, {key}"
"""
class Key(object):
    """A GUID for Models"""
    namespace, kind, key = None, None, None
    
    def __init__(self, namespace, kind = None, key = None):
        """Creates a key from keywords or from a str representation"""
        if kind is None and key is None:
            try:
                key, repr = namespace.split(":")
                assert key == "key", "Key representation should start with 'key:'"
                namespace, kind, key = repr.split(",")
            except:
                raise BadKeyError("Expected String of format 'key:\
                    namespace, kind, key', Got: %s" % namespace)
        validate = Validation.validateString
        self.namespace, self.kind, self.key = \
            validate(namespace), validate(kind), validate(key)
    
    def complete(self):
        """Checks if this key has all its parts"""
        if self.namespace and self.kind and self.key:
            return True
        return False
    
    def toTagURI(self):
        """
        Returns a tag: URI for this entity for use in XML output
        
        Foreign keys for entities may be represented in XML 
        output as tag URIs. RFC 4151 describes the tag URI 
        scheme. From http://taguri.org/. Key tags take this 
        format: "tag:<namespace>, date:<kind>[<key>]" e.g.
        
            tag:June,2006-08-29:Profile[Jack]
            
        Raises a BadKeyError if this key is incomplete.
        """ 
        if not self.complete():
            raise BadKeyError("Cannot use an incomplete key for tag URI's")
        date = datetime.date.today().isoformat()
        format = u"tag:{0},{1}:{2}[{3}]"
        return format.format(self.namespace, date, self.kind, self.key)
        
    def __unicode__(self):
        """Unicode representation of a key"""
        format = u"key: {self.namespace}, {self.kind}, {self.key}"
        return format.format(self = self)
    
    def __str__(self):
        """String representation of a key"""
        return unicode(self)
   
"""
Property:
Base class for all data descriptors; 
"""
class Property(object):
    """A Generic Data Property which can be READONLY or READWRITE"""
    counter = 0
    def __init__(self, default = None, mode = READWRITE, **keywords):
        """Initializes the Property"""
        if mode not in [READWRITE, READONLY]:
            raise ValueError("@mode must be one of READONLY,\
            READWRITE")
        if mode == READONLY and default is None:
            raise ValueError("You must provide a @default value\
            in READONLY mode")
        self.mode = mode
        self.required = keywords.pop("required", False)
        self.choices = keywords.pop("choices", [])
        self.omit = keywords.pop("omit", False)
        self.name = None
        self.deleted = False
        self.default = default
        """Check for validators and default values"""
        if "validator" in keywords and callable(keywords["validator"]):
            self.validator = keywords["validator"]
            self.default = self.validate(default)
        elif keywords.get("validator", None) is None:
            self.validator = None
        else:
            raise ValueError("keyword: validator must be a callable or None")
        self.counter += 1
        
    def __set__(self, instance, value):
        """Put @value in @instance's class dictionary"""
        if self.mode == READONLY:
            raise AttributeError("This is a READONLY attribute")
        value = self.validate(value)
        if self.name is None : self.name = Property.search(instance,self)
        if self.name is not None:
            instance.__dict__[self.name] = value
            self.value = value
            self.deleted = False
        else:
            raise AttributeError("Cannot find %s in  %s " % (self,instance))

    def __get__(self, instance, owner):
        """Read the value of this property"""
        if self.name is None : self.name = Property.search(instance,self)
        if self.name is not None:
            try:
                if instance is not None:
                    return instance.__dict__[self.name]
                elif owner is not None:
                    return owner.__dict__[self.name]
                else:
                    raise ValueError("@instance and @owner can't both be null")   
            except (AttributeError,KeyError) as error:
                if not self.deleted:
                    return self.default
                else:
                    raise AttributeError("Cannot find %s in %s" 
                        % (self,instance))
        else:
            raise AttributeError("Cannot find %s in: %s" % 
                (self,instance))
           
    def __delete__(self, instance):
        """ Delete this Property from @instance """
        if self.deleted: return 
        if self.mode != READWRITE:
            raise AttributeError("This is NOT a READWRITE Property, Error")
        if self.name is None : self.name = Property.search(instance,self)
        if self.name is not None:
            try:
                del instance.__dict__[self.name]
                del self.value
                self.deleted = True
            except (AttributeError,KeyError) as error: raise error
        else:
            raise AttributeError("Cannot find Property: %s in: %s or its ancestors" 
                % (self,instance))
                   
    @staticmethod
    def search(instance, descriptor):
        """Returns the name of this descriptor by searching its class hierachy"""
        '''Search class dictionary first'''
        for name, value in instance.__class__.__dict__.items():
            if value is descriptor:
                return name
        '''Then search all the ancestors dictionary'''        
        for cls in type(instance).__bases__:
            for name, value in cls.__dict__.items():
                if value is descriptor:
                    return name
        return None
        
    def empty(self, value):
        """What does empty mean to this descriptor?"""
        return not value
                        
    def validate(self, value):
        """Asserts that the value provided is compatible with this property"""
        if self.required and self.empty(value):
            raise BadValueError("This property is required, it\
                cannot be empty") 
        if self.choices:
            if value not in self.choices:
                raise BadValueError("The property %s is %r; it must\
                    be on of %r"% (self.name, value, self.choices))
        if self.validator is not None:
            value = self.validator(value)
        return value
           
    def __configure__(self, name, owner):
        """Allow this property to know its name, and owner"""
        self.name = name
        self.owner = owner
    
    def __str__(self):
        return "Property: {self.name}".format(self = self)
   
"""
Type:
A Property that does type coercion, checking and validation. This is base
class for all the common descriptors.
#..
class Story(Record):
    source = Type(Blog)
    
#..
In the snippet above you can only set instances of blog or types that can
be coerced to blog on the source attribute; any other type will throw a
BadValueError

kwds:
'type' = The class that will be used during type checking and coercion
"""
class Type(Property):
    """Does type checking and coercion"""
    type = None
    def __init__(self, default = None, mode = READWRITE, type = None, **keywords):
        """Sets self.type and move along"""
        self.type = type if self.type is None else self.type
        Property.__init__(self, default, mode, **keywords)
            
    def validate(self, value):
        """Overrides Property.validate() to add type checking and coercion"""
        value = super(Type,self).validate(value)
        if self.type is None:
            return value
        if value is not None and not isinstance(value,self.type):
            try:
                if isinstance(value, list): value = self.type(*value)
                elif isinstance(value, dict): value = self.type(**value)
                else: value = self.type(value)
            except: 
                raise BadValueError("Cannot coerce: %s to %s"% (value, self.type))
        return value

"""
__Model__:
Called to create a new Model; It configures all the Properties 
in the Model and caches them so that subsequent discovery will 
be quick. 
"""
class __Model__(type):
    def __init__(cls, name, bases, dict):
        """ Initialize all the Properties in this Models Ancestral Hierachy"""
        print "Configuring %s" % cls.__name__
        fields = {}
        for root in reversed(cls.__mro__):
            for name, prop in root.__dict__.items():
                if isinstance(prop, Property):
                    prop.__configure__(name, cls)
                    fields[name] = prop
        cls.__fields__ = fields
        super(__Model__, cls).__init__(name, bases, dict)
        print "Finished configuring Model: %s " % cls.__name__
        print "Model: %s, fields: %s" % (cls.__name__, str(fields))
        
"""
Model: 
The Universal Unit of Persistence, a model is always 
aware of the changes you make to it; ergo models only
persist changes you make to it; thereby saving bandw-
idth.
simple usecase:

@key("name")
class Profile(Model):
    name = String(default = "John Bull")

profile = Profile(name = "Jane Doe")
profile.put() #save to datastore

found = Profile.get("Jane Doe") #Retrieval
assert profile == found

"""
class Model(object):
    __metaclass__ = __Model__
    
    def __init__(self, **kwds ):
        """Initializes properties in this Model from @kwds"""
        self.differ = Differ(self, exclude = ['differ',])
        for name in self.fields():
            if name in kwds:
                setattr(self, name, kwds[name])
        self.differ.commit() #commit the state of this differ.
                
    def key(self):
        """Unique Key for this Model"""
        namespace, key = KindMap.get(self)
        if hasattr(self, key):
            value = getattr(self, key)
            kind = self.__class__.__name__
            if value is not None:
                return Key(namespace, kind, value)
            raise BadKeyError("The value for %s is None" % key)
        raise BadKeyError("Incomplete Key for %s " % self)
    
    @classmethod     
    def put(cls, cache = False, timeToLive = -1):
        """Store this model into the datastore"""
        pass
    
    
    def kind(self):
        '''self.kind() is a shortcut for finding the name of a models class'''
        return self.__class__.__name__
          
    @classmethod
    def get(cls, *keys):
        """Try to retrieve an instance of this Model from the datastore"""
        pass
    
    @classmethod
    def all(cls):
        """Yields all the instances of this model in the datastore"""
        pass
        
    @classmethod
    def delete(cls, *keys ):
        """Deletes all the entities whose key is in @keys """
        pass
        
    def fields(self):
        """Returns a dictionary of all known properties in this object"""
        return self.__fields__  
    
    def __str__(self):
        format = "Model: %s" % (self.kind(),)
        return format
        
    def __unicode__(self):
        """Unicode representation of this model"""
        return u'%s' % self.__str__()
              

