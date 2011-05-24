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
log = options.logger("homer::core::events")

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
        log.info("Creating an Event:: source: %s id: %s" % (source, id))
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
      
    def observe(self, event):
        """Implement this method to react to events """
        raise NotImplementedError("Stub::Write Implementation")

"""
Observable:
A Thread Safe GOF Observable object. This object will be useful for objects that
want to provide event subscription and notification to observers.

#.. To create an Observable for Events: "GET", "SET", "DELETE"
observable = Observable("GET", "SET", "DELETE")

#.. To add an observer that reacts to "GET" and "SET" Events
observable.add(observer, "GET", "SET")

#.. To propagate Events to Registered Observers
observable.propagate(Event(source, "GET", **arguments ))

"""
class Observable(object):
    """Extend this class if you want your class to notify listeners """
    def __init__(self, *events ):
        self.map = { name : set() for name in events }
        self.lock = RLock()
        self._poll = []
    
    def propagate(self, event):
        """Notify all registered Observers of this event"""
        assert isinstance(event, Event), "You have to call propagate with an\
            instance of Event"
        if event.id not in self.map.keys():
            raise BadEventError("This Observable cannot deal with this event")
        log.info("Propagating Event: %s" % event)
        self._poll.append(event)
        for ob in self.map[event.id]:
            ob.observe(event)
        
    def add(self, observer, *events ):
        """Add an Observer to this Observable"""
        assert isinstance(observer, Observer), "Parameter %s is invalid add a sub\
            class of Observer " % observer
        assert len(events) > 0, "You must pass in valid events"
        for i in events:
            assert i in self.map.keys(), "Events: %s are invalid" % str(events)
        with self.lock:
            log.info("Adding Observer: %s" % observer)
            for name in events:
                set = self.map[name]
                set.add(observer)
    
    def remove(self, observer):
        """Remove an Observer from this Observable"""
        log.info("Removing Observer: %s" % observer)
        with self.lock:
            for set in self.map.values():
                if observer in set:
                    set.remove(observer)
    
    def contains(self, observer):
        """Checks if this Observable contains this observer"""
        log.info("Checking if Observer: %s exists" % observer)
        with self.lock:
            for set in self.map.values():
                if observer in set:
                    return True
            return False
        
    def clear(self):
        """Remove all Registered Observers"""
        with self.lock:
            log.info("Removing all registered observers")
            for set in self.map.values():
                set.clear()
    
    @property
    def poll(self):
        """An ordered list of events this Observable has propapagated"""
        return self._poll
              
    def empty(self):
        """Is this Observable empty ? """
        for set in self.map.values():
            if len(set) == 0:
                continue
            else:
                return False
        return True

"""#.. Exceptions """
class BadObserverError(Exception):
    """ An Exception that gets thrown when you add a wrong observer to an Observable """
    pass

class BadEventError(Exception):
    """An Exception that gets thrown when you try to propagate an Event that Observable
       does not know
    """   
    pass     
