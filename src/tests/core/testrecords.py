#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the records module...
"""
from unittest import TestCase
from homer.core.records import Record
from homer.core.events import Observer

"""#.. Tests for homer.core.record.Record """  
class PrintObserver(Observer):
    """A simple observer that print events"""
    count = 0
    def clear(self):
        """Clear the count variable"""
        self.count = 0
        
    def observe(self, event):
        """Increments the count variable and prints the event"""
        self.count += 1
        print str(event)

class OrderObserver(Observer):
    """ An observer that records the order in which events have occurred"""
    poll = []
    def observe(self, event):
        """This just simply polls the event"""
        self.poll.append(event.id)
        
    def clear(self):
        """Clears the poll variable"""
        self.poll = []
  
class TestRecord(TestCase):
    """Unittests for Record; """
    
    def testRecordAcceptsKeywords(self):
        """Tests If accepts keyword arguments and sets them"""
        diction = { "name": "iroiso", "position" : "CEO", "nickname" : "I.I"}
        person = Record(**diction)
        for name in diction:
            self.assertTrue(hasattr(person, name))
            
    def testRecordFiresEvents(self):
        """Tests if a Record will fire events on SET and DELETE"""
        observer = PrintObserver()
        person = Record()
        diction = { "name": "iroiso", "position" : "CEO", "nickname" : "I.I"}
        person.observable.add(observer, "ADD", "SET", "DEL")
        for name, value in diction.items():
            setattr(person, name, value)
        assert observer.count > 0, "Observer should have recorded some events"
        
    def testRecordFiresTheCorrectEvents(self):
        """Tests if a Record will the correct Events; Hmmn.. Tricky.."""
        observer = OrderObserver()
        diction = { "name": "iroiso", "position" : "CEO", "nickname" : "I.I"}
        person = Record()
        person.observable.add(observer, "ADD","SET", "DEL")
        for name, value in diction.items():
            setattr(person, name, value)
        self.assertEqual(observer.poll, ["ADD", "ADD", "ADD"])
        observer.clear()
        new = { "name": "house", "position" : "Head of Diagnostics", "nickname"
            :"Gregg" }
        for name,value in new.items():
            setattr(person, name, value)
        self.assertEqual(observer.poll, ["SET", "SET", "SET"])
        observer.clear()
        for name in diction:
            delattr(person, name)
        self.assertEqual(observer.poll, ["DEL", "DEL", "DEL"])
        
        
        
        
        
    
