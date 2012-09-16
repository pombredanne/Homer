#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the collections module...
"""
from unittest import TestCase,expectedFailure,skip
from homer import String, URL
from homer import Map

class TestMap(TestCase):
    """Tests for the Map() collection"""
    def setUp(self):
        '''Creates a test object'''
        self.bookmarks = Map(String, URL)
        
    def testMapSanity(self):
        '''Makes sure that Maps are sane'''
        m = {"Google": "http://google.com", 234: "http://234next.com", 1.345: "http://base.com"}
        self.bookmarks.update(m)
        for k, v in m.items():
            self.assertEquals(self.bookmarks[str(k)], v)
    
    def testMapDoesValidation(self):
        """Makes sure that Maps do validation"""
        with self.assertRaises(Exception):
            self.test.bookmarks["hello"] = 1
            self.cls.bookmarks.convert(self.test)

    def testThatMapDidSave(self):
        '''Shows that Maps persist to the database'''
        pass
        

@skip("Fails, Not implemented yet")   
class TestList(TestCase):
    """Tests for List() descriptor"""
    def setUp(self):
        class Family(object):
            birthdays = List(date)
            nested = List(List(String))
        self.test = Family()
    
    def testListSanity(self):
        """Sanity checks for List()"""
        sample = [ date(1990,8,5) for i in range(10)]
        self.test.birthdays = sample
        self.test.nested.extend([["Hello", "World", ], ["Another", "Yes",]])
        print self.test.nested
        self.assertEqual(self.test.birthdays, sample)
    
    def testListHandlesNones(self):
        '''List should throw an error for Nones'''
        self.test.birthdays = None
    
    def testListTypeChecking(self):
        """This test should fail. It verifies that List type checking works"""
        sample = [i for i in range(10)]
        with self.assertRaises(Exception):
            self.test.birthdays = sample       

@skip("Fails, Not implemented yet")             
class TestSet(TestCase):
    """Tests for Set() descriptor"""
    def setUp(self):
        class Person(object):
            spouses = Set(String, default = set(["amy","tiffy"]))
            pets = Set(Float)
        self.test = Person()
    
    def testSetSanity(self):
        """Sanity checks, for Sets; """
        print self.test.spouses
        print self.test.pets
        self.assertEquals(self.test.spouses,set(["amy","tiffy"]))
        self.test.pets = set([1,2,3,])
        print self.test.pets
        self.assertEquals(self.test.pets, set([1.0, 2.0, 3.0,]))
        
    def testSetsAreHomogenous(self):
        """asserts that Sets contents are homogeneous and validated"""
        with self.assertRaises(Exception):
            self.test.pets = set(["Hello", "I should fail",])
                                  
