"""
Author : Iroiso . I (iroiso@live.com)
Copyright 2011
License: Apache License 2.0
Module: Utility functions and classes.
File Description: Utility functions for the SDK.

"""
class Schema(object):
    """Provides static methods that can be used to test if objects conform to Schema types"""
    
    @staticmethod
    def isSimple(object):
        """Is @object a simple type"""
        pass
        
    @staticmethod
    def isComplex(object):
        """Is @object a complex type ?"""
        pass
    
    @staticmethod
    def isSequence(object):
        """Is @object a sequence type ?"""
        pass
    
    @staticmethod
    def isMapping(object):
        """Is @object a mapping ? e.g. dict """
        pass
    
    def isSet(object):
        """Is @object a set of any kind ? """
        pass
    
"""
Size:
Size provide utilities for checking size of objects in Kb, Mb and Gb.
"""    
class Size(object):
    """Provides utility functions to convert to and from bytes,kilobytes, etc."""
    
    @staticmethod
    def inBytes(object):
        """Returns the size of this python object in bytes"""
        view = memoryview(object)
        return len(view) * view.itemsize


"""
Validation:
Provides utility methods for common type validation
"""
class Validation(object):
    '''Provides utility methods for validation of common types'''
    
    @staticmethod
    def validateString(value, exception = ValueError, length = 500, emptyOk = True):
        """ Utility method for validating strings """
        if value is None and emptyOk:
            return value
        if isinstance(value, basestring):
            if not len(value) <= length:
                raise exception("Your String must not be longer than: %s" % length)
            return value   
        else:
            raise exception("Expected String, Got: %s" % value)
