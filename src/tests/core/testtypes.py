#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for homer.core.types
"""
from homer.core.types import phone, blob
from unittest import TestCase,expectedFailure,skip

class TestPhone(TestCase):
    '''Unittests for the phone type'''
    
    def testSanity(self):
        '''Makes sure that basic usage is sane'''
        with self.assertRaises(ValueError):
            mobile = phone("(0248) 123-7654")
        mobile = phone("+2348094486101")
    
    def testRepr(self):
        '''Makes sure that phones get a valid python repr'''
        mobile = phone("+2348094486101")
        self.assertEquals(eval(repr(mobile)), mobile)
        
    def testStr(self):
        '''Makes sure that phones are properly stringified'''
        mobile = phone("+2342481237654")
        self.assertEquals("+2342481237654", str(mobile))
        
class TestBlob(TestCase):
    '''Unittests for the blob type'''
    
    def testSanity(self):
        '''Makes sure that basic usage is sane'''
        image = blob(content="Some rubbish text from a file" * 1024, mimetype="image/jpeg", gzipped=True)
        self.assertTrue(image.checksum != None)
        self.assertTrue("gzipped" in image.metadata)
        self.assertTrue(repr(image)) 
