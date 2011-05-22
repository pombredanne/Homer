#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Module that provide Event Notification for the Core
"""
from threading import RLock
from homer.core.options import options

__all__ = ["Event", "Observer", "Observable", ]

"""# Default Module Wide Objects """
log = options.logger()

"""
Event:
Base class of all events; You can add custom arguments that will made part of
the instance, this will allow devs to customize Event without extending it::
Duck Typing
#..e.g..
event = Event(source, id, old = "name", new = "value")
"""
class Event(object):
    """Base class of all Events"""
    def __init__(self, source, id, **arguments):
        """Creates an Event Object from these"""
        log.info("Creating an Event:: source: %s id: %s" % source, id )
        self.source = source
        self.id = id
        self.addendum = arguments
        for name,value in arguments.items():
            setattr(self, name, value)

    def __str__(self):
        format = "Event:: source: {self.source}, id: {self.id} \n".format(self = self)
        for name, value in self.addendum.items():
            format += "{name}: {value}, ".format(name = name, value = value)
        return format

"""
Observer:
An observer is an object that can listen for events; you attach Observers to 
Observables.
"""                   
class Observer(object):
    """ An object that listens for Events"""
    def __init__(self, id ):
        """@id is the event that this Observer reacts to."""
        self.id = id
        
    def observe(self, event):
        """Implement this method to react to events """
        raise NotImplementedError("Stub: Write Implementation")

"""
Observable:
A Thread Safe GOF Observable object. This object will be useful for objects that
want to provide event subscription and notification to observers.

#.. To create an Observable which propagates events with ids "GET", "SET", "DELETE"
observable = Observable("GET", "SET", "DELETE")

#.. To add listeners
observer = createObserver()
observable.add(observer)

#.. To propagate Events
observable.propagate(Event(source, "GET", **arguments ))

"""
class Observable(object):
    """Extend this class if you want your class to notify listeners """
    def __init__(self, *events ):
        self.events = set(events)
        self.observers = set()
        self.lock = RLock()
    
    def propagate(self, event):
        """Notify all registered Observers of this event"""
        assert isinstance(event, Event), "You have to call propagate with an\
            instance of Event"
        if event.id not in self.events:
            raise BadEventError()
        log.info("Propagating Event: %s" % event)
        for ob in self.observers:
            ob.observe(event)
        
    def add(self, observer ):
        """Add an Observer to this Observable""" # Make this thread safe.
        assert issubclass(observer, Observer), "You can only add instances of Observer"
        if observer.id not in self.events:
            raise BadObserverError()
        with self.lock:
            log.info("Adding Observer: %s" % observer)
            self.observers.add(observer)
    
    def remove(self, observer):
        """Remove an Observer from this Observable"""
        log.info("Removing Observer: %s" % observer)
        with self.lock:
            self.observers.remove(observer)
    
    def clear(self):
        """Remove all registered Observers"""
        with self.lock:
            log.info("Removing all registered observers")
            self.observers.clear()



"""#.. Exceptions """
class BadObserverError(Exception):
    """ An Exception that gets thrown when you add a wrong observer to an Observable """
    pass


class BadEventError(Exception):
    """An Exception that gets thrown when you try to propagate an Event that Observable
       does not know
    """   
    pass     
