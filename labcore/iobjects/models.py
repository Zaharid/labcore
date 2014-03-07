# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""
#from __future__ import absolute_import

import itertools
import copy

import mongoengine as mg
import networkx
from mongoengine import fields

from IPython.utils.py3compat import string_types
from IPython.utils.traitlets import Bool, Any
from IPython.html import widgets
from IPython.display import display

from labcore.iobjects.utils import (add_child, widget_mapping, param_types,
                                     )
from labcore.iobjects.mongotraits import (Document, EmbeddedDocument,
    EmbeddedReferenceField)




class Parameter(EmbeddedDocument):

    meta = {'abstract':True}

    eid = fields.ObjectIdField()

    name = fields.StringField(required = True, max_length=256, unique=True)
    param_type = fields.StringField(default="String", choices = param_types)

    default = fields.DynamicField()
    value = Any(db = True)

    def __eq__(self, other):
        return self.eid == other.eid

    def __hash__(self):
        return hash(self.eid)

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

class IObject(Document):

    meta = {'allow_inheritance': True}

    name = fields.StringField(required = True, max_length=256)
    inputs = fields.ListField(mg.EmbeddedDocumentField(Input))
    outputs = fields.ListField(mg.EmbeddedDocumentField(Output))

    address = fields.StringField()
    #executed = Bool(default_value = False, db=True)
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
    def display_outputs(self):
        return (out for out in self.outputs if out.output_type == 'display')




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




    def __str__(self):
        return self.name

    def __unicode__(self):
        if not self.name:
            raise AttributeError("Name not provided")
        return self.name

default_spec = ()


class Link(EmbeddedDocument):

#==============================================================================
#     def __init__(self, *args, **kwargs):
#         super(Link, self).__init__(*args, **kwargs)
#         if not all((self.to_output,self.fr,self.fr_input, self.to)):
#             raise TypeError("All parameters of a link must be specified.")
#==============================================================================

    eid = fields.ObjectIdField()

    to = fields.ReferenceField('IONode')
    fr_output = EmbeddedReferenceField('IONode', 'outputs')
    fr = fields.ReferenceField('IONode')
    to_input = EmbeddedReferenceField('IONode', 'inputs')

    def __eq__(self, other):
        return (self.to_output == other.to_output and self.fr == other.fr and
            self.fr_input == other.fr_input and self.to == other.to)
    def __hash__(self):
        a = hash(self.to_output)
        b = hash(self.to)
        c = hash(self.fr_input)
        d = hash(self.fr)
        return a^b^c^d

    def __unicode__(self):
        return "{0.fr}:{0.fr_input}->{0.to}:{0.to_output}".format(self)



class IONode(Document):
    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], IObject):
            kwargs['iobject'] = args[0]
            args = args[1:]
        super(IONode, self).__init__(*args,**kwargs)
        if not self.iobject:
            raise TypeError("An IObject is needed to initialize a node.")

        obj_outs = set(self.iobject.outputs)
        obj_ins = set(self.iobject.inputs)
        my_outs = set(self.outputs)
        my_ins = set(self.inputs)

        new_outs = obj_outs - my_outs
        new_ins = obj_ins - my_ins
        for out in new_outs:
            self.outputs.append(copy.copy(out))
        for inp in new_ins:
            self.inputs.append(copy.copy(inp))

        dead_outs = my_outs - obj_outs
        dead_ins = my_ins - obj_ins
        for out in dead_outs:
            self.outputs.remove(out)
        for inp in dead_ins:
            self.inputs.remove(inp)

    #id = fields.ObjectIdField()
    iobject = fields.ReferenceField(IObject, required = True)

    inputs = fields.ListField(fields.EmbeddedDocumentField(Input))
    outputs = fields.ListField(fields.EmbeddedDocumentField(Output))

    inlinks = fields.ListField(fields.EmbeddedDocumentField(Link))
    outlinks = fields.ListField(fields.EmbeddedDocumentField(Link))

    gui_order = fields.IntField()
    executed = Bool(db = True)
    failed = Bool(db = True)

    def _paramdict(self, paramlist):
        return {param.name : param for param in paramlist}

    @property
    def inputdict(self):
        return self._paramdict(self.inputs)

    @property
    def outputdict(self):
        return self._paramdict(self.outputs)

    @property
    def parents(self):
        return (link.fr for link in self.inlinks)

    @property
    def children(self):
        return (link.to for link in self.outlinks)

    @property
    def descendants(self):
         """Return ancestors in order (closest first)."""
         for a in self._related(set(), 'children'):
             yield a

    @property
    def ancestors(self):
        """Return ancestors in order (closest first)."""
        for a in self._related(set(), 'parents'):
            yield a

    def _related(self, existing, what):
        p_set = set(getattr(self, what))

        new_related = p_set-existing
        existing |= p_set

        for a in new_related:
            yield a
        for a in new_related:
            for na in a._related(existing, what):
                yield na
    @property
    def linked_inputs(self):
        for link in self.inlinks:
            yield link.fr_input

    @property
    def linked_outputs(self):
        for link in self.outlinks:
            yield link.to_output

    @property
    def free_inputs(self):
        fis = set(self.inputs) - set(self.linked_inputs)
        for fi in fis:
            yield fi

    @property
    def free_outputs(self):
        fos = set(self.outputs) - set(self.linked_outputs)
        for fo in fos:
            yield fo

    def _executed_changed(self):
        if self.executed:
            self.widget.add_class('executed')
        else:
            self.widget.remove_class('executed')
            for child in self.children:
                child.executed = False


    def run(self, **kwargs):
        params = dict(kwargs)
        runinfo = RunInfo()

        for inlink in self.inlinks:
            if inlink.fr_input.name in kwargs:
                continue
            p = inlink.fr
            if (not p.executed or
                any(not ant.executed for ant in p.antecessors)):

                p.run()

        for inp in self.inputs:
            if inp.name in kwargs:
                continue
            elif inp.input_method == 'user_input':
                inp.value = inp.widget.value
            params[inp.name] = inp.value
        try:
            results = self.iobject.execute(**params)
        except Exception as e:
            runinfo.success = False
            runinfo.error = e
            self.executed = False
            self.failed = True
        else:
            for out in self.outputs:
                last_value = out.value
                new_value = results[out.name]
                if last_value != new_value and out.is_connected:
                    out.to.executed = False
                out.value = new_value

            self.executed = True

        return results

    def make_form(self, css_classes):
        iocont =  widgets.ContainerWidget()
        css_classes[iocont] = ('iobject-container')
        add_child(iocont, widgets.LatexWidget(value = self.name))
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

    def __eq__(self, other):
        return self.id == other.id

#==============================================================================
#     def __getattribute__(self, attr):
#         try:
#             return object.__getattribute__(self, attr)
#         except AttributeError:
#             return getattr(self.iobject, attr)
#==============================================================================

    def __unicode__(self):
        return self.iobject.name
    def __str__(self):
        return self.iobject.name


class IOGraph(Document):

    def __init__(self, *args, **kwargs):
        super(IOGraph, self).__init__(*args, **kwargs)

        for link in self.links:
            if self._link_valid(link):
                self._init_link(link)
            else:
                self.remove_link(link)


    name = fields.StringField()
    nodes = fields.ListField(fields.ReferenceField(IONode))

    @property
    def links(self):
        for node in self.nodes:
            for link in node.inlinks:
                yield link

    def build_graph(self):
        G = networkx.MultiDiGraph()
        G.add_nodes_from(self.nodes)
        for node in self.nodes:
            G.add_edges_from((link.fr, node, {'link':link}) for link in node.inlinks)
        return G

    @property
    def graph(self):
        #TODO: Cache?
        return self.build_graph()

    def _link_valid(self, link):
        return (link.to in self.nodes and link.fr in self.nodes and
            link.to_output in link.to.outputs and
            link.fr_input in link.fr.inputs)

    def _init_link(self, link):
        inp = link.fr_input
        out = link.to_output
        def set_output(o, value):
            inp.value = value

        out.on_trait_change(set_output, name = 'value')
        out.handler = set_output


    def bind(self, fr, out, to, inp):
        if to in fr.ancestors or to is fr:
            raise ValueError("Recursive binding is not allowed.")
        if not fr in self.nodes or not to in self.nodes:
            raise ValueError('Nodes must be in graph nodes before linking.')
        if isinstance(inp, string_types):
            inp = to.inputdict[inp]
        if isinstance(out, string_types):
            out = to.outputdict[out]

        link = Link(to_output = out, fr = fr, fr_input = inp, to=to)

        #Do this way to trigger _changed_fields-
        to.inlinks = to.inlinks + [link]
        fr.outlinks = fr.outlinks + [link]

        self._init_link(link)

    def unbind(self, fr, out, to, inp):
        if isinstance(inp, string_types):
            inp = to.inputdict[inp]
        if isinstance(out, string_types):
            out = to.outputdict[out]
        link = Link(to = to, to_output = out, fr = fr, fr_input = inp)
        self.remove_link(link)

    def remove_link(self, link):
        to = link.to
        fr = link.fr
        out = link.to_output
        out.on_trait_change(out.handler, name = 'value', remove = True)
        to.inlinks.remove(link)
        to.inlinks = list(to.inlinks)
        fr.outlinks.remove(link)
        fr.outlinks = list(fr.outlinks)

    def draw_graph(self):
        G = self.build_graph()
        networkx.draw(G)

    def make_control(self):
        control_container = widgets.ContainerWidget()
        css_classes = {control_container: 'control-container'}
        for node in self.sorted_iterate():
            add_child(control_container, node.make_form(css_classes))

    def sorted_iterate(self):
        #TODO Improve this
        return iter(self.nodes)


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
