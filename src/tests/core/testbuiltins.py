#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Tests for the builtins module
"""
from unittest import TestCase
from homer.core.builtins import RecordObserver

class TestRecordObserver(TestCase):
    """Y'up I'm only testing the singleton"""
    def testCapturesEvents(self):
        """Does a RecordObserver capture events?"""
        pass
    
    def testModified(self):
        """Tests RecordObserver.modified"""
        pass
    
    def testDeleted(self):
        """Tests RecordObserver.deleted"""
        pass
        
    def testAdded(self):
        """Tests RecordObserver.added"""
        pass
    
    def testClear(self):
        """Tests RecordObserver.clear"""
        pass
