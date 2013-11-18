# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 20:44:15 2013

@author: zah
"""
import usbtmc

class TestDevice(object):
    def write(self, s):
        return None
    def ask(self, s):
        return s
    def ask_raw(self, s):
        return s

class USBDevice(usbtmc.Instrument):
    pass