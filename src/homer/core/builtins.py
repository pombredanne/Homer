#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Useful builtin functions and classes for everyday use of Homer.
"""
__all__ = ["object"]


class object(object):
    ''' An object that adds an automatic keyword based constructor to any object'''
    def __init__(self, **keywords):
        for name, value in keywords.items():
            setattr(self, name, value)

def fields(cls, instance):
    '''Searches a class heirachy for instances of a particular type'''
    if not isinstance(cls, type): cls = cls.__class__
    results = {}
    def add(name, prop):
        if isinstance(prop, instance) and not name.startswith("_"):
            results[name] = prop
    for root in reversed(cls.__mro__):
        for name, prop in root.__dict__.items():
            add(name, prop) 
    return results
    

