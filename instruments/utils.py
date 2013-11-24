# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 18:33:43 2013

@author: zah
"""
import inspect
from functools import wraps
from django.db.models import signals

import re

def autoconnect(cls):
    """ 
    Class decorator that automatically connects pre_save / post_save signals on 
    a model class to its pre_save() / post_save() methods.
    """
    issignal = lambda x: isinstance(x,signals.Signal)
    allsignals = inspect.getmembers(signals, issignal)
    def connect(signal, func):
        cls.func = staticmethod(func)
        @wraps(func)
        def wrapper(sender, **kwargs):
            return func(kwargs.pop('instance'), **kwargs)
        signal.connect(wrapper, sender=cls)
        return wrapper
        
    for (name, method) in allsignals:
        if hasattr(cls, name):
            setattr(cls, name, connect(method, getattr(cls, name)))
        
    return cls 
    

def normalize_name(name):
    name = re.sub(r"\ ", '_', name)
    if not (re.match("^[a-zA-Z][a-zA-Z0-9_]*$", name)):
        raise ValueError("The identifier '%s' is not a valid command name"%name)
    return name

    
#==============================================================================
#     if hasattr(cls, 'pre_save'):
#         cls.pre_save = connect(signals.pre_save, cls.pre_save)
# 
#     if hasattr(cls, 'post_save'):
#         cls.post_save = connect(signals.post_save, cls.post_save)
#         
#     if hasattr(cls, 'pre_init'):
#         cls.pre_init = connect(signals.pre_init, cls.pre_init)
#         
#     if hasattr(cls, 'post_init'):
#         cls.post_init = connect(signals.post_init, cls.post_init)
#==============================================================================

