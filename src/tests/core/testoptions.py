#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Unittests for the options module...
"""
from unittest import TestCase
from homer.core.options import options

class TestOptions(TestCase):
    """Test for the options.options"""
    
    def testLogger(self):
        """Test options.logger()"""
        assert options.logger() is not None, "options.logger() should not return\
            None"
            
