# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 18:42:58 2014

@author: zah
"""

import models

ios = []
for i in range(5):
    i1 = models.Input(name = "i1", value = 'uno')
    i2 = models.Input(name = "i2", value = 'dos')
    o1 = models.Output(name = "o1")
    o2 = models.Output(name = "o2")
    
    io = models.IOSimple(name = "IO%i"%i)
    io.inputs = [i1,i2]
    io.outputs = [o1,o2]
    
    io.save()                
    ios += [io]
    globals()['io%i'%i] = io
    
io0= ios[0]
io0.bind_to_input(ios[1],["o1"],['i1'])