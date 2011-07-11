#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the Differ Module...
"""
from unittest import TestCase
from homer.core.differ import Differ
from homer.core.models import Model, key
from homer.core.commons import Integer, Float, String


class TestDiffer(TestCase):
    '''Basic tests for the current differ implementation'''
    def testSanity(self):
        '''Sanity tests for differ'''
        class Simple(Model):
            pi = Float()
            name = String()
            instances = Integer()
            
        simple = Simple(pi = 3.142, name = "Hello", instances = 500)
        del simple.name
        self.assertEquals(list(simple.differ.deleted()), ["name",])
        simple.instances = 20
        self.assertEquals(list(simple.differ.modified()), ["instances",])
        simple.stuff = ["Some stuff here".split()]
        self.assertEquals(list(simple.differ.added()), ["stuff",])
        simple.differ.commit()
        simple.name = "Another-name"
        simple.stuff.append("Some-more")
        self.assertEquals(list(simple.differ.added()), ["name",])
        self.assertEquals(list(simple.differ.modified()), ["stuff",])
    
    def testRevert(self):
        '''Tests differ.revert()'''
        class Simple(Model):
            pi = Float()
            name = String()
            instances = Integer()
        simple = Simple(pi = 3.142, name = "Hello", instances = 500)
        del simple.pi; del simple.name; del simple.instances
        simple.differ.revert()
        self.assertEquals(simple.pi, 3.142); self.assertEquals(simple.name, "Hello"); self.assertEquals(simple.instances, 500)
        
        
            
    
