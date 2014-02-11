# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""

import mongoengine as mg

mg.connect('labcore')

class Parameter(mg.EmbeddedDocument):
    name = mg.StringField(required = True, max_length=256)
    ptype = mg.StringField(default = "STR")
    default = mg.DynamicField()
    value = mg.DynamicField()

    

class IObject(mg.Document):
    name = mg.StringField(required = True, max_length=256)
    inputs = mg.ListField(mg.EmbeddedDocumentField(Parameter))
    outputs = mg.ListField(mg.EmbeddedDocumentField(Parameter))
    dispays = mg.ListField(mg.EmbeddedDocumentField(Parameter))
    address = mg.StringField()
    executed = mg.BooleanField(default = False)
    log_output = mg.BooleanField(default = False)
    def run_(self):
        results = self.execute()
    

class IONode():
    node = mg.ReferenceField(IObject, reverse_delete_rule = mg.CASCADE)
    
    
class IOGraph():
    pass

    
    