# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 18:00:09 2013

@author: zah
"""
import instruments

osc = instruments.load_instrument('osc')

def init():
    osc.reset()
    osc.set_probe(1,1)
    osc.set_probe(2,1)
    osc.enable_generator(1)
    osc.device.timeout = 1
    
def measure(freq):
    osc.set_generator_frequency(freq)
    osc.autoscale()
    osc.set_acquire_type('AVERAGE')
    phase = osc.measure_phase()
    return phase