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


__all__ = ["Record", "Type", "key", "Key"]

"""# Default Module Wide Objects """
log = options.logger("homer::core::records")
RecordEvents = ("SET", "ADD", "DEL", )
KeyEvents = ("KADD", "KSET", "KDEL")
READWRITE, READONLY = 1, 2


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
        self.timestamp = time.time()
    
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
        
"""Exceptions"""
class BadValueError(Exception):
    """An exception that signifies that a validation error has occurred"""
    pass
    
"""
Record:
Unit of Persistence; Any class you want to be persistable should extend this 
class
Events:
1."SET" =  source, "SET", name, old, new ;
2."ADD" =  source, "ADD", name, value
3."DEL" =  source, "DEL", name

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
        log.debug("Setting attribute: %s  with value: %s" % (name, value))
        old = getattr(self, name, None)
        object.__setattr__(self, name, value)
        if old is None:
            EventSource.Observable().propagate(Event(self, "ADD", name = name,
                value = value))
            if getattr(self,"kind", None):
                if name == self.kind.key:
                    EventSource.Observable().propagate(Event(self, "KADD", 
                        name = name,  value = value))
        elif old != value:
            """I only propagate a set when there is a difference in values"""
            EventSource.Observable().propagate(Event(self, "SET", name = name, 
                old = old, new = value))
            if getattr(self,"kind", None):
                if name == self.kind.key:
                    EventSource.Observable().propagate(Event(self, "KSET", name=
                        name, old = old, new = value))
        log.debug("successful set attribute: %s  with value: %s" % 
            (name, value))
    
    def __delattr__(self, name ):
        """Try to DELETE attribute if successful fire the DEL Event """
        log.debug("Attempting to DEL attribute: %s" % name)
        object.__delattr__(self, name)
        EventSource.Observable().propagate(Event(self, "DEL", name = name))
        if getattr(self, "kind", None):
            if name == self.kind.key:
                EventSource.Observable().propagate(Event(self, "KDEL", 
                    name = name))
        log.debug("Successfully DEL attribute: %s" % name)
 
"""
EventSource:  
Basically this is the point of coupling with the extension and options module.
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
                from homer.core.builtins import DiffObserver
                evs = RecordEvents + KeyEvents
                obs = Observable(*evs)
                obs.add(DiffObserver, *evs )
                cls.default = obs
                return cls.default
            
        else:
            'Return all the observers that the extension module provides'
            log.info("About to load extension from the plugins module")
            evs = RecordEvents + KeyEvents
            obs = Observable(*evs)
            for obs, evts in Plugins.all():
                try:
                    log.info("Adding Observer: %s with Events: %s" % (obs,evts))
                    observable.add(obs, evts)
                except error:
                    log.info("Exception occured: %s when adding plugin: %s"
                        % (error, obs))
            return observable 
                    

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

