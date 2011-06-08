"""
Author : Iroiso . I (iroiso@live.com)
Copyright 2011
License: Apache License 2.0
Module: Utility functions and classes.
File Description: Utility functions for the SDK.

"""
class Size(object):
    """Provides utility functions to convert to and from bytes,kilobytes, etc."""
    
    @staticmethod
    def inBytes(object):
        """Returns the size of this python object in bytes"""
        view = memoryview(object)
        return len(view) * view.itemsize


class Validator(object):
    '''Provides utility methods for validation of common types'''
    
    @staticmethod
    def ValidateString(value, exception = ValueError, length = 500, emptyOk = True):
        """
        Utility method for validating strings; Returns the value you passed in
        if it is valid.
        
        Raises: ValueError or the user defined exception if String is not valid
        """
        if value is None and emptyOk:
            return value
        if isinstance(value, basestring):
            if not len(value) <= length:
                raise exception("Your String must not be longer than: %s" % length)
            return value   
        else:
            raise exception("Expected String, Got: %s" % value)
