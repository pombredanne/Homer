
# Author : Iroiso . I 
# Copyright 2011
# License: Apache License 2.0
# Module: Utility functions and classes.
# File Description: Utility functions for the SDK.

# Copyright 2011 June Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import sys

__all__ = ["Size", ]
"""
Size:
Size provide utilities for checking size of objects in Kb, Mb and Gb.
"""    
class Size(object):
    """Provides utility functions to convert to and from bytes,kilobytes, etc."""
    
    @staticmethod
    def inBytes(object):
        """Returns the size of this python object in bytes"""
        return sys.getsizeof(object)

