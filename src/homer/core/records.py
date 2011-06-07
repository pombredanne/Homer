#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Provides Record, Descriptor and Type
"""
import time
from homer.core.options import options
from homer.core.events import Observable, Observer, Event
from homer.core.types import Descriptor, READONLY


__all__ = ["Record", "key", "Key"]

"""# Default Module Wide Objects """
log = options.logger("homer::core::records")
RecordEvents = ("SET", "ADD", "DEL", )



"""
@key:
This decorator creates a 'Key' for your Record automatically.
You can get the 'Key' of a Record instance by using Record.key; If you pass an
object that is not a subclass of Record a TypeError Exception is raised.

@key("link", namespace = "com.twitter.base")
class Profile(Record):
    link = URL()
    name = String()
    bio =  String(length = 200)
  
"""
def key(name, namespace = None):
    """The @key decorator""" 
    def inner(cls):
        if issubclass(cls, Record):
            log.info("Adding key for Record: %s " % object)
            assert hasattr(cls, name), "Record: %s must have an attribute: %s" % (cls, name)
            key = Key(namespace = namespace, kind = cls.__name__, key = name)
            cls.__kind__ = Descriptor(default = key, mode = READONLY)
            return cls
        else:
            raise TypeError("You must pass in a subclass of Record not:\
            %s" % cls)
    return inner
    
"""
Key:
Represents the Key of an entity that should be stored in KV datastore;
Should a Key Object store the value
"""
class Key(object):
    """A unique identifier for Records"""
    namespace, kind, key, id = None, None, None, None
    
    def __init__(self, **arguments ):
        """Creates the Key from keyword arguments"""
        log.info("Creating a new Key with arguments %s" % str(arguments))
        for i in ["namespace", "kind", "key", "id", ]:
            assert isinstance(i, str), "Arguments must be Strings"
            setattr(self, i, arguments.get(i, None))
        self.timestamp = int(time.time())
    
    @property
    def complete(self):
        """Checks if all the parts of this key are complete"""
        for i in ["namespace", "kind", "key", "id"]:
            part = getattr(self, i)
            if part is None:
                return False
        return True
        
    def clone(self, **arguments):
        """
        Create a clone of this key while filling up missing parts with
        values from @arguments
        """
        clone = Key()
        for i in ["namespace", "kind", "key", "id", ]:
            value = getattr(self, i)
            if value is None:
                setattr(clone, i, arguments.get( i, None))
            else:
                setattr(clone, i, value)
        return clone  
                
    def __str__(self):
        '''Creates and returns a TagURI based key string '''
        format = "key: {self.namespace}, {self.kind}: {self.key}[{self.id}]"
        return format.format(self = self)
        

"""
Record:
Unit of Persistence; Any class you want to be persistable should extend this 
class
Events:
1."SET" =  source, "SET", name, old, new ::: fired when an attribute modification occurs
2."ADD" =  source, "ADD", name, value ::: fired when an new attribute is added to a record
3."DEL" =  source, "DEL", name ::: fired when an attribute is deleted
"""
class Record(object):
    """Unit of Persistence..."""
  
    def __init__(self, **arguments):
        """Fills the attributes in this record with **arguments"""
        log.info("Creating Record with @id: %s" % id(self))
        for name,value in arguments.items():
            setattr(self, name, value)
        log.info("Created Record with @id: %s" % id(self))
    
    @property
    def key(self):
        """Returns the Key of this Record else return None"""
        if hasattr(self, "__kind__"):
            """Check if the key attribute of this instance is set"""
            name = self.__kind__.key
            if hasattr(self,name):
                val = getattr(self,name)
                if val is not None:
                    return self.__kind__.clone(id = val)
                else:
                    return None
            else:
                return None
        else:
            return None
    
    @property
    def kind(self):
        """Returns the Parent Key of this object.."""
        return self.__kind__
                
    def __setattr__(self, name, value):
        """Do comparisons and propagate() an ADD or SET Event to observers"""
        pass
    
    def __delattr__(self, name ):
        """Try to DELETE attribute if successful fire the DEL Event """
        pass
        
"""
EventSource:  
Basically this is the point of coupling with the extension and options module.
EventSource always makes sure that you get upto date watchers from the system.
"""
class EventSource(object):
    default = None
    
    @classmethod
    def Observable(cls):
        """Returns an observer that has observers from the extension module"""
        if options.debug:
            'in debug mode an observer with only the DiffObserver'
            log.info("Debug Mode: loading only default Observers")
            if cls.default is not None:
                return cls.default
            else:
                'Create the default if it does not exist'
                from homer.core.builtins import RecordObserver
                obs = Observable(*RecordEvents)
                obs.add(RecordObserver, *RecordEvents )
                cls.default = obs
                return cls.default   
        else:
            'Return all the observers that the extension module provides'
            return None
                    



