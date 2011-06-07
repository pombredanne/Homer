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
from homer.core.records import Record,key, Key

"""#.. Tests for homer.core.record.key"""
class TestKeyAndRecord(TestCase):
    """Tests for the @key decorator"""
    @expectedFailure
    def testkeySanity(self):
        """Makes sure that basic usage for @key works"""
        @key("name")
        class Person(Record):
            name = "Iroiso Ikpokonte"
        assert isinstance(Person, type)
        person = Person()
        assert person.kind is not None, "This cannot be None"
        assert person.key is not None, "This should not be None"
        assert person.name == "Iroiso Ikpokonte", "Yup, this should not happen too"
        person.name = None
        assert person.key is None, "Yup, this should be None"
        
    def testkeyAcceptsOnlyRecords(self):
        """Asserts that @key only works on subclasses of Record"""
        with self.assertRaises(TypeError):
            @key("name")
            class House(object):
                name = "House M.D"
    
    def testkeyChecksifKeyAttributeExists(self):
        """Asserts that the attribute passed in to @key must exist in the class"""
        with self.assertRaises(AssertionError):
            @key("name")
            class House(Record):
                pass
    
    @expectedFailure
    def testRecordAcceptsKeywords(self):
        """Tests If accepts keyword arguments and sets them"""
        diction = { "name": "iroiso", "position" : "CEO", "nickname" : "I.I"}
        person = Record(**diction)
        for name in diction:
            self.assertTrue(hasattr(person, name))
  
    def testRecordKey(self):
        """Tests that Record.key works"""
        @key("name", namespace = "com.june.news")
        class Story(Record):
            name = "No time dimension" 
        story = Story()
        assert story.key is not None, "You should have a key"
        self.assertTrue(story.key.complete)
        print "'" + str(story.key) + "'"
        story.name = "Michael Jackson Dies"    
     
        
               

