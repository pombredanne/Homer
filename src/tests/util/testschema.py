#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the Schema class...
"""
from datetime import date, time, datetime
from unittest import TestCase
from homer.util import Schema

class TestSchema(TestCase):

    def testSimple(self):
        """Show that simple types are properly discovered"""
        Datetime, Date, Time = datetime.now(), datetime.now().date(), datetime.now().time()
        tests = ["Hello", Datetime, Date, Time, 1, 1.0, False]
        for ob in tests:
            self.assertTrue(Schema.isSimple(ob))
   
    def testSequence(self):
        """Shows that sequence types are properly discovered"""
        traps = ["Hello", {"Hello" : "World" }, set([1, 2, 3,]) ]
        for ob in traps:
            self.assertFalse(Schema.isSequence(ob))
        tests = [[1,2,3,], (1,2,3,), range(1, 20), xrange(1, 30)]
        for ob in tests:
            self.assertTrue(Schema.isSequence(ob))
    
    def testMapping(self):
        """Shows that Map like objects are properly discovered"""
        tests = [ {"Hello": "World"}, dict() ]
        for ob in tests:
            self.assertTrue(Schema.isMapping(ob))
            
    def testSet(self):
        """Shows that sets work well"""
        tests = [ set("""Shows that sets work well""".split(" "))]
        for ob in tests:
            self.assertTrue(Schema.isSet(ob))
            
    def testComplex(self):
        """Shows that complex objects work"""
        class Person(object):
            name = "hello people"
            
        person = Person()
        self.assertTrue(Schema.isComplex(person))
