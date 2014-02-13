# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""

import mongoengine as mg
import networkx
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
    
        
    def __unicode__(self):
        return self.name

    

    

class IObject(mg.Document):

    
    meta = {'allow_inheritance': True}
    
    
    name = fields.StringField(required = True, max_length=256)
    inputs = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    outputs = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    dispays = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    
    def _paramdict(self, paramlist):
        return {param.name : param for param in paramlist}

    def inputdict(self):
        return self._paramdict(self.inputs)
    
    def displaydict(self):
        return self._paramdict(self.displays)
    
    def outputdict(self):
        return self._paramdict(self.outputs)
    
    @property
    def links(self):
        return [inp for inp in self.inputs if inp.input_method == "io_input"]
    
    @property
    def antecessors(self):
        l = self.parents
        parents = list(l)
        for p in parents:
            l += p.parents
            
        return l
    
    def parents(self):
        return [inp.to for inp in self.inputs 
            if inp.input_method == "io_input"]
        
    
    def _rec_graph(self, G, parents):
        for p in parents:
            G.add_node(p)
            G.add_edge(self, p)
            p._rec_graph(G, p.parents)
            
        
    def build_graph(self, ):
        G = networkx.Graph()
        G.add_node(self)
        self._rec_graph(G, self.parents)
        return G
        
    address = fields.StringField()
    executed = fields.BooleanField(default = False)
    log_output = fields.BooleanField(default = False)
    
    
    def bind_to_input(self, outputs, to, inputs):

        if to in self.antecessors:
            raise ValueError("Recursive binding is not allowed")
        
        for (outp, inp) in zip(outputs, inputs):
            if isinstance(outp, str):
                outp = self.outputdict[outp]
            if isinstance(inp, str):
                inp = to.inputdict[inp]
            inp.input_method = 'io_input'
            inp.to = to
                
    def bind_to_output(self, inputs, of , outputs):
        if self in of.antecessors:
            raise ValueError("Recursive binding is not allowed")
        
        for (outp, inp) in zip(outputs, inputs):
            if isinstance(outp, str):
                outp = of.outputdict[outp]
            if isinstance(inp, str):
                inp = self.inputdict[inp]
            inp.input_method = 'io_input'
            inp.to = of
            
        
        
    
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
        return results
    
        
    def __unicode__(self):
        return self.name
        
class IOSimple(IObject):
    
    def execute(self, **kwargs):
        results = {}
        keys = iter(kwargs)
        for out in self.outputs:
            results[out.name] = kwargs[ next(keys) ]
        
        return results
    
    
    


    

    
    
    

    
    
class IOGraph():
    pass

    
    