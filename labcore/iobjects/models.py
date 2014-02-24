# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""
#from __future__ import absolute_import

import itertools


import mongoengine as mg
import networkx
from mongoengine import fields

from IPython.utils.traitlets import Bool
from IPython.html import widgets
from IPython.display import display

from mongotraits import TraitDocument

mg.connect('labcore')


class Parameter(mg.EmbeddedDocument):
    meta = {'allow_inheritance': True}
    
    name = fields.StringField(required = True, max_length=256, unique=True)
    param_type = fields.StringField(default="STR")
    
    default = fields.DynamicField()
    value = fields.DynamicField()
    
        
    def __str__(self):
        return self.name
    def __unicode__(self):
        return self.name
        
                
INPUT_METHODS = ('constant', 'user_input', 'io_input')

class Input(Parameter):
    input_method = fields.StringField(choices=INPUT_METHODS, 
                                      default="user_input")

    input_display = fields.StringField()
    fr = fields.ReferenceField('IObject')
    fr_output = fields.EmbeddedDocumentField('Output')
    
    

OUTPUT_TYPES = ('display', 'hidden')
    
class Output(Parameter):
    
    output_type = fields.StringField(choices=OUTPUT_TYPES, 
                                      default="display")    
    is_connected = fields.BooleanField(default = False)                                  
    to = fields.ReferenceField('IObject')
    to_input = fields.EmbeddedDocumentField('Input')
    
    
class RunInfo(object):
    pass    

class IObject(TraitDocument):
    
    meta = {'allow_inheritance': True}
       
    name = fields.StringField(required = True, max_length=256)
    inputs = fields.ListField(mg.EmbeddedDocumentField(Input))
    outputs = fields.ListField(mg.EmbeddedDocumentField(Output))
    
    address = fields.StringField()
    executed = Bool(default_value = False, db=True)
    log_output = fields.BooleanField(default = False)
    #dispays = fields.ListField(mg.EmbeddedDocumentField(Parameter))
    
    def _paramdict(self, paramlist):
        return {param.name : param for param in paramlist}

    @property    
    def inputdict(self):
        return self._paramdict(self.inputs)
    
    @property    
    def outputdict(self):
        return self._paramdict(self.outputs)
    
    @property
    def links(self):
        return (inp for inp in self.inputs if inp.input_method == 'io_input')
    
    @property
    def free_inputs(self):
        return (inp for inp in self.inputs if inp.input_method=='user_input')
    

    @property
    def display_outputs(self):
        return (out for out in self.outputs if out.output_type == 'display')
   
    @property
    def antecessors(self):
        for a in self._antecessors(set()):
            yield a
                
    def _antecessors(self, existing):
        p_set = set(self.parents)
        
        new_antecessors = p_set-existing
        existing |= p_set

        for a in new_antecessors:
            yield a
        for a in new_antecessors:
            #yield a
            for na in a._antecessors(existing):
                yield na        
    
    @property
    def graph(self):
        #TODO: Cache?
        return self.build_graph()
        
    @property
    def parents(self):
        return {inp.fr for inp in self.inputs 
            if inp.input_method == "io_input"}
        
    
    def _rec_graph(self, G, links):
        for link in links:
            fr = link.fr
            G.add_node(fr)
            G.add_edge(fr, self, link=link, 
                       label = "%s->%s"%(link.name, link.fr_output)
            )
            fr._rec_graph(G, fr.links)
            
                    
    def build_graph(self, ):
        G = networkx.MultiDiGraph()
        G.add_node(self)
        self._rec_graph(G, self.links)
        return G
    
    def draw_graph(self):
        G = self.build_graph()
        networkx.draw(G)
    
    
    
    def bind_to_input(self, to, outputs, inputs):

        if to in self.antecessors:
            raise ValueError("Recursive binding is not allowed")
        
        for (outp, inp) in zip(outputs, inputs):
            if isinstance(outp, str):
                outp = self.outputdict[outp]
            if isinstance(inp, str):
                inp = to.inputdict[inp]
            inp.input_method = 'io_input'
            inp.fr = self
            outp.to = to
            inp.fr_output = outp
            outp.to_input = inp
            
                
    def bind_to_output(self, fr, inputs , outputs):
        if self in fr.antecessors:
            raise ValueError("Recursive binding is not allowed")
        
        for (outp, inp) in zip(outputs, inputs):
            if isinstance(outp, str):
                outp = fr.outputdict[outp]
            if isinstance(inp, str):
                inp = self.inputdict[inp]
            inp.input_method = 'io_input'
            inp.fr= fr
            inp.fr_output = outp
                
    
    def run(self):
        params = {}
        runinfo = RunInfo()
        
        for p in self.parents:
            if (not p.executed or 
                any(not ant.executed for ant in p.antecessors)):
                p.run()

        for inp in self.inputs:
            
            if inp.input_method == 'io_input':
                inp.value = inp.fr_output.value
            elif inp.input_method == 'user_input':
                inp.value = inp.widget.value
            params[inp.name] = inp.value
            
        try:
            results = self.execute(**params)
        except Exception as e:
            runinfo.success = False
            runinfo.error = e
        else:
            for out in self.outputs:
                last_value = out.value
                new_value = results[out.name]
                if last_value != new_value and out.is_connected:
                    out.to.executed = False
                out.value = new_value
                    
         
            self.executed = True
            
        return results
    
    def __str__(self):
        return self.name
        
    def __unicode__(self):
        return self.name
        
default_spec = ()

def add_child(container, child):
    container.children = container.children + [child]

    
class IPIObject(IObject):
    
    def _executed_changed(self):
        if self.executed:
            self.widget.add_class('executed')
        else:
            self.widget.remove_class('executed')
        
    def run(self):
        super(IPIObject,self).run()
        for out in self.display_outputs:
            out.widget.value = "<strong>%s</strong>: %r" %(out.name, out.value)
        
    
    def _add_classes(self, dic):
        for item in dic:
            item.add_class(dic[item])
    
    
    def make_control(self):
        control_container = widgets.ContainerWidget()
        
       
        css_classes = {control_container: 'control-container'}
        
        add_child(control_container, 
                  widgets.LatexWidget(value = "IObject Widget"))
                  
        
        for io in itertools.chain([self],self.antecessors):
        
            io._add_form(control_container, css_classes)
     
        
        display(control_container)
        self._add_classes(css_classes)
        self.control_container = control_container
        return control_container
        
    def _add_form(self, control_container, css_classes):
        iocont =  widgets.ContainerWidget()
        css_classes[iocont] = ('iobject-container')
        add_child(iocont, widgets.LatexWidget(value = self.name))
        add_child(control_container, iocont)
        self.widget = iocont
        for inp in self.free_inputs:
    
            w = widgets.TextWidget(description = inp.name, value = inp.value,
                                   default = inp.default)
            inp.widget = w
            
            def set_exec(w):
                self.executed = False
            w.on_trait_change(set_exec, name = 'value') 
            add_child(iocont,w)
        
        for out in self.display_outputs:
            w = widgets.HTMLWidget()
            out.widget = w
            add_child(iocont,w)
        
        button = widgets.ButtonWidget(description = "Execute %s" % self.name)
        
        def _run(b):
            self.run()
        button.on_click(_run)        
        add_child(iocont, button)
        
        
class IOSimple(IPIObject):
    
    def execute(self, **kwargs):
        results = {}
        keys = iter(kwargs)
        for out in self.outputs:
            results[out.name] = kwargs[ next(keys) ]
        
        return results

    
class IOGraph():
    pass

    
    