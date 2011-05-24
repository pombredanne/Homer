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
READWRITE, READONLY = 1, 2

"""Exceptions"""
class BadValueError(Exception):
    """An exception that signifies that a validation error has occurred"""
    pass
    
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
class Descriptor(object):
    """A Generic Data Descriptor which can be READONLY or READWRITE"""
    
    def __init__(self, default = None, mode = READWRITE, **keywords):
        """Initializes the Descriptor"""
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
        self.default = None
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
        if self.name is None : self.name = Descriptor.search(instance,self)
        if self.name is not None:
            instance.__dict__[self.name] = value
            self.value = value
            self.deleted = False
        else:
            raise AttributeError("Cannot find this property:%s in \
                this the given object: %s " % (self,instance))

    def __get__(self, instance, owner):
        """Read the value of this property"""
        if self.name is None : self.name = Descriptor.search(instance,self)
        if self.name is not None:
            try:
                found = instance.__dict__[self.name] 
                return found  
            except (AttributeError,KeyError) as error:
                # Notifications will occur even default values are returned.
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
        if self.name is None : self.name = Descriptor.search(instance,self)
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
   
"""
Type:
A Descriptor that does type coercion, checking and validation.
#..

class Story(Record):
    source = Type(Blog)
    
"""
class Type(Descriptor):
    """A Descriptor that does coercion and validation"""
    pass
    




    

