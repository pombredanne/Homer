#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Provides Record, Descriptor and Type
"""
import datetime
from threading import Lock
from homer.util import Validator


__all__ = ["Record", "key", ]

"""Exceptions """
class BadKeyError(Exception):
    pass

"""
@key:
This decorator creates a 'Key' for your Record automatically. 
You can get the 'Key' of a Record instance by using Record.key; If you pass an
object that is not a subclass of Record a TypeError Exception is raised.

@key("link", namespace = "June:Homer")
class Profile(Record):
    link = URL()
    name = String()
    bio =  String(length = 200)
  
"""
def key(name, namespace = "June"):
    """The @key decorator""" 
    def inner(cls):
        if issubclass(cls, Record):
            if hasattr(cls, name):
                KindMap.putKey(cls, name, namespace)
            else:
                raise BadKeyError("There is no attribute with this name in %s" % cls)
            return cls
        else:
            raise TypeError("You must pass in a subclass of Record not: %s" % cls)
    return inner


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
            assert isinstance(kind, type), "Kind has to be a class; Got: %s instead" % kind
            name = kind.__name__
            cls.keyMap[name] = key, namespace
            cls.typeMap[name] = kind
    
    @classmethod
    def getKey(cls, kind):
        """Returns a tuple (key, namespace) for this kind or None if non-existent"""
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
A GUID for Record objects. A Key contains all the information required to retreive
a Record from the datastore; 
"""
class Key(object):
    """A GUID for Records"""
    namespace, kind, key = None, None, None
    
    def __init__(self, namespace, kind = None, key = None):
        """Creates a key with keywords"""
        if kind is None:
            """Tries to create a key from a serialized representation"""
            try:
                key, repr = namespace.split(":")
                assert key == "key", "Key representation should start with 'key:'"
                namespace, kind, key = repr.split(",")
            except:
                raise BadKeyError("Expected String of format 'key: namespace, kind, key',\
                Got: %s" % namespace)
        validate = Validator.ValidateString
        self.namespace, self.kind, self.key = validate(namespace), validate(kind), validate(key)
          
    def complete(self):
        """Checks if this key has all its parts"""
        if self.namespace and self.kind and self.key:
            return True
        return False
    
    def toTagURI(self):
        """
        Returns a tag: URI for this entity for use in XML output
        
        Foreign keys for entities may be represented in XML output as tag URIs.
        RFC 4151 describes the tag URI scheme. From http://taguri.org/.
        Key tags take this format: "tag:<namespace>, date:<kind>[<key>]" e.g.
        
            tag:June,2006-08-29:Profile[Jack]
            
        Raises a BadKeyError if this key is incomplete.
        """ 
        date = datetime.date.today().isoformat()
        return u"tag:{self.namespace},{date}:{self.kind}[self.key]".format(self = self, date = date)
        
       
    def __unicode__(self):
        """Unicode representation of a key"""
        format = u"key: {self.namespace}, {self.kind}, {self.key}"
        return format.format(self = self)
    
    def __str__(self):
        """String representation of a key"""
        return unicode(self)
            
"""
Record(unit of persistence):
Any class you want to store should extend this class. Record keeps track of 
changes which you make to it.

@key("name")
class Profile(Record):
    name = String("John Bull")
    
"""
class Record(object):
    """Unit of Persistence..."""
    
    @property
    def key(self):
        """Returns a Key (If it is complete) for this Record else return None"""
        name, namespace = KindMap.getKey(self)
        kind = self.__class__.__name__
        if getattr(self, name, None) is not None:
            return Key(namespace, kind, getattr(self, name))
        return None
   
   
        




