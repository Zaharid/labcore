# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 17:16:50 2013

@author: root
"""

import usbtmc

devices = usbtmc.list_devices()

instruments = [usbtmc.Instrument(dev) for dev in devices]

for instr in instruments:
    print instr.ask("*idn?")