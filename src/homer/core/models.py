#!/usr/bin/env python
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

from homer.util import Validator
from homer.core.options import options



__all__ = ["Model", "key", ]

"""Module Variables """
log = options.logger("homer.core.models")
READWRITE, READONLY = 1, 2


"""Exceptions """
class BadKeyError(Exception):
    pass

"""Exceptions"""
class BadValueError(Exception):
    """An exception that signifies that a validation error has occurred"""
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
                KindMap.putKey(cls, name, namespace)
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
def cache(timeout = -1):
    """Mark this Model as one that you cache"""
    pass


class CachePolicy(object):
    """An object that dictates how an object should be cached"""
    pass
    
"""
Property:
Base class for all data descriptors; 
"""
class Property(object):
    """A Generic Data Property which can be READONLY or READWRITE"""
    
    def __init__(self, default = None, mode = READWRITE, **keywords):
        """Initializes the Property"""
        if mode not in [READWRITE, READONLY]:
            raise ValueError("mode must be one of READONLY,\
            READWRITE")
        if mode == READONLY and default is None:
            raise ValueError("You must provide a default value\
            in READONLY mode")
        self.mode = mode
        self.required = keywords.get("required", False)
        self.choices = keywords.get("choices", [])
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
            raise AttributeError("Cannot find this property:%s in \
                this the given object: %s " % (self,instance))

    def __get__(self, instance, owner):
        """Read the value of this property"""
        if self.name is None : self.name = Property.search(instance,self)
        if self.name is not None:
            try:
                if instance is not None:
                    found = instance.__dict__[self.name] 
                    return found  
                elif owner is not None:
                    found = owner.__dict__[self.name]
                    return found
                else:
                    raise ValueError("@instance and @owner can't both be null")   
            except (AttributeError,KeyError) as error:
                if not self.deleted:
                    return self.default
                else:
                    raise AttributeError("Cannot find Property: %s in: %s" 
                        % (self,instance))
        else:
            raise AttributeError("Cannot find Property:%s in: %s" % 
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
            raise AttributeError("Cannot find Property: %s in: %s" 
                % (self,instance))
                   
    @staticmethod
    def search(instance, descriptor):
        """Returns the name of this descriptor by searching its class hierachy"""
        for name, value in instance.__class__.__dict__.items():
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
    
    def isSimple(self):
        """Is this property a simple property ?; simple as in XML Schemas"""
        return False
    
    def isComplex(self):
        """Is this property a complex property ?; complex as in XML Schemas"""
        return False
        
    def isSequence(self):
        """Will this property qualify as a Sequence type in an XML Schema definition?"""
        return False
           
    def __configure__(self, name, owner):
        """Allow this property to know its name"""
        self.name = name
    
    def __str__(self):
        return "Property: {self.name}".format(self = self)
   
"""
Type:
A Property that does type coercion, checking and validation. This is base
class for all the common descriptors. look at the example below for 
clarification.
#..
class Story(Record):
    source = Type(Blog)
    
#..
The snippet above will make sure that you can only set Blog objects on
source. If you try to set a different type of object; Type will attempt to
convert this object to a blog by coercion i.e calling Blog(object). if this
fails it raises a BadValueError.

Keywords:
type = The type that will be used during type checking and coercion
omit = Tells the SDK that you do not want to the property to be persisted
       or marshalled.
"""
class Type(Property):
    type = None
    def __init__(self, default = None, mode = READWRITE, type = None, **keywords):
        """Sets a type, checks if type is simple, complex or sequence"""
        self.omit = keywords.pop("omit", False)
        self.type = type if self.type is None else self.type
        Property.__init__(self, default, mode, **keywords)
        
         
    def validate(self, value):
        """Overrides Property.validate() to add type checking and coercion"""
        value = super(Type,self).validate(value)
        if self.type is None:
            return value
        if value is not None and not isinstance(value,self.type):
            try:
                value = self.type(value)
            except: 
                raise BadValueError("Cannot coerce: %s to %s"% (value, self.type))
        return value
       
"""
KindMap(implementation detail):
A class that maps classes to their key attributes in a thread safe manner; 
This is an impl detail that may go away in subsequent releases.
"""
class KindMap(object):
    """Maps classes to attributes which will store their keys"""
    lock, keyMap, typeMap = Lock(), {}, {}
   
    @classmethod
    def putKey(cls, kind, key, namespace = None):
        """Thread safe class that maps kind to key and namespace"""
        with cls.lock: 
            assert isinstance(kind, type), "Kind has to be a\
                class; Got: %s instead" % kind
            name = kind.__name__
            cls.keyMap[name] = key, namespace
            cls.typeMap[name] = kind
    
    @classmethod
    def getKey(cls, kind):
        """Returns a tuple (key, namespace) for this kind or None"""
        with cls.lock:
            name = kind.__class__.__name__
            return cls.keyMap.get(name, None)
    
    @classmethod
    def classForKind(cls, name):
        """Returns the class object for this name"""
        with cls.lock:
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
        validate = Validator.ValidateString
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
ActiveModels:
Tracks all Models that exists; active(instances) or dormant
(just defined classes).
"""
class ActiveModels(object):
    """Keeps track of all model classes and instances"""
    
    @classmethod
    def active(cls):
        """Return all existing Model instances"""
        pass
    
    @classmethod
    def get(cls, key):
        """ Return an instance that has this key; else return None """
        pass
        
    @classmethod   
    def all(cls):
        """Returns all defined Model classes"""
        pass
        
"""
__configure__:
Called to create a new Model; It configures all the Properties 
in the Model and caches them so that subsequent discovery will 
be efficient.
"""
class __configure__(type):
    def __new__(cls, name, bases, dict):
        """ Where the magic occurs """
        props = {}
        for key, prop in dict.items():
            if isinstance(prop, Property):
                prop.__configure__(key)
                props[key] = prop
                print "Just configured: " + str(prop)
                
        dict["__fields__"] = props
        return type.__new__(cls, name, bases, dict)
                          
"""
Model: 
The Universal Unit of Persistence.
usecase:

@key("name")
class Profile(Model):
    name = String("John Bull")
    
"""
class Model(object):
    __metaclass__ = __configure__
      
    def key(self):
        """Create and Return the Key for this Model or return None"""
        pass
    
    def rollback(self):
        """Rollback changes you've made on your Model"""
        pass
        
    def put(cache = True, timeout = -1):
        """Put this model in Cassandra and Redis if cache is True"""
        pass
    
    @classmethod
    def all(cls):
        """Retreives all the instances of this Model from the Cassandra"""
        pass
        
    @classmethod
    def get(cls, key, cache = True):
        """Try to retrieve an instance of this Model from the datastore"""
        pass
    
    def cache(timeout = -1):
        """Stores this model in Redis only"""
        pass
            
    def fields(self):
        """Returns a dictionary of all known properties in this object"""
        return self.__fields__


"""
View:
Base class of all objects that know how to track changes
"""
class View(object):
    """Base class for all views"""
    tracking = True
    
    def track(self, object):
        raise NotImplementedError("Use a concrete subclass of View")
        
    @context
    def block(self):
        """Block tracking while you execute this context"""
        tracking = False
        yield
        tracking = True

"""
ModelView:
A ThreadSafe way to track changes to Models; 
The differences between NormalView and ModelView are:

1. ModelView tracks only instances of Model.
2. ModelView loops through Properties in a Model and tracks them too. unless if
   the Property stores a Model of course.
3. ModelView yields all the Views for the properties in the Model it tracks 
   through the ModelView.view() method.
   
"""   
class ModelView(View):
    """A ThreadSafe way to track changes to Model objects"""
    
    def __init__(self, Model):
        """inits lock object and modification sets"""
        if isinstance(Model, Model):
            raise TypeError("Expected: a instance of Model, Got: %s" % Model)
        self.lock = Lock()
        self.Model = Model
        self.changedSet, self.delSet = set(), set()
        self.track()
    
    def view(self):
        """Returns a dict containing attributes of this self.Model and their views"""
        pass
        
    def deleted(self):
        '''Returns a set of all the attributes that have been deleted'''
        return copy.deepcopy(self.delSet)
        
    def modified(self):
        '''Returns a set of the attributes that have changed'''
        return copy.deepcopy(self.changedSet)
    
    def flush(self):
        """Empty all tracking information and start afresh;
        
           This will useful if a Model is reloaded from the 
           datastore or when it is saved. basically it resets
           self.originals
        """
        pass
        
    def track(self):
        '''Track changes on self.Model and its attributes'''
        log.info("Tracking Model: %s for changes" % object)
        SET = getattr(self.Model, "__setattr__")
        DEL = getattr(self.Model, "__delattr__")
        
        def __set__(instance, name, value):
            """Tracks changes on attribute during assignment."""
            if self.tracking:
                log.info("Tracking changes on: %s" % self.Model )
                previous = getattr(instance, name, None)
                try:
                    SET(instance, name, value)
                    if previous is not getattr(instance, name):
                        with self.lock:
                            self.changedSet.add(name)
                            self.delSet.remove(name)  
                except error: 
                    raise errror      
            else:
                log.info("Stopped tracking changes on: %s" % self.Model)
                SET(instance, name, value)
                
        def __delete__(instance, name):
            """Tracks changes when deletion occurs"""
            if self.tracking:
                try:
                    log.info("Tracking ON...")
                    DEL(instance, name)
                    if not hasattr(instance, name):
                        with self.lock:
                            self.changedSet.remove(name)
                            self.delSet.add(name)         
                except error:
                    raise error
            else:
                log.info("Tracking OFF...")
                DEL(instance, name)
                   
        update(__set__, SET), update(__delete__, DEL)
        log.info("Wrapping __setattr__, and __delattr__")
        setattr(object,"__setattr__", __set__)
        setattr(object,"__delattr__", __delete__)


class ListView(View):
    """A view that tracks lists"""
    pass

class SetView(View):
    """A view that tracks sets"""
    pass
    
class HashView(View):
    """A view that tracks mappings"""
    pass

class NormalView(View):
    """Tracks normal objects"""
    pass
    
"""
Views:
A factory for creating view

"""
class Views(object):

    @classmethod
    def forModel(Model):
        """Install a view for this Model"""
        pass
        
    @classmethod
    def getView(Model):
        """Returns the view for this Model"""
        pass
                       
        
        

