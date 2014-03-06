# -*- coding: utf-8 -*-
"""
Created on Thu Mar  6 21:55:34 2014

@author: zah
"""

import mongoengine as mg
from models import Link, Input, Output, IONode, IObject
from mongotraits import Document, EmbeddedDocument
mg.connect('test')


n = IONode(IObject(name = "UM"))

inp = Input(name = "i")
o = Output(name = "o")
print inp.eid

n.inputs = [inp]
n.outputs= [o]

print n

class Doc(Document):
    embs = mg.ListField(mg.EmbeddedDocumentField(Link))

d = Doc()

for i in range(3):
    x = Link(to = n, fr = n, fr_input = inp, to_output = o)
    d.embs += [x]

d.save()