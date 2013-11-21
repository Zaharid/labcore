# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 20:44:15 2013

@author: zah
"""
import usbtmc

class BaseDevice(object):
    def identify(self):
        try:
            m = self.model
        except AttributeError:
            self.idn = self.ask("*idn?")
            self.model = ",".join(self.idn.split(',')[0:2])
            m = self.model
        return (m, self)
    
    @classmethod
    def get_instruments(cls):
        return [dev.identify() for dev in cls.list_instruments()]


class TestDevice(BaseDevice):
    def __init__(self):
        self.model = "TEST DEVICE"
    def write(self, s):
        return None
        
    def ask(self, s):
        return s
        
    def ask_raw(self, s):
        return s
        
    @classmethod
    def list_instruments(cls):
        return [TestDevice()]

class USBDevice(usbtmc.Instrument, BaseDevice):
    @classmethod    
    def list_instruments(cls):
        devices = usbtmc.list_devices()
        return [USBDevice(dev) for dev in devices]

