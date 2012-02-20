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
from homer.core.models import Default
    
class TestDefault(TestCase):
    '''Does Default work as I expect'''
    def setUp(self):
        '''Creates a sample class with a Default Property installed on it'''
        class Sample(object):
            '''The simplest default class'''
            default = Default()
        self.cls = Sample
        self.sample = Sample()

    def testSanity(self):
        '''Tests Expected Behaviour'''
        self.assertRaises(AttributeError, lambda : delattr(self.sample, "default"))
        self.assertRaises(AttributeError, lambda : setattr(self.sample, "default", "Hello"))
        values = self.sample.default
        self.assertTrue(values)
        self.assertTrue(len(values) == 2)
        
