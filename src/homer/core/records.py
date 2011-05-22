#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Provides Record, Descriptor and Type
"""
from homer.core.options import options

__all__ = ["Record", "Type", ]

"""
Record:
Unit of Persistence; Any class you want to be persistable should extend this class

"""
class Record(object):
    """Unit of Persistence..."""
    pass



"""
Type:
A Descriptor that does type coercion, checking and validation.
#..

class Story(Record):
    source = Type(Blog)
    
"""
class Type(Property):
    """A Descriptor that does coercion and validation"""
    pass
    



"""
Property:
Base class for all data descriptors; 
"""
class Property(object):
    """A Generic Descriptor which can be READONLY or READWRITE"""
    pass
    
    

