# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""

import mongoengine as mg
import networkx
from mongoengine import fields

from IPython.html import widgets
from IPython.display import display

mg.connect('labcore')



class Parameter(mg.EmbeddedDocument):
    meta = {'allow_inheritance': True}
    
    name = fields.StringField(required = True, max_length=256, unique=True)
    param_type = fields.StringField(default="STR")
    
    default = fields.DynamicField()
    value = fields.DynamicField()
    
        
    def __unicode__(self):
        return self.name
        
        
        
INPUT_METHODS = ('constant', 'user_input', 'io_input')
class Input(Parameter):
    input_method = fields.StringField(choices=INPUT_METHODS, 
                                      default="user_input")

    input_display = fields.StringField()
    fr = fields.ReferenceField('IObject')
    fr_output = fields.StringField()
    

OUTPUT_TYPES = ('display', 'hidden')
    
class Output(Parameter):
    
    input_method = fields.StringField(choices=OUTPUT_TYPES, 
                                      default="display")
    to = fields.ReferenceField('IObject')
    

    




    

class IObject(mg.Document):

    
    meta = {'allow_inheritance': True}
    
    
    name = fields.StringField(required = True, max_length=256)
    inputs = fields.ListField(mg.EmbeddedDocumentField(Input))
    outputs = fields.ListField(mg.EmbeddedDocumentField(Output))
    #dispays = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    
    def _paramdict(self, paramlist):
        return {param.name : param for param in paramlist}

    @property    
    def inputdict(self):
        return self._paramdict(self.inputs)
    
    @property
    def displaydict(self):
        return self._paramdict(self.displays)
    
    @property    
    def outputdict(self):
        return self._paramdict(self.outputs)
    
    @property
    def links(self):
        return (inp for inp in self.inputs if inp.input_method == "io_input")
    
    @property
    def free_inputs(self):
        return (inp for inp in self.inputs if inp.input_method=='user_input')
    
    
    @property
    def antecessors(self):
        l = self.parents
        parents = list(l)
        for p in parents:
            l += p.parents
            
        return l
        
    @property
    def parents(self):
        return {inp.fr for inp in self.inputs 
            if inp.input_method == "io_input"}
        
    
    def _rec_graph(self, G, links):
        for link in links:
            fr = link.fr
            G.add_node(fr)
            G.add_edge(self, fr, link=link, 
                       label = "%s->%s"%(link.name, link.fr_output)
            )
            fr._rec_graph(G, fr.links)
            
            
        
    def build_graph(self, ):
        G = networkx.MultiDiGraph()
        G.add_node(self)
        self._rec_graph(G, self.links)
        return G
    
    def build_form(self):
        pass
        
    address = fields.StringField()
    executed = fields.BooleanField(default = False)
    log_output = fields.BooleanField(default = False)
    
    
    def bind_to_input(self, fr, outputs, inputs):

        if fr in self.antecessors:
            raise ValueError("Recursive binding is not allowed")
        
        for (outp, inp) in zip(outputs, inputs):
            if isinstance(outp, str):
                outp = self.outputdict[outp]
            if isinstance(inp, str):
                inp = fr.inputdict[inp]
            inp.input_method = 'io_input'
            inp.fr = self
            inp.fr_output = outp.name
                
    def bind_to_output(self, to, inputs , outputs):
        if self in to.antecessors:
            raise ValueError("Recursive binding is not allowed")
        
        for (outp, inp) in zip(outputs, inputs):
            if isinstance(outp, str):
                outp = to.outputdict[outp]
            if isinstance(inp, str):
                inp = self.inputdict[inp]
            inp.input_method = 'io_input'
            inp.fr= to
            inp.fr_output = outp.name
            
        
        
    
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
        

    
    

default_spec = ()
    
class IPIObject(IObject):
    
    def _add_classes(self, dic):
        for item in dic:
            item.add_class(dic[item])
    
    def make_control(self):
        control_container = widgets.ContainerWidget()
        display(control_container)
       
        dic = {control_container: 'control-container'}
        self._rec_form(control_container, dic)
        
        
        control_container.children =(control_container.children + [widgets.LatexWidget(value = "IObject Widget")])
        
        
        self._add_classes(dic)
        return control_container
    
    def _rec_form(self, control_container, dic):
        iocont =  widgets.ContainerWidget()
        dic[iocont] = ('iobject-container')
        iocont.children = iocont.children + [widgets.LatexWidget(value = self.name)]
        control_container.children = control_container.children + [iocont]
        for inp in self.free_inputs:
            w = widgets.TextWidget(description = inp.name)
            iocont.children = iocont.children + [w]
        
        button = widgets.ButtonWidget(description = "Execute %s" % self.name)        
        iocont.children = iocont.children + [button]
        
        for p in self.parents:
            p._rec_form(control_container, dic)

class IOSimple(IPIObject):
    
    def execute(self, **kwargs):
        results = {}
        keys = iter(kwargs)
        for out in self.outputs:
            results[out.name] = kwargs[ next(keys) ]
        
        return results
            
            
        

    

    
    
    

    
    
class IOGraph():
    pass

    
    