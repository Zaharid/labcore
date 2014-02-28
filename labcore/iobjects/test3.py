# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 16:49:39 2014

@author: zah
"""

from labcore.iobjects.models import (IOGraph, IONode, Link, IOSimple, Input, Output,)

g =  IOGraph()
ions = []
for i in range(5):
    io = IOSimple(name = "io%d"%i)
    i1 = Input(name = "i1")
    i2 = Input(name = "i2")
    o1 = Output(name = "o1")
    o2 = Output(name = "o2")
    io.inputs = [i1,i2]
    io.outputs = [o1,o2]
    io.save()
    ion = IONode(io)
    ions += [ion]

g.nodes = ions

g.bind(ions[0], 'i1', ions[2], 'o1')
g.save()