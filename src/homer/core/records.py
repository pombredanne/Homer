#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Provides Record, Descriptor and Type
"""
from homer.core.options import options
from homer.core.events import Observable, Observer, Event

__all__ = ["Record", "Type", ]

"""# Default Module Wide Objects """
log = options.logger("homer::core::records")
RecordEvents = ("SET", "ADD", "DEL", )

"""
Record:
Unit of Persistence; Any class you want to be persistable should extend this 
class
Events:
1."SET" =  source, "SET", name, old, new
2."ADD" =  source, "ADD", name, value
3."DEL" =  source, "DEL", name

"""
class Record(object):
    """Unit of Persistence..."""
    observable = Observable(*RecordEvents)
    def __init__(self, **arguments):
        """Fills the attributes in this record with **arguments"""
        log.info("Creating Record with @id: %s" % id(self))
        for name,value in arguments.items():
            setattr(self, name, value)
        log.info("Created Record with @id: %s" % id(self))

    def __setattr__(self, name, value):
        """Do comparisons and propagate() an ADD or SET Event to observers"""
        log.debug("Attempting to SET attribute: %s  with value: %s" % 
            (name, value))
        old = getattr(self, name, None)
        object.__setattr__(self, name, value)
        if old is None:
            self.observable.propagate(Event(self, "ADD", name = name,
                value = value))
        elif old != value:
            """I only propagate a set when there is a difference in values"""
            self.observable.propagate(Event(self, "SET", name = name, old = old,
                new = value))
        log.debug("Successfully SET attribute: %s  with value: %s" % 
            (name, value))
    
    def __delattr__(self, name ):
        """Try to DELETE attribute if successful fire the DEL Event """
        log.debug("Attempting to DEL attribute: %s" % name)
        object.__delattr__(self, name)
        self.observable.propagate(Event(self, "DEL", name = name))
        log.debug("Successfully DEL attribute: %s" % name)
    
"""
Property:
Base class for all data descriptors; 
"""
class Property(object):
    """A Generic Descriptor which can be READONLY or READWRITE"""
    pass
    

"""
Type:
A Descriptor that does type coercion, checking and validation.
#..

class Story(Record):
    source = Type(Blog)
    
"""
class Type(Property):
    """A Descriptor that does coercion and validation"""
    pass
    




    

