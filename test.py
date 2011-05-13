#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Copyright 2011
License: Apache License 2.0
Description: Utility for running all the selected or all tests in the tests package

Usage:
At prompt change to the project directory.
To run all tests type:
$./test.py 

To run specific tests type:
$./test.py testrecor* testproper*

The above example runs all the tests that match the unix filename patterns provided.

"""
import sys
import os.path
from glob import glob
from unittest import TextTestRunner,TestLoader,TestSuite

"""Configure Path"""
sys.path.extend(["./src",])
"""##############"""

def find(*argument):
    """Discovers tests from the tests package and returns them"""
    base = "src/tests/"
    suite = TestSuite()
    if not argument:
        suite = TestLoader().discover(base)
    elif argument:
        for i in argument:
            found = TestLoader().discover(start_dir = base, pattern = i)
            suite.addTest(found)
    return suite


if __name__ == "__main__":
    """ Find unittests and run them """
    arguments = sys.argv[1:]
    suite = find(*arguments)
    runner = TextTestRunner(verbosity = 2)
    runner.run(suite)
    
