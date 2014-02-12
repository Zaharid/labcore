# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""

import mongoengine as mg
from mongoengine import fields

mg.connect('labcore')

class Parameter(mg.EmbeddedDocument):
    name = fields.StringField(required = True, max_length=256)
    ptype = fields.StringField(default = "STR")
    default = fields.DynamicField()
    value = fields.DynamicField()
    
    def __unicode__(self):
        return self.name

    

class IObject(mg.Document):
    name = fields.StringField(required = True, max_length=256)
    inputs = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    outputs = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    dispays = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    address = fields.StringField()
    executed = fields.BooleanField(default = False)
    log_output = fields.BooleanField(default = False)
    def run_(self):
        results = self.execute()
    
    def __unicode__(self):
        return self.name
    

class IONode():
    node = mg.ReferenceField(IObject, reverse_delete_rule = mg.CASCADE)
    
    def __unicode__(self):
        return self.node.name
    
    
class IOGraph():
    pass

    
    