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
from .testdb import BaseTestCase
from homer.core.commons import String, Integer
from homer.core.models import BadValueError, key, Model
    
class TestUUID(BaseTestCase):
    '''Persistence Unittests for the UUID Descriptor'''

    def testPersistence(self):
        '''Checks if persistence using UUID's work'''
        @key("id")
        class Person(Model):
            id = UUID()
            name = String()
            age = Integer()
            
        person = Person(name="Iroiso", age=50)
        person.save()
        value = str(person.id)
        
        found = Person.read(value)
        print "First: %s , Second: %s" % (value, found.id)
        assert person == found, "They must be equal"
        assert value == str(found.id), "The UUID's must be equal too"
    
        
        
