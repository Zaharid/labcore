# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 20:44:15 2013

@author: zah
"""
from itertools import count
from collections import namedtuple
import usbtmc

DeviceInfo = namedtuple('DeviceInfo', ['model', 'prodct_id', 'device_object'])

class BaseDevice(object):
    def identify(self):
        try:
            m = self.model
            p = self.product_id
        except AttributeError:
            self.idn = self.ask("*idn?")
            idinfo = self.idn.split(',')
            self.model = ",".join(idinfo[0:2])
            self.product_id = idinfo[2]
            m = self.model
            p = self.product_id
        return DeviceInfo(m, p, self)
    
    @classmethod
    def get_instruments(cls):
        return [dev.identify() for dev in cls.list_instruments()]
    def __repr__(self):
        return "<Device %s as %s>" % (self.product_id, self.__class__.__name__)


class TestDevice(BaseDevice):
    product = count()
    def __init__(self, model = 'TEST DEVICE', product_id = None):
        self.model = model
        if product_id is None:
            self.product_id = "PRODUCT %i" % next(TestDevice.product)
    def write(self, s):
        return None
        
    def ask(self, s):
        return s
        
    def ask_raw(self, s):
        return s
        
    @classmethod
    def list_instruments(cls):
        return [TestDevice(), TestDevice(), TestDevice("TEST DEVICE 2")]

class USBDevice(usbtmc.Instrument, BaseDevice):
    @classmethod    
    def list_instruments(cls):
        devices = usbtmc.list_devices()
        return [USBDevice(dev) for dev in devices]

