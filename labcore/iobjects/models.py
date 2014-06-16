# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:18:00 2014

@author: zah
"""
#from __future__ import absolute_import

import inspect
import weakref
import time

from IPython.utils.py3compat import string_types, PY3
from IPython.utils import traitlets
from IPython.utils.traitlets import (Bool, Any, Unicode, Enum, Instance, Int,
                                     )
from IPython.html import widgets
from IPython.display import display


from bson import objectid

import networkx


from labcore.mongotraits import (Document, EmbeddedDocument,
    EmbeddedReference, Reference, TList, Meta, ObjectIdTrait)

from labcore.widgets.widgetrepr import WidgetRepresentation

from labcore.iobjects.utils import (add_child, param_types,
                                     )
from labcore.iobjects import parallel_client


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
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(self.id)

    def repr_name(self):
        return self.name

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

class IObjectMeta(traitlets.MetaHasTraits):
    _ioclasses = weakref.WeakValueDictionary()
    def __init__(cls, name, bases, classdict):
        super().__init__(name, bases, classdict)
        cls._ioclasses[name] = cls

class IObjectBase(traitlets.HasTraits, metaclass = IObjectMeta):
    _reference = Unicode(widget = None)
    _iobjects = weakref.WeakValueDictionary()
    name = Unicode(order = -1)
    inputs = TList(Instance(Input))
    outputs = TList(Instance(Output))


    def declare_dict_ref(self, reference):
        self.__class__._iobjects[self.reference] = self

    @classmethod
    def load_dict_ref(cls, ref):
        return cls._iobjects[ref]

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
    class WidgetRepresentation(WidgetRepresentation):
        varname_map = 'name'

default_spec = ()

class IObject(IObjectBase):
    def __init__(self, function, *args, **kwargs):
        super().__init__(*args, **kwargs)
        reference = self._get_function_path(function)
        self.function = function
        self.reference = reference
        self.declare_dict_ref(reference)


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


class DocumentIObjectMeta(Meta, IObjectMeta):
    pass
class DocumentIObject(Document, IObjectBase, metaclass = DocumentIObjectMeta):

    def __init__(self, *args, **kwargs):
       super.__init__(*args, **kwargs)
       self.reference = str(self.id)

    @classmethod
    def load_dict_ref(cls, ref):
        return cls.load_ref(objectid.ObjectId(ref))


class Link(EmbeddedDocument):
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

    def __str__(self):
        return "{0.fr_output} -> {0.to_input}".format(self)

class MirrorMixin(traitlets.HasTraits):
    mirror_id = ObjectIdTrait(allow_none = False)
    def __hash__(self):
        return hash(self.mirror_id)

class OutputMirror(MirrorMixin, Output):
    pass
class InputMirror(MirrorMixin, Input):
    pass

class IONode(Document):
    def __init__(self, iobject = None, **kwargs):
        super(IONode, self).__init__(**kwargs)
        if iobject is not None:
            self.iobject = iobject

        if not self.name:
            self.name = self.iobject.name

        obj_outs = set(self.iobject.outputs)
        obj_ins = set(self.iobject.inputs)
        my_outs = set(self.outputs)
        my_ins = set(self.inputs)

        new_outs = obj_outs - my_outs
        new_ins = obj_ins - my_ins
        for out in new_outs:
            vals = dict(out._trait_values)
            mirror_id = vals.pop('_id')
            myout = OutputMirror(mirror_id = mirror_id,  **vals)
            self.outputs = self.outputs + (myout,)

        for inp in new_ins:
            vals = dict(inp._trait_values)
            mirror_id = vals.pop('_id')
            myinp = InputMirror(mirror_id = mirror_id, **vals)
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
    _iobject = Instance(IObject, db=False, widget = None)
    _iobject_key = Unicode(widget = None)
    _iobject_class = Unicode(widget = None)


    name = Unicode()

    inputs = TList(Instance(InputMirror))
    outputs = TList(Instance(OutputMirror))

    inlinks = TList(Instance(Link))
    outlinks = TList(Instance(Link))

    executed = Bool(widget = None)
    pending = Bool(widget = None)
    failed = Bool(widget = None)
    has_widget = Bool(default_value = False, db = False, widget = None)

    runaddress = Enum(values = parallel_client.client_map.keys(),
                      default_value = 'local', allow_none = False)

    _async_results = None
    _results = None

    @property
    def iobject(self):
        if not self._iobject:
            try:
                iobject_class = IObjectMeta._ioclasses[self._iobject_class]
                self._iobject = iobject_class.load_dict_ref(self._iobject_key)
            except KeyError:
                raise IObjectError("IONodes must have a valid iobject.")
        return self._iobject

    @iobject.setter
    def iobject(self, iobject):
        self._iobject = iobject
        self._iobject_class = iobject.__class__.__name__
        self._iobject_key = iobject.reference


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
            self._toggle_executed()

        if not self.executed:
            self._async_results = None
            self._results = None
            for child in self.children:
                child.executed = False

    def _pending_changed(self):

        if self.has_widget:
            self._toggle_pending()

    def _toggle_executed(self):
        if self.executed:
            self.widget.add_class('executed')
        else:
            self.widget.remove_class('executed')

    def _toggle_pending(self):
        if self.pending:
            self.widget.add_class('pending')
            self.widget.button.disabled = True
        else:
            self.widget.remove_class('pending')
            self.widget.button.disabled = False
    
    def _runnode(self, deps, **params):
       
        if parallel_client.client:
            targets = parallel_client.targets(self.runaddress)
            v = parallel_client.view
            with v.temp_flags(targets = targets, after = deps, block = False):
                async_results = v.apply_async(self.iobject.__call__, **params)
        return async_results


    def run(self, **kwargs):
        params = dict(kwargs)
        
        deps = []

        for inlink in self.inlinks:
            if inlink.fr_output.name in kwargs:
                continue
            p = inlink.fr
            if (not p.executed or
                any(not ant.executed for ant in p.ancestors)):
                
                deps.append(p.run())
                

        for inp in self.inputs:
            if inp.name in kwargs:
                continue
            params[inp.name] = inp.value
        async_results = self._runnode(deps, **params)
        self.pending = True
        return async_results
       

        return async_results
    
    def on_result(self, results):
        self.pending = False
        self.executed = True
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
    
    def run_sync(self, **kwargs):
        async_results = self.run(**kwargs)
        results = async_results.get()
        self.on_result(results)
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
            w.traits()['value'].allow_none = True
            traitlets.link((inp,'value'),(w,'value'))

            def set_exec(_w):
                self.executed = False
            w.on_trait_change(set_exec, name = 'value')
            add_child(iocont,w)

        for out in self.free_outputs:
            w = widgets.HTMLWidget()
            out.widget = w
            add_child(iocont,w)
            w.traits()['value'].allow_none = True
            traitlets.link((out,'value'),(w,'value'))

        button = widgets.ButtonWidget(description = "Execute %s" % self.name)
        def _run(b):
            self.executed = False
            self.run_sync()
        button.on_click(_run)
        add_child(iocont, button)

        self.widget = iocont
        self.widget.button = button
        self.has_widget = True
        self._toggle_executed()
        return iocont

    def repr_name(self):
        return self.name
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.name


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
        if not fr in self.nodes:
            self.nodes = self.nodes + (fr,)
        if not to in self.nodes:
            self.nodes = self.nodes + (to,)
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



    def build_graph(self):
        G = networkx.MultiDiGraph()
        G.add_nodes_from(self.nodes)
        for node in self.nodes:
            G.add_edges_from((link.fr, node, {'label':str(link)})
                    for link in node.inlinks)
            class _N():
                def __init__(self, n):
                    self.str = str(n)
                def __str__(self):
                    return self.str
            inps = [_N(inp) for inp in node.free_inputs]
            G.add_nodes_from(inps)
            G.add_edges_from(((inp, node, {'label':''})
            for inp in inps))

        return G

    @property
    def graph(self):
        #TODO: Cache?
        return self.build_graph()

    def draw_graph(self):
        G = self.build_graph()
        pos = networkx.spring_layout(G)

        nodelist = [node for node in G.nodes() if isinstance(node, IONode)]

        networkx.draw(G, pos,  node_size =  1700, nodelist = nodelist)
        edge_labels = {(edge[0], edge[1]):edge[2]['label'] for edge in G.edges_iter(data = True)}
        networkx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    def make_control(self):
        control_container = widgets.ContainerWidget()
        run_all_btn = widgets.ButtonWidget(description = "Run all")
        def _ra(btn):
            result = self.run_all()
            display(result)
        run_all_btn.on_click(_ra)
        add_child(control_container, widgets.HTMLWidget(
                    value="<h2>%s</h2>"%self.name))
        add_child(control_container, run_all_btn)
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
        async_results = {}
        results = {}
        for node in self.sorted_iterate():
            if not node.executed:
                async_results[node] = node.run()
            else:
                results[node] = node._results

        while async_results:
            delnodes = []
            for (node, async_result) in async_results.items():
                if async_result.ready():
                    r = async_result.result
                    results[node] = r
                    node.on_result(r)
                    delnodes.append(node)
            time.sleep(0.3)
            for node in delnodes:
                del async_results[node]

        return results

    def save_all(self):
        self.save(cascade=True)


