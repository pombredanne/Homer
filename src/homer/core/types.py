#!/usr/bin/env python

"""
Author : Iroiso,
Project: Homer SDK
License: Apache License 2.0
Copyright 2012, June inc.

Description:
Common data types for the homer project, these classes
are designed to 'look like' builtin classes, e.g.

mobile = phone('+1', '(248) 123-7654')
assert mobile.country == "+1"
assert mobile.number == '2481237654'
"""
import sys
import json
import hashlib

__all__ = ["phone", "blob",]


class phone(object):
    '''A Phone number in international format'''
    def __init__(self, country, number):
        '''country == 'country code' number == 'local number' '''
        assert isinstance(country, str) and isinstance(number, str), "Type Error, Please use strings instead"
        country, number = country.strip(), number.strip()
        if country[0] != '+':
            raise ValueError("Country code must begin with a '+'")
        # Strip out all non numbers, and remove the first zeros
        value = [c for c in number if c.isdigit()]
        if value[0] == '0':
            value = value[1:]    
        self.number = ''.join(value)
        self.country = country
    
    def __eq__(self, other):
        '''Equality tests'''
        assert isinstance(other, phone),"%s must be a phone type" % other
        return self.number == other.number and self.country == other.country
            
    def __str__(self):
        '''String representation of an international phone number'''
        return self.country + self.number
    
    def __repr__(self):
        '''Returns a phone object as a tuple'''
        return "phone('%s', '%s')" % (self.country, self.number)


class blob(object):
    '''A opaque binary object with a content-type and description'''
    def __init__(self, content="", mimetype="application/text", description="", **keywords):
        '''Basic constructor for a blob'''
        self.metadata = {}
        self.content = content
        self.mimetype = mimetype
        self.description = description
        self.metadata.update(keywords)
        self.checksum = self.__md5(content)
    
    def __md5(self, content):
        '''Calculates the md5 hash of the content and returns it as a string'''
        m = hashlib.md5()
        m.update(content)
        return m.hexdigest()
            
    def __eq__(self, other):
        '''Compares the checksums if @other is a blob, else it compares content directly''' 
        if isinstance(other, blob):
            return self.checksum == other.checksum
        else: 
            return self.content == other
    
    def __sizeof__(self):
        '''Returns the size of this blob, this returns the size of the content string'''
        return sys.getsizeof(self.content)
        
    def __repr__(self):
        '''Returns a JSON representation of the contents of this blob'''
        dump = {"metadata": self.metadata, "content": self.content,\
           "mimetype": self.mimetype, "description": self.description, 
                        "checksum": self.checksum}
        return json.dumps(dump)
        
    def __str__(self): 
        '''Returns a human readable string representation of the blob'''
        return "Blob: [mimetype:%s, checksum:%s, description:%s]" % \
            (self.mimetype, self.checksum, self.description)
            
