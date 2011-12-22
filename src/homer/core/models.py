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
from weakref import WeakValueDictionary
import datetime
from functools import update_wrapper as update
from contextlib import contextmanager as context

from homer.core.builtins import object
from homer.util import Validation
from homer.core.differ import Differ, DiffError


__all__ = ["Model", "key",]

READWRITE, READONLY = 1, 2
Limit = 5000

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
    """An exception that is thrown if you try to set an attribute that is not declared in a Model"""
    pass

class NamespaceCollisionError(Exception):
    """An Exception that is thrown when you declare to classes with the same name in one namespace"""
    pass
        
"""
@key:
This decorator automatically configures your Model, and creates
a key entry for it within the SDK. If you pass in an object
that is not a Model a TypeError is raised.

@key("link")
class Profile(Model):
    link = URL("http://twitter.com")
    
"""
def key(name, namespace = None):
    """The @key decorator""" 
    def inner(cls):
        if issubclass(cls, Model):
            Schema.Put(namespace, cls, name)
            return cls
        else:
            raise TypeError("You must pass in a subclass of  Model not: %s" % cls)
    return inner
    
"""
Schema:
Holds Global Storage Configuration for all Models. It stores things like
the key attribute of a Model, Its cache expiration settings, finally it
maps names to classes which is useful during deserialization.
"""
class Schema(object):
    """Maps classes to attributes which will store their keys"""
    schema, keys = {}, {}
    
    @classmethod
    def Put(cls, namespace, model, key):
        """Stores Meta Information for a particular class"""
        kind = model.__name__    
        if not namespace in cls.schema:
            cls.schema[namespace] = WeakValueDictionary()    
        if kind not in cls.schema[namespace]:
            cls.schema[namespace][kind] = model
            cls.keys[id(model)] = (namespace, kind, key, )
        else:
            raise NamespaceCollisionError("Model: %s already exists\
                in the Namespace: %s" % (model, namespace))
    
    @classmethod
    def clear(cls):
        '''Clears the internal state of the Schema object'''
        cls.schema.clear()
        cls.keys.clear()
              
    @classmethod
    def Get(cls, model):
        """Returns a tuple [namespace, kind, key, expiration] for this Model"""
        try:
            model = model if isinstance(model, type) else model.__class__
            return cls.keys[id(model)]
        except KeyError:
            raise BadModelError("Class: %s is not a valid Model, are you sure it has an @key; ",(model))
    
    @classmethod
    def ExpiresIn(cls, model):
        """Returns the expiration setting for this model in seconds
           @model : An instance of Model.
        """
        return cls.Get(model)[2] # Returns the expiration flag for the kind.
    
    @classmethod
    def ClassForModel(cls, namespace, name):
        """Returns the class object for the Model with @name"""
        try:
            return cls.schema[namespace][name]
        except KeyError:
            raise BadModelError("There is no Model with name: %s" % name)

"""
Key:
A GUID for Model objects. A Key contains all the information 
required to retreive a Model from any Backend
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
                assert key == "key", "Key representation\
                    should start with 'key:'"
                namespace, kind, key = repr.split(",")
            except:
                raise BadKeyError("Expected String of"\
                    + "format 'key: namespace, kind, key', Got:%s" % namespace)
        validate = Validation.validateString
        self.namespace, self.kind, self.key =\
            validate(namespace), validate(kind), key #We do not validate the key.
    
    def isComplete(self):
        """Checks if this key has a namespace, kind and key"""
        if self.namespace and self.kind and self.key:
            return True
        return False
        
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
            raise ValueError("@mode must be one of READONLY,READWRITE")
        if mode == READONLY and default is None:
            raise ValueError("You must provide a @default value in READONLY mode")
        self.mode = mode
        self.required = keywords.pop("required", False)
        self.choices = keywords.pop("choices", [])
        self.omit = keywords.pop("omit", False)
        self.indexed = keywords.pop("indexed", False)
        self.ttl = keywords.pop("ttl", None)
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
        if self.name is None : self.name = Property.search(instance, None,self)
        if self.name is not None:
            instance.__dict__[self.name] = value
            self.deleted = False
        else:
            raise AttributeError("Cannot find %s in  %s " % (self,instance))
    
    def __get__(self, instance, owner):
        """Read the value of this property"""
        if self.name is None : self.name = Property.search(instance, owner,self)
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
            raise AttributeError("Cannot find any property named %s in: %s" % 
                (self.name, owner))
           
    def __delete__(self, instance):
        """ Delete this Property from @instance """
        if self.deleted: return 
        if self.mode != READWRITE:
            raise AttributeError("This is NOT a READWRITE Property, Error")
        if self.name is None : self.name = Property.search(instance, None ,self)
        if self.name is not None:
            try:
                del instance.__dict__[self.name]
                self.deleted = True
            except (AttributeError,KeyError) as error: raise error
        else:
            raise AttributeError("Cannot find Property: %s in: %s or its ancestors" 
                % (self,instance))
    
    def __call__(self, value):
        """A shortcut to self.validate(value)"""
        return self.validate(value)
                             
    @staticmethod
    def search(instance, owner, descriptor):
        """Returns the name of this descriptor by searching its class hierachy"""
        '''Search class dictionary first'''
        if instance is not None:
            for name, value in instance.__class__.__dict__.items():
                if value is descriptor:
                    return name
            '''Then search all the ancestors dictionary'''        
            for cls in type(instance).__bases__:
                for name, value in cls.__dict__.items():
                    if value is descriptor:
                        return name
        elif owner is not None:
            for name, value in owner.__dict__.items():
                if value is descriptor:
                    return name
            '''Then search all the ancestors dictionary'''        
            for cls in owner.__bases__:
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
    
    def convert(self, instance):
        '''Yields the datastore representation of its value'''
        return str(getattr(instance, self.name))
    
    def deconvert(self, instance, value):
        '''Converts a value from the datastore to a native python object'''
        return self.__set__(instance, value)
           
    def configure(self, name, owner):
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
    
    def __call__(self, value):
        """A shortcut to self.validate(value)"""
        return self.validate(value)
              
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

###
# Model and Its Friends
###
from copy import copy, deepcopy
from homer.backend import Simpson
"""
Model: 
The Universal Unit of Persistence, a model is always 
aware of the changes you make to it; ergo models persist
only changes you make to them; thereby saving bandwidth.

Simple usecase:

@key("name")
class Profile(Model):
    name = String("John Bull")

"""
class Model(object):
    '''Unit of persistence'''
    def __init__(self, **kwds ):
        """Creates an instance of this Model"""
        self.differ = Differ(self, exclude = ['differ', 'properties'])
        self.properties = set()
        required = set()
        for name, prop in self.fields().items():
            self.properties.add(name)
            prop.configure(name, type(self))
            if name in kwds:
                setattr(self, name, kwds[name])
       
    def key(self):
        """Unique key for identifying this instance"""
        namespace, kind, key = Schema.Get(self)
        if hasattr(self, key):
            value = getattr(self, key)
            if value is not None:
                key = value() if callable(value) else value
                return Key(namespace, kind, key)
            raise BadKeyError("The value for %s is None" % key)
        raise BadKeyError("Incomplete Key for %s " % self)
           
    def rollback(self):
        '''Undoes the current state of the object to the last committed state'''
        self.differ.revert();
    
    def save(self, cache = True):
        """Stores this object in the datastore and in the cache"""
        #Todo: Check that all required properties are set before every save.
        print 'Putting %s at the backend' % self
        Simpson.put(self)
        self.differ.commit()
               
    @classmethod
    def read(cls, keys, cache = True):
        """Retreives objects from the datastore, if @cache check the cache"""
        return Simpson.read(*keys)
    
    @classmethod
    def kind(cls):
        """The Type Name of @self in the Datastore"""
        return cls.__class__.__name__
        
    @classmethod
    def delete(cls, keys, cache = True):
        """Deletes this Model from the datastore and cache"""
        Simpson.delete(*keys)
       
    @classmethod
    def cql(cls, query, *args, **kwds):
        """Interface to Cql from your model, which yields models"""
        return CqlQuery('SELECT * FROM %s %s' % (cls.kind()
            , query), *args, **kwds)
    
    @classmethod
    def all(cls, limit = Limit):
        """Yields all the instances of this model in the datastore"""
        return CqlQuery('SELECT * FROM %s LIMIT=%s'% (cls.kind(), limit))
        
    def fields(self):
        """Returns all the Descriptors for @this by searching the class heirachy"""
        cls = self.__class__;
        fields = {}
        for root in reversed(cls.__mro__):
            for name, prop in root.__dict__.items():
                if isinstance(prop, Property):
                    fields[name] = prop
        return fields
    
    def keys(self):
        '''Returns a copy of all the keys in this model excluding the key property'''
        return copy(self.properties)
    
    def values(self):
        '''Returns all the values in this Model excluding the value for the key property'''
        result = []
        print self.keys()
        for name in self.keys():
            result.append(getattr(self, name))
        return copy(result)
    
    def __setitem__(self, key, value):
        '''Equivalent to calling setattr(instance, key, value) on this object'''
        setattr(self, key, value)
        self.properties.add(key)
        
    def __getitem__(self, key):
        '''Allows dictionary style access'''
        return getattr(self, key)
        
    def __delitem__(self, key):
        ''' Allows us to delete a deletable Property on this object'''
        delattr(self, key)
        self.properties.remove(key)
    
    def items(self):
        '''Returns a copy of key value pair of every property in the Model'''
        results = []
        for name in self.keys():
            results.append((name, getattr(self, name)))
        return results
            
    def iterkeys(self):
        '''Yields all the keys one by one'''
        for i in self.keys():
            yield i
    
    def itervalues(self):
        '''Yields all the values one by one'''
        for i in self.values():
            yield i
        
    def iteritems(self):
        '''Yields a key, value pair of each object'''
        results = []
        for name in self.keys():
            yield name, getattr(self, name)
           
    def __len__(self):
        '''How many properties are contained in this object'''
        return len(self.properties)
    
    def __contains__(self, key):
        '''Does this model contain this key'''
        return key in self.properties
        
    def __str__(self):
        '''A String representation of this Model'''
        format = "Model: %s" % (self.kind(),)
        return format
        
    def __unicode__(self):
        """Unicode representation of this model"""
        return u'%s' % self.__str__()
       
              

