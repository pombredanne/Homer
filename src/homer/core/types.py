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

__all__ = ["phone", "rating",]


class phone(object):
    '''A Phone number in international format'''
    
    def __init__(self, country, number):
        '''country == 'country code' number == 'local number' '''
        country, number = country.strip(), number.strip()
        if country[0] != '+':
            raise ValueError("Country code must begin with a '+'")
        # Strip out all non numbers, and remove the first zeros
        value = [c for c in number if c.isdigit()]
        if value[0] == '0':
            value = value[1:]    
        self.number = ''.join(value)
        self.country = country
    
    def __repr__(self):
        '''Returns a phone object as a tuple'''
        return "phone('%s', '%s')" % (self.country, self.number)
    
    def __eq__(self, other):
        '''Equality tests'''
        assert isinstance(other, phone),"%s must be a phone type" % other
        return self.number == other.number and self.country == other.country
            
    def __str__(self):
        '''String representation of an international phone number'''
        return self.country + self.number


