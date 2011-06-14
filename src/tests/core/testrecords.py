#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the records module...
"""
from unittest import TestCase,expectedFailure,skip
from homer.core.records import key, Record
from homer.core.types import Property

class TestKeyAndRecord(TestCase):
    """Keys and Record where built to work together; they should be tested together"""
    
    def testkeySanity(self):
        """Makes sure that basic usage for @key works"""
        @key("name")
        class Person(Record):
            name = Property("JohnBull")
            
        assert isinstance(Person, type)
        person = Person()
        assert person.key() is not None, "Key Must not be None when its attribute is non null"
        self.assertTrue(person.name == "JohnBull")
        print "'" + str(person.key()) + "'"
        print person.key().toTagURI()
        person.name = None
        assert person.key() is None, "Key Should be None when its attribute is not set"
        
    def testkeyAcceptsOnlyRecords(self):
        """Asserts that @key only works on subclasses of Record"""
        with self.assertRaises(TypeError):
            @key("name")
            class House(object):
                name = Property("House M.D")
    
    def testkeyChecksifKeyAttributeExists(self):
        """Asserts that the attribute passed in to @key must exist in the class"""
        with self.assertRaises(Exception):
            @key("name")
            class House(Record):
                pass
    
    def testRecordAcceptsKeywords(self):
        """Tests If accepts keyword arguments and sets them"""
        diction = { "name": "iroiso", "position" : "CEO", "nickname" : "I.I"}
        class Person(Record):
            name = Property()
            position = Property()
            nickname = Property()
        
        person = Person(**diction)
        for name in diction:
            self.assertEqual(getattr(person,name), diction[name])
        print "..........................................."
        for name, value in person.fields().items():
            print name, str(value)

    def testRecordsDoesNotAllowExpansion(self):
        """Shows that record does not allow expansion"""
        @key("name")
        class Person(Record):
            name = "Iroiso"
            birthdate = "Aug 5th 1990"
        
        person = Person()
        with self.assertRaises(AttributeError):
            person.girlfriend = "Natasha"
               

