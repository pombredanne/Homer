#!/usr/bin/env python
"""
Author : Iroiso . I (iroiso@live.com)
Project: Homer SDK
License: Apache License 2.0
Copyright 2011, June inc.

Description:
Module that provide Event Notification for the Core
"""
__all__ = ["Event", "Observer", ]

class Event(object):
    """Base class of all Events"""
    pass
    

class Observer(object):
    """I know how to register event watchers and broadcast events"""
    pass


class Observable(object):
    """Extend this class if you want your class to notify listeners """
    pass
