# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:26:40 2014

@author: zah
"""
import mongoengine as mg
import models

o1 = models.Output(name = 'o1')
o2 = models.Output(name = 'o2')
io = models.IObject(name = 'io')
io.outputs += [o1,o2]
io.save()
g = models.IOGraph()
g.nodes += [models.IONode(io)]
g.save()
l = models.Link()
l.to_output = o1
l.fr = g.nodes[0]
print l.to_output
print l.fr

class Test(mg.Document):
    a = mg.IntField()
    b = mg.IntField()