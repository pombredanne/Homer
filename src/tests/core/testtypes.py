#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the records module...
"""
from unittest import TestCase,expectedFailure
from homer.core.types import Property, Type, READWRITE, READONLY, BadValueError
from datetime import datetime, date

"""#.. Tests for homer.core.record.Type"""
class TestType(TestCase):
    """Sanity Checks for Type"""
    def setUp(self):
        """Creates a Type"""
        class Bug(object):
            name = Type(type = str )
            filed = Type(type = date ) 
        self.bug = Bug()
            
    def testTypeSanity(self):
        """Makes sure that Type doe type checking"""
        self.assertRaises(Exception, lambda: 
            setattr(self.bug, "filed", "Today"))
        now = datetime.now().date()
        self.bug.filed = now
   
    def testTypeCoercion(self):
        """Does Type do coercion? """
        self.bug.name = 23
        self.assertEqual(self.bug.name, "23")
            

"""#.. Tests for homer.core.record.Property"""
class TestProperty(TestCase):
    def setUp(self):
        """Creates a new Bug class everytime"""
        class Bug(object):
            """No bugs..."""
            name = Property()
            email = Property("iroiso@live.com", mode = READONLY)
            girlfriend = Property("gwen", choices = ["amy","stacy","gwen"],required = True)   
        self.bug = Bug()
         
    def testReadWriteProperty(self):
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
        """Asserts that a required Property cannot be set to an empty value"""
        with self.assertRaises(BadValueError):
            self.bug.girlfriend = None
       
    def testReadOnlyProperty(self):
        """Makes sure that ReadOnlies are immutable """
        with self.assertRaises(ValueError):
            self.readOnly = Property(mode = READONLY)
        with self.assertRaises(AttributeError):
            print("You cannot write to a read only Property")
            setattr(self.bug,"email",100)
        with self.assertRaises(AttributeError):
            print("You cannot delete a read only Property")
            delattr(self.bug,"email")
    
       
    
