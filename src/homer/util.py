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


