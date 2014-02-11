# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 19:24:50 2014

@author: zah
"""
import mongoengine
from mongoengine import fields

mongoengine.connect('labcore')

class Parameter(mongoengine.EmbeddedDocument):
    name = fields.StringField()

class IObject(mongoengine.Document):
    name = fields.StringField()
    pinputs = fields.ListField(fields.EmbeddedDocumentField(Parameter))
    
c1 = Parameter(name = "uno")
c2 = Parameter(name = "dos")
p = IObject(name = "tres")
p.pinputs = [c1,c2]
p.save()