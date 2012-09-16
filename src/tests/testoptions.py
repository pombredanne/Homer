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
from homer.options import Settings

class TestOptions(TestCase):
    """Test for the options.options"""
    
    def testLogger(self):
        """Tests options.logger() to make sure its not none"""
        assert Settings.logger() is not None, "options.logger() should not return\
            None"

