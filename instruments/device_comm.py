# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 16:49:36 2013

@author: zah
"""
from device_adapters import TestDevice, USBDevice
from models import Instrument

active_interfaces = ( 
                     TestDevice,
                     USBDevice,
            )

def find_instruments():
    return [instuple for iface in active_interfaces
            for instuple in iface.get_instruments() ]
                

def associate_known():
    for name, instrument in find_instruments():
        pass