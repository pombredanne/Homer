#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Useful builtin functions and classes for everyday use of Homer.
"""
__all__ = ["tag", "object"]

def tag(object):
    """Returns a human readable globally unique id for this object (format :http://taguri.org)"""
    if not isinstance(object, Record):
        raise ValueError("%s : must be a subclass of Record" % object)
    

class object(object):
    ''' An object that adds an automatic keyword based constructor to any object'''
    def __init__(self, **keywords):
        for name, value in keywords.items():
            setattr(self, name, value)
                
