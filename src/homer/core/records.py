#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Contains Record, Key and @key
"""
import copy
import datetime
from threading import Lock
from functools import update_wrapper as update
from contextlib import contextmanager as context

from homer.util import Validator
from homer.core.options import options
from homer.core.types import Property


__all__ = ["Record", "key", ]

"""Module Variables """
log = options.logger("homer.core.records")

"""Exceptions """
class BadKeyError(Exception):
    pass

"""
@key:
This decorator automatically configures your record and creates
a key entry for it within the SDK. If you pass in an object
that is not a Record a BadKeyError is raised.

@key("link", namespace = "June")
class Profile(Record):
    link = URL("http://twitter.com")
    
  
"""
def key(name, namespace = "June"):
    """The @key decorator""" 
    def inner(cls):
        if issubclass(cls, Record):
            if hasattr(cls, name):
                KindMap.putKey(cls, name, namespace)
                return cls
            else:
                raise BadKeyError("There is no attribute with this name in %s" % cls)
        else:
            raise TypeError("You must pass in a subclass of  Record not: %s" % cls)
    return inner

"""
@cache
@key("link")
class Profile(Record):
    link = URL("http://twitter.com")
"""
def cache(timeout = -1):
    """Put this record in Redis"""
    pass
    
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
A GUID for Record objects. A Key contains all the information 
required to retreive a Record from Cassandra or Redis
Key is serialized to this String format:
"key: {namespace}, {kind}, {key}"
"""
class Key(object):
    """A GUID for Records"""
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
RecordSet:
Tracks all Records that exists; active(instances) or dormant
(just defined classes). 
"""
class RecordSet(object):
    """An object that keeps track of all the subclasses of Record that exist"""
    @classmethod
    def active(cls):
        """Return all Record instances"""
        pass
        
    @classmethod   
    def all(cls):
        """Returns all defined Record classes"""
        pass
        
"""
__configure__:
Called to create a new Record; It configures all the Properties 
in the Record and caches them so that subsequent discovery will 
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
Record: Unit of Persistence
Any class you want to store should extend this class. 
Record keeps track of changes which you make to it.

@key("name")
class Profile(Record):
    name = String("John Bull")
    
"""
class Record(object):
    __metaclass__ = __configure__
    
    def __init__(self, **kwds):
        """init kwds through descs, create views, add to RecordSet.active()"""
        for name, prop in self.fields().items():
            if name in kwds:
                prop.__set__(self, kwds[name])
                
    def key(self):
        """If this Record has a Key return it"""
        name, namespace = KindMap.getKey(self)
        kind = self.__class__.__name__
        value = getattr(self, name, None)
        if value is not None:
            return Key(namespace, kind, value)
        return None
    
    def rollback(self):
        """Rollback your model to the last saved state"""
        pass
        
    def __call__(self, **kwds):
        """This is equivalent to the constructor, it is commonly used to reload records"""
        pass
        
    def __setattr__(self, name, value):
        """Make sure that only defined properties are set on this object"""
        if name not in self.fields():
            raise AttributeError("Attribute %s does not exist in %s" % (name, self))
        super(Record, self).__setattr__(name, value)
        
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
RecordView:
A View that specializes in tracking Records; The differences between NormalView 
and RecordView are:

1. RecordView tracks only instances of Record.
2. RecordView loops through Properties in a Record and tracks them too. unless if
   the Property stores a Record of course.
3. RecordView yields all the Views for the properties in the Record it tracks 
   through the RecordView.view() method.
   
"""   
class RecordView(View):
    """Tracks changes to Record objects"""
    
    def __init__(self, record):
        """inits lock object and modification sets"""
        if isinstance(record, Record):
            raise TypeError("Expected: a instance of Record, Got: %s" % record)
        self.lock = Lock()
        self.record = record
        self.changedSet, self.delSet = set(), set()
        self.track()
    
    def view(self):
        """Returns a dict containing attributes of this self.record and their views"""
        pass
        
    def deleted(self):
        '''Returns a set of all the attributes that have been deleted'''
        return copy.deepcopy(self.delSet)
        
    def modified(self):
        '''Returns a set of the attributes that have changed'''
        return copy.deepcopy(self.changedSet)
    
    def flush(self):
        """Empty all tracking information and start afresh;
        
           This will useful if a record is reloaded from the 
           datastore or when it is saved. basically it resets
           self.originals
        """
        pass
        
    def track(self):
        '''Track changes on self.record and its attributes'''
        log.info("Tracking Record: %s for changes" % object)
        SET = getattr(self.record, "__setattr__")
        DEL = getattr(self.record, "__delattr__")
        
        def __set__(instance, name, value):
            """Tracks changes on attribute during assignment."""
            if self.tracking:
                log.info("Tracking changes on: %s" % self.record )
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
                log.info("Stopped tracking changes on: %s" % self.record)
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
    def forRecord(record):
        """Install a view for this Record"""
        pass
        
    @classmethod
    def getView(record):
        """Returns the view for this Record"""
        pass
                       
        
        

