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
from homer.core.records import Record, Descriptor
from homer.core.records import READWRITE, READONLY, BadValueError
from homer.core.events import Observer

"""#.. Tests for homer.core.record.Descriptor"""
class TestDescriptor(TestCase):
    def setUp(self):
        """Creates a new Bug class everytime"""
        class Bug(object):
            """No bugs..."""
            name = Descriptor()
            email = Descriptor("iroiso@live.com", mode = READONLY)
            girlfriend = Descriptor("gwen", choices = ["amy","stacy","gwen"],required = True)   
        self.bug = Bug()
         
    def testReadWriteDescriptor(self):
        """Makes sure that ReadWrites can be read,written and deleted"""
        setattr(self.bug,"name","Emeka")
        self.assertEqual(self.bug.name , "Emeka")
        delattr(self.bug, "name")
        with self.assertRaises(AttributeError):
            print self.bug.name
    
    def testSetDeleteSetGetWorks(self):
        """Tests this sequence, Delete,Set,Get does it work; Yup I know its crap"""
        setattr(self.bug,"name","First name")
        delattr(self.bug,"name")
        self.assertRaises(AttributeError, lambda: getattr(self.bug,"name"))
        setattr(self.bug,"name","NameAgain")
        self.assertEquals(self.bug.name,"NameAgain")
        delattr(self.bug,"name")
        self.assertRaises(AttributeError, lambda: getattr(self.bug, "name"))
        setattr(self.bug,"name","AnotherNameAgain")
        self.assertEquals(self.bug.name,"AnotherNameAgain")
    
    def testDelete(self):
        """Tests if the del keyword works on READWRITE attributes"""
        self.bug.name = "Emeka"
        del self.bug.name
        self.assertRaises(Exception,lambda:getattr(self.bug,"name"))
            
    def testChoices(self):
        """Tries to set a value that is not a amongst the properties choices"""
        with self.assertRaises(BadValueError):
            self.bug.girlfriend = "steph"
            
    def testRequired(self):
        """Asserts that a required Descriptor cannot be set to an empty value"""
        with self.assertRaises(BadValueError):
            self.bug.girlfriend = None
       
    def testReadOnlyDescriptor(self):
        """Makes sure that ReadOnlies are immutable """
        with self.assertRaises(ValueError):
            self.readOnly = Descriptor(mode = READONLY)
        with self.assertRaises(AttributeError):
            print("You cannot write to a read only Descriptor")
            setattr(self.bug,"email",100)
        with self.assertRaises(AttributeError):
            print("You cannot delete a read only Descriptor")
            delattr(self.bug,"email")
    
    
    
"""#.. Tests for homer.core.record.Record """  
class CountObserver(Observer):
    """A simple observer that print events"""
    count = 0
    def clear(self):
        """Clear the count variable"""
        self.count = 0
        
    def observe(self, event):
        """Increments the count variable and prints the event"""
        self.count += 1

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
        observer = CountObserver()
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
        
        
        
        
        
    
