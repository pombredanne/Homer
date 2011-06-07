#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Provides implementation for Descriptors and Type.
"""

READWRITE, READONLY = 1, 2

"""Exceptions"""
class BadValueError(Exception):
    """An exception that signifies that a validation error has occurred"""
    pass
    
    
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
A Descriptor that does type coercion, checking and validation. This is base
class for all the common descriptors. If you intend to write a new descriptor
start from here unless you know what you're doing...
#..

class Story(Record):
    source = Type(Blog)
    
#..
The snippet above will make sure that you can only set Blog objects on the on
source. If you try to set a different type of object; Type will attempt to
convert this object to a blog by coercion i.e calling Blog(object). if this
fails this raises an exception.

Keywords:
type = The type that will be used during type checking and coercion
omit = Tells the SDK that you do not want to the property to be persisted or marshalled.
"""
class Type(Descriptor):
    """A Descriptor that does coercion and validation"""
    type = None
    def __init__(self, default = None, mode = READWRITE, type = None, **keywords):
        """Generally like Descriptor.__init__ 'cept it accepts type and omit"""
        Descriptor.__init__(self, default, mode, **keywords)
        if self.type is None:
            self.type = type
        self.omit = keywords.get("omit", False)
        
    def validate(self, value):
        """overrides Descriptor.validate() to add type checking and coercion"""
        assert value.__class__ is not self.__class__,"You cannot do Type(Type)"
        value = super(Type,self).validate(value)
        if self.type is None:
            return value
        if value is not None and not isinstance(value,self.type):
            value = self.type(value)
        return value
