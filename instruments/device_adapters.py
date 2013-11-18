# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 20:44:15 2013

@author: zah
"""
import usbtmc

class BaseDevice(object):
    def __init__(self):
        self.idn = self.ask("*idn?")
    
    def get_model(self):
        pass
    def get_serial_number(self):
        pass

class TestDevice(object):
    def write(self, s):
        return None
        
    def ask(self, s):
        return s
        
    def ask_raw(self, s):
        return s

class USBDevice(usbtmc.Instrument):
    pass