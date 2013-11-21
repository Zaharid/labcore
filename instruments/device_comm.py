# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 16:49:36 2013

@author: zah
"""
from django.core.exceptions import ObjectDoesNotExist

from device_adapters import TestDevice, USBDevice
from instruments.models import Instrument

active_interfaces = ( 
                     TestDevice,
                     USBDevice,
            )

def find_all():
    return {name:device for iface in active_interfaces
            for (name, device) in iface.get_instruments() 
            }
                

def associate_known():
    instruments = []
    for devname, device in find_all().items():
        try:
            ins = Instrument.objects.get(device_id = devname)
            ins.associate(device)
            instruments.append(ins)            
        except ObjectDoesNotExist:
            pass
    
    return instruments

def find_unknown():
    alldevs = find_all()
    unknown = {k: v for k,v in alldevs.items() 
        if not Instrument.objects.filter(device_id = k).exists()}
    return unknown
    
