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
            

def fields(object, type):
        """Searches class hierachy and returns all known properties for this object"""
        cls = object.__class__;
        fields = {}
        for root in reversed(cls.__mro__):
            for name, prop in root.__dict__.items():
                if isinstance(prop, type):
                    fields[name] = prop
        return fields
                
