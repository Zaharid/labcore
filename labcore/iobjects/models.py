# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""

import mongoengine as mg
from mongoengine import fields

mg.connect('labcore')

INPUT_METHODS = ('constant', 'user_input', 'io_input')

class Parameter(mg.EmbeddedDocument):
    name = fields.StringField(required = True, max_length=256, unique=True)
    param_type = fields.StringField(default="STR")
    input_method = fields.StringField(choices=INPUT_METHODS, 
                                      default="user_input")
    default = fields.DynamicField()
    value = fields.DynamicField()
    to = fields.ReferenceField('IObject')

    

    

class IObject(mg.DocumentIObject):

    
    meta = {'allow_inheritance': True}
    
    
    name = fields.StringField(required = True, max_length=256)
    inputs = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    outputs = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    dispays = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    
    
    address = fields.StringField()
    executed = fields.BooleanField(default = False)
    log_output = fields.BooleanField(default = False)
    
    def run(self):
        params = {}
        for inp in self.inputs:
            if inp.input_method == "io_input" and not inp.to.executed:
                #TODO: Wait,etc                
                inp.to.run()
                
            params[inp.name] = inp.value
        results = self.execute(**params)
        
        for out in self.outputs:
           out.value = results[out.name]
         
        self.executed = True
        
class IOSimple(IObject):
    
    def execute(self, **kwargs):
        results = {}
        for out in self.outputs:
            results[out.name] = "OK"
        
        return results
    
    
    


    

    
    
    

    
    
class IOGraph():
    pass

    
    