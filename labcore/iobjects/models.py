# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""
#from __future__ import absolute_import

import inspect
import weakref

from IPython.utils.py3compat import string_types, PY3
from IPython.utils import traitlets
from IPython.utils.traitlets import (Bool, Any, Unicode, Enum, Instance, Int,
                                     )
from IPython.html import widgets
from IPython.display import display

import networkx

from labcore.iobjects.utils import (add_child, widget_mapping, param_types,
                                     )
from labcore.mongotraits import (Document, EmbeddedDocument,
    EmbeddedReference, Reference, TList)


class IObjectError(Exception):
    pass



class Parameter(EmbeddedDocument):

    name = Unicode()
    param_type = Enum(default_value="String", values = param_types)

    default = Any()
    value = Any(db = False)
    description = Unicode()
    #parent_ref = ObjectIdTrait(allow_none = True)
    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.name
    def __unicode__(self):
        return self.name

INPUT_METHODS = ('constant', 'user_input', 'io_input')

class Input(Parameter):
    input_method = Enum(default_value="user_input",values=INPUT_METHODS)

OUTPUT_TYPES = ('display', 'hidden')

class Output(Parameter):

    output_type = Enum(default_value="display",values=OUTPUT_TYPES)


class RunInfo(object):
    pass

class IObjectBase(traitlets.HasTraits):
    name = Unicode()
    inputs = TList(Instance(Input))
    outputs = TList(Instance(Output))

    #executed = Bool(default_value = False, db=True)
    log_output = Bool(default_value = False)
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

    def __str__(self):
        return self.name

    def __unicode__(self):
        if not self.name:
            raise AttributeError("Name not provided")
        return self.name

default_spec = ()

class IObject(IObjectBase):
    function_path = Unicode()
    _simple_output = Bool(default_value = False)
    _iobjects = weakref.WeakValueDictionary()
    def __init__(self, function, *args, **kwargs):
        super(IObject,self).__init__(*args,**kwargs)
        self.function = function
        self.function_path = self._get_function_path(function)
        self.__class__._iobjects[self.function_path] = self


    @staticmethod
    def _get_function_path(function):
        mod = inspect.getmodule(function)
        modname = mod.__name__ + '.' if mod is not None else ''
        function_path = "%s%s"%(modname, function.__qualname__)
        return function_path


    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def __doc__(self):
        doc = super(IObject, self).__doc__()
        doc += ("\nThe documentation for the original function is:\n"+
        self.function.__doc__())


if PY3:
    def _map_param(param, cls):
        FParam = inspect.Parameter
        bad_kinds = (FParam.VAR_KEYWORD, FParam.VAR_POSITIONAL)
        if param.kind in bad_kinds:
            raise IObjectError("IObjects cannot have variable arguments"\
            " as inputs.")
        if param.annotation is not FParam.empty:
            param_type = param.annotation
        else:
            param_type = 'String'
        if param.default is not FParam.empty:
            default = param.default
        else:
            default = None
        return cls(name = param.name, param_type=param_type, default=default)

    def _map_output(output):
        if not (isinstance(output,tuple) and len(output)==2):
            raise ValueError("Return annotation must be of the form"\
            "('name',type) or a list of such values")
        name, param_type = output
        param_type = str(param_type)
        return Output(name = name, param_type=param_type)

    def iobject(f, signature = None, *args, **kwargs):

        if signature is None:
            signature = inspect.signature(f)
        inputs = [_map_param(param, Input)
            for param in signature.parameters.values()]

        ret = signature.return_annotation
        if ret is not inspect._empty:
            _simple_output = False
            if isinstance(ret, list):
                outputs = [_map_output(output) for output in ret]
            else:
                outputs = [_map_output(ret)]
        else:
            outputs = [Output(name="output")]
            _simple_output = True
        return IObject(function = f, name = f.__name__, inputs = inputs,
                       outputs=outputs,
                       _simple_output = _simple_output)



class Link(EmbeddedDocument):

#==============================================================================
#     def __init__(self, *args, **kwargs):
#         super(Link, self).__init__(*args, **kwargs)
#         if not all((self.to_input,self.fr,self.fr_output, self.to)):
#             raise TypeError("All parameters of a link must be specified.")
#==============================================================================

    to = Reference(__name__+'.IONode')
    fr_output = EmbeddedReference(Output, document = __name__+'.IONode',
                                  trait_name='outputs')
    fr = Reference(__name__+'.IONode')
    to_input = EmbeddedReference(Input, __name__+'.IONode', 'inputs')

    def __eq__(self, other):
        return (self.to_input == other.to_input and self.fr == other.fr and
            self.fr_output == other.fr_output and self.to == other.to)
    def __hash__(self):
        a = hash(self.to_input)
        b = hash(self.to)
        c = hash(self.fr_output)
        d = hash(self.fr)
        return a^b^c^d

    def __unicode__(self):
        return "{0.fr}:{0.fr_output}->{0.to}:{0.to_input}".format(self)

class OutputMirror(Output):
    pass
class InputMirror(Input):
    pass

class IONode(Document):
    def __init__(self, iobject = None, **kwargs):
        super(IONode, self).__init__(**kwargs)
        if iobject is not None:
            self.iobject = iobject
        else:
            try:
                self.iobject = IObject._iobjects[self._iobject_key]
            except KeyError:
                raise IObjectError("IONodes must have a valid iobject.")

        if not self.name:
            self.name = self.iobject.name

        obj_outs = set(self.iobject.outputs)
        obj_ins = set(self.iobject.inputs)
        my_outs = set(self.outputs)
        my_ins = set(self.inputs)

        new_outs = obj_outs - my_outs
        new_ins = obj_ins - my_ins
        for out in new_outs:
            myout = OutputMirror(**out._trait_values)
            self.outputs = self.outputs + (myout,)

        for inp in new_ins:
            myinp = InputMirror(**inp._trait_values)
            self.inputs = self.inputs + (myinp,)

        obj_outs = set(self.iobject.outputs)
        obj_ins = set(self.iobject.inputs)
        my_outs = set(self.outputs)
        my_ins = set(self.inputs)

        dead_outs = my_outs - obj_outs
        dead_ins = my_ins - obj_ins
        for out in dead_outs:
            newouts = list(self.outputs)
            newouts.remove(out)
            self.outputs = newouts
        for inp in dead_ins:
            newins = list(self.inputs)
            newins.remove(inp)
            self.inputs = newins

    #id = fields.ObjectIdField()
    _iobject = Instance(IObject, db=False)
    _iobject_key = Unicode()

    @property
    def iobject(self):
        if not self._iobject:
            self._iobject = IObject._iobjects[self._iobject_key]
        return self._iobject

    @iobject.setter
    def iobject(self, obj):
        self._iobject = obj
        self._iobject_key = obj.function_path
    name = Unicode()

    inputs = TList(Instance(InputMirror))
    outputs = TList(Instance(OutputMirror))

    inlinks = TList(Instance(Link))
    outlinks = TList(Instance(Link))

    gui_order = Int()
    executed = Bool()
    failed = Bool()
    has_widget = Bool(default_value = False, db = False)

    def FParamdict(self, paramlist):
        return {param.name : param for param in paramlist}

    @property
    def inputdict(self):
        return self.FParamdict(self.inputs)

    @property
    def outputdict(self):
        return self.FParamdict(self.outputs)

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
    def input_mapping(self):
        return {link.to_input:link for link in self.inlinks}

    @property
    def output_mapping(self):
        return {link.fr_output:link for link in self.outlinks}

    @property
    def linked_inputs(self):
        for link in self.inlinks:
            yield link.to_input

    @property
    def linked_outputs(self):
        for link in self.outlinks:
            yield link.fr_output

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
        if self.has_widget:
            self._toggle_widget()

        if not self.executed:
            for child in self.children:
                child.executed = False

    def _toggle_widget(self):
        if self.executed:
            self.widget.add_class('executed')
        else:
            self.widget.remove_class('executed')


    def run(self, **kwargs):
        params = dict(kwargs)
        runinfo = RunInfo()

        for inlink in self.inlinks:
            if inlink.fr_output.name in kwargs:
                continue
            p = inlink.fr
            if (not p.executed or
                any(not ant.executed for ant in p.ancestors)):
                p.run()

        for inp in self.inputs:
            if inp.name in kwargs:
                continue
            params[inp.name] = inp.value
        try:
            results = self.iobject.__call__(**params)


        except Exception as e:
            runinfo.success = False
            runinfo.error = e
            self.executed = False
            self.failed = True

        else:
            if self.iobject._simple_output:
                results = {self.iobject.outputs[0].name :  results}
            for out in self.outputs:
                last_value = out.value
                new_value = results[out.name]
                if last_value != new_value and out in self.output_mapping:
                     self.output_mapping[out].to.executed = False
                out.value = new_value

            for inp in self.inputs:
                inp.default = inp.value

            self.executed = True

        return results

    def make_form(self, css_classes):
        iocont =  widgets.ContainerWidget()
        css_classes[iocont] = ('iobject-container')
        add_child(iocont, widgets.HTMLWidget(value = "<h3>%s</h3>"%self.name))
        for inp in self.free_inputs:
            #We have to filter none kw...
            allkw = dict(description = inp.name, value = inp.value,
                       default = inp.default)
            kw = {key:value for (key,value) in allkw.items()
                    if value is not None}
            w = widgets.TextWidget(**kw)
            inp.widget = w
            w.traits()['value']._allow_none = True
            traitlets.link((inp,'value'),(w,'value'))

            def set_exec(_w):
                self.executed = False
            w.on_trait_change(set_exec, name = 'value')
            add_child(iocont,w)

        for out in self.free_outputs:
            w = widgets.HTMLWidget()
            out.widget = w
            add_child(iocont,w)
            w.traits()['value']._allow_none = True
            traitlets.link((out,'value'),(w,'value'))

        button = widgets.ButtonWidget(description = "Execute %s" % self.name)
        def _run(b):
            self.run()
        button.on_click(_run)
        add_child(iocont, button)

        self.widget = iocont
        self.has_widget = True
        self._toggle_widget()
        return iocont

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

    name = Unicode()
    nodes = TList(Reference(IONode))

    @property
    def links(self):
        for node in self.nodes:
            for link in node.inlinks:
                yield link

    def build_graph(self):
        G = networkx.MultiDiGraph()
        G.add_nodes_from(self.nodes)
        for node in self.nodes:
            G.add_edges_from((link.fr, node, {'link':link})
                    for link in node.inlinks)
        return G

    @property
    def graph(self):
        #TODO: Cache?
        return self.build_graph()

    def _link_valid(self, link):
        return (link.to in self.nodes and link.fr in self.nodes and
            link.fr_output in link.fr.outputs and
            link.to_input in link.to.inputs)

    def _init_link(self, link):
        inp = link.to_input
        out = link.fr_output
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
            out = fr.outputdict[out]

        link = Link(to_input = inp, fr = fr, fr_output = out, to=to)

        #Do this way to trigger _changed_fields-
        to.inlinks = to.inlinks + (link,)
        fr.outlinks = fr.outlinks + (link,)

        self._init_link(link)

    def unbind(self, fr, out, to, inp):
        if isinstance(inp, string_types):
            inp = to.inputdict[inp]
        if isinstance(out, string_types):
            out = fr.outputdict[out]
        link = Link(to = to, to_input = inp, fr = fr, fr_output = out)
        self.remove_link(link)

    def remove_link(self, link):
        to = link.to
        fr = link.fr
        out = link.fr_output
        if hasattr(out, 'handler'):
            out.on_trait_change(out.handler, name = 'value', remove = True)
        l = list(to.inlinks)
        l.remove(link)
        to.inlinks = l
        l = list(fr.outlinks)
        l.remove(link)
        fr.outlinks = l

    def draw_graph(self):
        G = self.build_graph()
        networkx.draw(G)

    def make_control(self):
        control_container = widgets.ContainerWidget()
        add_child(control_container, widgets.HTMLWidget(
                    value="<h2>%s</h2>"%self.name))
        css_classes = {control_container: 'control-container'}
        for node in self.sorted_iterate():
            add_child(control_container, node.make_form(css_classes))
        display(control_container)
        for (widget, klass) in css_classes.items():
            if isinstance(widget, widgets.ContainerWidget):
                widget.remove_class("vbox")
            widget.add_class(klass)

    def sorted_iterate(self):
        #TODO Improve this
        return iter(self.nodes)

    def run_all(self):
        result = {}
        for node in self.sorted_iterate:
            if not node.executed:
                result[node] = node.run()
        return result

    def save_all(self):
        self.save(cascade=True)

class IOSimple(IObject):

    def __init__(self, *args,**kwargs):
        super(IOSimple, self).__init__(function = self.f, **kwargs)

    @staticmethod
    def f(**kwargs):
        results = {}
        keys = iter(kwargs)
        for out in self.outputs:
            results[out.name] = kwargs[ next(keys) ]

        return results
