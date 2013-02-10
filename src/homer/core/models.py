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
import codecs
import datetime
import cPickle as pickle
from copy import copy, deepcopy
from weakref import WeakValueDictionary
from functools import update_wrapper as update
from contextlib import contextmanager as context

from .builtins import object, fields
from .differ import Differ, DiffError

READWRITE, READONLY = 1, 2
__all__ = [ 
            "Model", "key", "Key", "Reference", "KeyHolder", "Property", "Type",
            "UnIndexable", "UnIndexedType", "READONLY", "READWRITE",
]

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
    
class NamespaceCollisionError(Exception):
    """An Exception that is thrown when you declare to classes with the same name in one namespace"""
    pass
    
class ReservedNameError(Exception):
    """Thrown to signify that you've tried to use a reserved name"""
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
        if issubclass(cls, BaseModel):
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
    schema, keys, initialized = {}, {}, set()
    
    @classmethod
    def Initialize(cls, instance):
        '''Tracks the Id of every model that has been initialized'''
        assert isinstance(instance, BaseModel), "You must pass in a model instance"
        cls.initialized.add(id(instance))
        #Do Pre-Storage Initialization Here if necessary
    
    @classmethod
    def Initialized(cls, instance):
        '''Checks if a Model was previously initialized'''
        return id(instance) in cls.initialized   
        
    @classmethod
    def Put(cls, namespace, model, key):
        """Stores Meta Information for a particular class"""
        from homer.options import CONFIG
        if not namespace:
            namespace = CONFIG.DEFAULT_NAMESPACE
        kind = model.__name__    
        if not namespace in cls.schema:
            cls.schema[namespace] = WeakValueDictionary()    
        if kind not in cls.schema[namespace]:
            cls.schema[namespace][kind] = model
            cls.keys[id(model)] = (namespace, kind, key, )
        else:
            raise NamespaceCollisionError("Model: %s already \
                exists in the Namespace: %s" % (model, namespace))
    
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
            raise BadModelError("Class: %s is not a valid Model; ",(model))
    
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
    def __init__(self, namespace, kind = None, id = None):
        """Creates a key from keywords or from a str representation"""
        self.namespace = namespace
        self.kind = kind
        self.id = id
        self.saved = False
        self.columns = []
     
    def complete(self):
        """Checks if this key has a namespace, kind and key"""
        if bool(self.namespace) and bool(self.kind) and bool(self.id):
            return True
        else:
            return False
    
    def __hash__(self):
        '''A Key object is hashable'''
        return hash(repr(self))

    def __unicode__(self):
        """Unicode representation of a key"""
        format = u"Key('{self.namespace}', '{self.kind}', '{self.id}')"
        return format.format(self=self)
    
    def __eq__(self, other):
        '''Compare two keys for equality'''
        return self.namespace == other.namespace and self.kind\
            == other.kind and self.id == other.id
    
    def __repr__(self):
        format = "Key('{self.namespace}', '{self.kind}', '{self.id}')"
        return format.format(self = self)

"""
Converters and Descriptors:
A converter is a single class that contains methods for coercion, validation
and transformation to and from data store entities, A descriptor is a special
converter that is also a python descriptor, allowing users of descriptors
to do coercion, and validation on attributes of their class.
"""
class Converter(object):
    '''The contract for all converters'''
    
    def __call__(self, value):
        '''A shortcut to validate'''
        return self.validate(value)
        
    def validate(self, value):
        '''Basic Definition just returns the value passed to it'''
        return value
        
    def convert(self, value):
        '''Returns the datastore suitable repr of @value'''
        value = self.validate(value)
        return pickle.dumps(value)
    
    def deconvert(self, value):
        '''Converts a @value which is a datastore repr to a native python object'''
        return pickle.loads(value)
  
         
"""
Property:
Base class for all data descriptors; 
"""
class Property(Converter):
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
        self.__indexed = keywords.pop("indexed", False)
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
            if hasattr(instance, "__store__"):
                instance.__store__[self.name] = value
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
                if hasattr(instance, "__store__"):
                    del instance.__store__[self.name]
                self.deleted = True
            except (AttributeError,KeyError) as error: raise error
        else:
            raise AttributeError("Cannot find Property: %s in: %s or its ancestors" 
                % (self,instance))
   
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
        return value is None
                        
    def validate(self, value):
        """Asserts that the value provided is compatible with this property"""
        if self.required and self.empty(value):
            raise BadValueError("Property: %s is required, it cannot be empty" % self.name) 
        if self.choices:
            if value not in self.choices:
                raise BadValueError("The property %s is %r; it must be on of %r"% (self.name, value, self.choices))
        if self.validator is not None:
            value = self.validator(value)
        return value
    
    def indexed(self):
        '''Checks if this property should be indexed'''
        return self.__indexed
        
    def saveable(self):
        '''All descriptors can be saved by default'''
        return True
           
    def configure(self, name, owner):
        """Allow this property to know its name, and owner"""
        self.name = name
        self.owner = owner
    
    def __str__(self):
        '''String representation of a Property'''
        return "Property: {self.name}".format(self = self)

"""
UnIndexable:
The base class of all Properties that cannot be indexed. Normally
properties that cannot be indexed will be pickled into the datastore
"""
class UnIndexable(Property):
    '''A Property that cannot be indexed'''
    
    def convert(self, value):
        '''Pickles this object to the datastore'''
        return pickle.dumps(value)
    
    def deconvert(self, value):
        '''Converts a raw datastore back to a native python object'''
        loaded = pickle.loads(value)
        return loaded
        
    def indexed(self):
        '''An un-indexable property cannot be indexed'''
        return False

"""
UnSaveable:
The base class of all descriptors that cannot be saved.
"""
class UnSaveable(Property):
    '''A Property that cannot be persisted'''
    
    def indexed(self):
        '''All Unsaveable descriptors cannot be indexed'''
        return False
        
    def saveable(self):
        '''All unsaveable descriptors cannot be saved'''
        return False
    
'''
Default:
A Descriptor that is a shortcut for creating default types.
'''
class Default(UnSaveable):
    '''Used to create default descriptors for Models'''
    def __init__(self, key=Converter, value=Converter):
        '''Simple stash for Descriptors for  Models'''
        assert issubclass(key, Converter), "%s must be an instance of Converter" % key
        assert issubclass(value, Converter), "%s must be an instance of Converter" % value
        self.key, self.value = key, value

    def __set__(self, instance, value):
        """Put @value in @instance's class dictionary"""
        raise AttributeError("A Default Property is Read only")
    
    def __get__(self, instance, owner):
        """Read the value of this property"""
        return self.key, self.value
           
    def __delete__(self, instance):
        """ Delete this Property from @instance """
        raise AttributeError("A Default Property cannot be deleted")
          
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
                if isinstance(value, list) or isinstance(value, tuple): value = self.type(*value)
                elif isinstance(value, dict): value = self.type(**value)
                else: value = self.type(value)
            except: 
                raise BadValueError("Cannot coerce: %s to %s"% (value, self.type))
        return value

"""
UnIndexedType:
A Type that cannot be indexed
"""
class UnIndexedType(UnIndexable, Type):
    '''A Type that cannot be indexed'''
    pass

from homer.backend import Lisa, CqlQuery, FetchMode

"""
Reference:
A Pointer to another Model that has been persisted
in the database. The Reference property is not fool hardy. i.e.
It does not verify if the Model it points to exists or not on cassandra.
It only checks that the model you are trying to set on it has a complete key.
"""  
class Reference(Property):
    '''A Pointer to another persisted Model'''
    def __init__(self, cls, default = None, **arguments):
        '''Override the properties constructor'''
        assert issubclass(cls, BaseModel), "A Reference must point to a Model"
        self.cls = cls
        Property.__init__(self, default, **arguments)
    
    def convert(self, value):
        '''References are stored as Keys in the datastore'''
        value = self.validate(value)
        if isinstance(value, BaseModel):
            return repr(value.key())
        else: 
            return repr(None)
        
    def deconvert(self, value):
        '''Pulls the referenced model from the datastore, and sets it'''
        key = eval(value) #Change the @value back to a key.
        if key:
            found = Lisa.read(key, FetchMode.All)
            return found
        else: return None
         
    def validate(self, value):
        '''Makes sure you can only set a Model or a Key on a Reference'''
        if value is None:
            return None
        if isinstance(value, self.cls):
            key = value.key()
        else:
            raise BadValueError("You must use a subclass of: %s" % self.cls.__name__)
        assert key.complete(), "Your %s's key must be complete" % value
        return value

"""
KeyHolder:
A KeyHolder is a data descriptor that is designed for storing complete
keys in the datastore. It knows how to convert models to Key objects if
necessary. If the `cls` keyword parameter is provided it does type checking
on on the keys before storage.
"""
class KeyHolder(Property):
    '''A descriptor that stores a single complete key'''
    def __init__(self, cls=None, **keywords):
        '''initialize a KeyHolder'''
        if cls:
            assert issubclass(cls, Model), "You must pass in a subclass of Model"
        self.cls = cls
        super(KeyHolder, self).__init__(**keywords)

    def convert(self, value):
        '''Does a repr() on a key object'''
        return repr(value)

    def deconvert(self, value):
        '''Does an eval() on a string value to return an key'''
        val = eval(value)
        assert isinstance(val, Key), "Value didn't convert to a Key"
        return val
    
    def validate(self, value):
        '''Validates any object put in a key holder'''
        assert isinstance(value, Key) or isinstance(value, Model),\
            "You must pass in a Model or Key to a KeyHolder not a : %s" % value
        if self.cls:
            if isinstance(value, Model):
                assert isinstance(value, self.cls),"You must provide an instance of %s" % self.cls.__name__
            else:
                assert isinstance(value, Key)
                kind = getattr(value, "kind", None)
                assert kind is not None, "You must provide a complete key, GOT: %s" % value
                assert kind == self.cls.__name__, "Invalid kind got: %s require: %s" % (kind, self.cls.__name__)
        if isinstance(value, Model):
            value = value.key()
        if not value.complete():  
            raise BadValueError("Your key is not complete")
        return value

"""
Basic:
Represents a type that you can convert and deconvert with str()
"""
class Basic(Type):
    '''A Type that can be converted with str'''

    def convert(self,  value):
        '''Converts the basic type with the str operation'''
        codec = codecs.lookup("utf-8")
        value = self.validate(value)
        if not isinstance(value, basestring):
            value = str(value)
        return codec.encode(value)[0]
        
    def deconvert(self, value):
        '''Since we are expecting a str, we just return the value'''
        return value

"""
BaseModel:
The Base class of all model related objects, It
supports the dictionary protocol.
"""
class BaseModel(object):
    '''The objects that all Models inherit'''

    def __new__(cls, *arguments, **keywords):
        '''Customizes all Model instances to include special attributes'''
        instance = object.__new__(cls, *arguments, **keywords)
        instance.__store__ = {} #We need a Store for the differ to work.
        return instance

    def __init__(self):
        self.differ = Differ(self, exclude = ['differ',])

    def key(self):
        raise NotImplemented("Use a subclass of BaseModel")

    def __setitem__(self, name, value):
        raise NotImplemented("Use a subclass of BaseModel")

    def __getitem__(self, name):
        raise NotImplemented("Use a subclass of BaseModel")

    def __delitem__(self, name):
        raise NotImplemented("Use a subclass of BaseModel")
               
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
class Model(BaseModel):
    '''Unit of persistence'''
    def __new__(cls, *arguments, **keywords):
        '''Customizes all Model instances to include special attributes'''
        instance = BaseModel.__new__(cls, *arguments, **keywords)
        if not hasattr(cls, "default"):
            cls.default = Default()
        [prop.configure(name, cls) for name, prop in fields(cls, Property).items()] 
        return instance
        
    def __init__(self, **kwds ):
        """Creates an instance of this Model"""
        super(Model, self).__init__()
        self.__key = None 
        for name, value in kwds.items():
            self[name] = value
            
    def key(self):
        """Unique key for identifying this instance"""
        def validate(name):
            '''Compute the key if necessary and validate'''
            found = getattr(self, name)
            value = found() if callable(found) else found
            if value is None:
                raise BadKeyError("The key for %s cannot be None" % self)
            return str(value)  
        if self.__key is None:
            namespace, kind, key = Schema.Get(self)
            self.__id = key
            value = validate(key)
            self.__key = Key(namespace, kind, value)
        else:
            self.__key.id = validate(self.__id)
        return self.__key
                  
    def rollback(self):
        '''Undoes the current state of the object to the last committed state'''
        self.differ.revert();
    
    def save(self):
        """Stores this object in the datastore and in the cache"""
        # Makes sure that all required properties are available before persistence.
        for name, prop in fields(self, Property).items():
            if hasattr(prop, 'required') and prop.required:
                value = getattr(self, name)
                if prop.empty(value):
                    raise BadValueError("Property: %s is required" % name)
        
        Lisa.save(self)
        self.differ.commit()
               
    @classmethod
    def read(cls, key, mode = FetchMode.All):
        """Retreives objects from the datastore """
        assert isinstance(key, (basestring, Key))
        namespace, kind, member = Schema.Get(cls)
        if isinstance(key, Key):
            assert kind == key.kind, "Mismatched Model, reading a %s with %s" % (kind, key.kind)
            return Lisa.read(key, mode)
        else: 
            key = Key(namespace, kind, key)
            return Lisa.read(key, mode)
    
    @classmethod
    def kind(cls):
        """The Type Name of @self in the Datastore"""
        return cls.__name__
        
    @classmethod
    def delete(cls, *keys):
        """Deletes this Model from the datastore and cache"""
        todelete = []
        namespace, kind, member = Schema.Get(cls)
        for key in keys:
            assert isinstance(key, str)
            todelete.append(Key(namespace, kind, key)) 
        Lisa.delete(*todelete)
       
    @classmethod
    def query(cls, **kwds):
        """Interface to Cql from your model, which yields models"""
        #NOTE: Only static properties can be indexed by homer, 
        #      so we don't worry about querying for dynamic properties
        query = ""
        started = False
        for name in kwds:
            if not started:
                pattern = "%s=:%s" % (name, name)
                query += pattern
                started = True
            else:
                pattern = " AND %s=:%s" % (name, name)
                query += pattern

        q = 'SELECT * FROM %s WHERE %s' % (cls.kind(), query)
        query = CqlQuery(cls, q, **kwds)
        query.convert = True
        return query
    
    @classmethod
    def all(cls):
        '''Returns all instances of this Model stored in the datastore'''
        query = CqlQuery(cls, "SELECT * FROM %s" % cls.kind())
        return query

    @classmethod
    def count(cls, **keywords):
        '''Counts all the instances of this Model from the datastore'''
        if not keywords:
            return CqlQuery(cls, "SELECT COUNT(*) FROM %s;" %(cls.kind(),)).fetchone()
        else:
            # Dynamically build the WHERE clause.
            extras = ""
            started = False
            for name in keywords:
                if not started:
                    pattern = "%s=:%s" % (name, name)
                    extras += pattern
                    started = True
                else:
                    pattern = " AND %s=:%s" % (name, name)
                    query += pattern
            q = "SELECT COUNT(*) FROM %s WHERE %s;" % (cls.kind(), extras)
            query = CqlQuery(cls, q, **keywords)
            query.convert = True
            return query.fetchone()
         
    def keys(self):
        '''Returns a copy of all the keys in this model excluding the key property'''
        return copy(self.__store__.keys())
    
    def values(self):
        '''Returns all the values in this Model excluding the value for the key property'''
        result = []
        for name in self.keys():
            result.append(self[name])
        return copy(result)
    
    def __setitem__(self, key, value):
        '''Allows dictionary style item sets to behave properly'''
        props = fields(self, Property)
        if key in props:
            setattr(self, key, value) 
        else:
            # TODO: Maybe I should cache the Converter instead of creating it every time.
            k, v = self.default
            k = k() if isinstance(k, type) else k  #Construct the converter object if necessary
            v = v() if isinstance(v, type) else v
            self.__store__[k(key)] = v(value)
    
    def __getitem__(self, key):
        '''Allows dictionary style item access to behave properly'''
        return self.__store__[key]
    
    def __delitem__(self, key):
        '''Allows dictionary style item deletions to work properly'''
        props = fields(self, Property)
        if key in props:
            delattr(self, key) 
        else:
            del self.__store__[key]
            
    def items(self):
        '''Returns a copy of key value pair of every property in the Model'''
        results = []
        for name in self.keys():
            results.append((name, self[name]))
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
            yield name, self[name]
    
    def __eq__(self, other):
        '''Two Models are equal if and only if their keys are equal'''
        return self.key() == other.key()
            
    def __len__(self):
        '''How many properties are contained in this object'''
        return len(self.__store__)
    
    def __contains__(self, key):
        '''Does this model contain this key'''
        return key in self.__store__
        
    def __str__(self):
        '''A String representation of this Model'''
        format = "Model: %s" % (self.kind(), )
        return format
        
    def __unicode__(self):
        """Unicode representation of this model"""
        return u'%s' % str(self)
       
              

