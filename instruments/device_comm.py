# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 16:49:36 2013

@author: zah
"""


from django.core.exceptions import ObjectDoesNotExist

from device_adapters import TestDevice, USBDevice



active_interfaces = ( 
                     TestDevice,
                     USBDevice,
            )
            
def test_mode():
    global active_interfaces
    active_interfaces = (TestDevice,)
            
active_devices = None

class DevObj(object):
    def __init__(self, product_id, device):
        self.product_id = product_id
        self.device = device
    def __repr__(self):
        return self.device.__repr__()

def find_all():    
    if active_devices is None:
        refresh_devices()
    return active_devices

def refresh_devices():
    global active_devices
    active_devices = {}
    for iface in active_interfaces:
        for name, product, device in iface.get_instruments():
            
            
            active_devices[name] = (active_devices.get(name, []) +
                                    [DevObj(product, device)])

def get_device(model, product_id):
    try:
        l = find_all()[model]
    except KeyError:
        raise ValueError("No device of type %s found." % model)
    try:
        item = next(x for x in l if x.product_id == product_id)
    except StopIteration:
        raise ValueError("The '%s' device of type %s is not found" 
                            % (product_id, model))
    return item
    
    
                
def next_not_controlled(name):
    l = find_all()[name]
    for devobj in l:
        try:
            c = devobj.device.is_controlled
        except AttributeError:
            return devobj
        if not c:
            return devobj

def associate_known():
    from instruments import models
    instruments = []
    for devname, devlist in find_all().items():
        for (product_id, device) in devlist:
            try:            
                ins = models.Instrument.objects.get(device_id = devname)
                ins.associate(device)
                instruments.append(ins)            
            except ObjectDoesNotExist:
                pass
    
    return instruments
    
def create_instrument(name, base_instrument, device_id, devobj = None):
    """Creates an instrument object from an active device and initializes it
    so that it can emit commands."""
    from instruments import models as m
    if isinstance(base_instrument, str):
        base_instrument = m.BaseInstrument.objects.get(name = base_instrument)
    ins = m.Instrument.objects.create(name = name, 
                                     base_instrument = base_instrument, )
    if devobj is None:
        devobj = next_not_controlled(device_id)
    ins.associate(devobj.device)
    return ins
    
def find_unknown():
    from instruments import models
    alldevs = find_all()
    unknown = {k: v for k,v in alldevs.items() 
        if not models.Instrument.objects.filter(device_id = k).exists()}
    return unknown
    
