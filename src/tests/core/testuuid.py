#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the Default Property...
"""
from unittest import TestCase,expectedFailure,skip
from homer.core.commons import UUID
from homer.core.models import BadValueError, key, Model
    
class TestUUID(TestCase):
    '''Unittests for the UUID Descriptor'''
    
    def setUp(self):
        '''Create a sample set up object'''
        class Person(object):
            id = UUID()
        self.person = Person()

    def testGeneration(self):
        '''Shows that UUID Properties generate UUID's even when they've not been set'''
        value = self.person.id
        print "\n................................................."
        print "UUID: %s" % (value,)
        print "................................................."
        self.assertTrue(value is not None)
        self.assertEquals(value, self.person.id)
        
    def testSanity(self):
        '''Shows that UUID Descriptors are READWRITE/DELETE'''
        value = self.person.id
        del self.person.id
        self.assertTrue(self.person.id is not None)
        self.assertNotEquals(value, self.person.id)
        self.person.id = value
        self.assertEquals(value, self.person.id)
        self.assertRaises(BadValueError, lambda: setattr(self.person, "id", "Hello"))
        
