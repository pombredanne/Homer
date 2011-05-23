#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the events module...
"""
from unittest import TestCase
from homer.core.events import Event, Observer, Observable
from homer.core.events import BadObserverError, BadEventError


"""#.. Event Tests """
class TestEvent(TestCase):
    """Tests for the Event type"""
    
    def testBasic(self):
        """Simple Example of Using Events"""
        event = Event(self, "BasicEvent")
        self.assertIsNotNone(event)
    
    def testAddendum(self):
        """Checks if added keywords become attributes"""
        keywords = {"old": 1 , "new" : 2}
        event = Event(self, "TestAddendum", **keywords)
        for name in keywords:
            self.assertTrue(hasattr(event, name))


"""#.. Observable Tests """  
class PrintObserver(Observer):
    """A simple observer that print events"""
    count = 0
    def observe(self, event):
        self.count += 1
        print "Event occured: " + event.id
  
               
class TestObservable(TestCase):
    """
    Tests for the homer.core.events.Observable; Doesn't contain ThreadSafety Tests
    """       
    def testAdd(self):
        """Tests add(observer) normal, and bad case"""
        observable = Observable("SET", "GET", "DELETE")
        observer = PrintObserver()
        observable.add(observer, "SET")
        self.assertRaises(AssertionError, lambda : observable.add(observer))
        self.assertTrue(observable.contains(observer))
        with self.assertRaises(AssertionError):
            observable.add(object(), "GET")    
        
    def testRemove(self):
        """Tests remove(observer) normal, and bad case"""
        observable = Observable("SET", "GET", "DELETE")
        observer = PrintObserver()
        observable.add(observer, "SET", "GET")
        self.assertTrue(observable.contains(observer))      
        observable.remove(observer)
        self.assertFalse(observable.contains(observer))
        
    def testClear(self):
        """Tests clear() """
        observable = Observable("SET", "GET", "DELETE")
        self.assertTrue(observable.empty())
        observer = PrintObserver()
        observable.add(observer, "SET", "GET")
        self.assertTrue(observable.contains(observer))
        self.assertFalse(observable.empty())
        observable.clear()
        self.assertTrue(observable.empty())
          
    def testPropagate(self):
        """Tests that propagate(Event) normal, and bad case"""
        observable = Observable("SET", "GET", "DELETE")
        self.assertTrue(observable.empty())
        observer = PrintObserver()
        observable.add(observer, "SET", "GET")
        self.assertFalse(observable.empty())
        observable.propagate(Event(self, "SET", value = 12))
        observable.propagate(Event(self, "GET", value = 12))
        self.assertEqual(observer.count, 2)
        self.assertRaises(AssertionError, lambda: observable.propagate(object))
        self.assertRaises(BadEventError, lambda: 
            observable.propagate(Event(self, "OPEN")))
        
    
    
