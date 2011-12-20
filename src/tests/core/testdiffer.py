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
        simple.differ.commit()
        del simple.name
        self.assertTrue("name" in simple.differ.deleted())
        simple.instances = 20
        self.assertTrue("instances" in simple.differ.modified())
        simple.stuff = ["Some stuff here".split()]
        self.assertTrue("stuff" in simple.differ.added())
        simple.differ.commit()
        simple.name = "Another-name"
        simple.stuff.append("Some-more")
        self.assertTrue("name" in simple.differ.added())
        self.assertTrue("stuff" in simple.differ.modified())
    
    def testRevert(self):
        '''Tests differ.revert()'''
        class Simple(Model):
            pi = Float()
            name = String()
            instances = Integer()
        simple = Simple(pi = 3.142, name = "Hello", instances = 500)
        simple.differ.commit()
        del simple.pi; del simple.name; del simple.instances
        simple.differ.revert()
        self.assertEquals(simple.pi, 3.142); self.assertEquals(simple.name, "Hello"); self.assertEquals(simple.instances, 500)
        
        
            
    
