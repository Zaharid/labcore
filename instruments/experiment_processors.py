# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 22:45:51 2013

@author: zah
"""
import functools
import time

from zutils.utils import make_signature

def add_timeout(f, command, argnames, kwargdefaults, timeout = 1.0):
    @functools.wraps
    def f_(*args, **kwargs):
        result = f(*args, **kwargs)
        time.sleep(timeout)
        return result
    return make_signature(f_, argnames, kwargdefaults)
    