# -*- coding: utf-8 -*-
"""
Created on Mon Mar  3 20:12:50 2014

@author: zah
"""
import inspect
from collections import defaultdict

from IPython.utils import traitlets
from IPython.html import widgets

def add_to_list(l, elem):
    """Add an element to a list changing the id and refreshing it"""
    l = l + [elem]

def remove_from_list(l, elem):
    """Delete an element from a list changing the id and refreshing it"""
    l.remove(elem)
    l = list(l)

def add_child(container, child):
    container.children = container.children + (child,)


class EvaluableWidget(widgets.TextWidget):

    def __setattribute__(self, attr, value):

        super(EvaluableWidget, self).__setattribute__(attr, value)
        if attr == 'value':
            self.context = inspect.stack[1][0].f_locals

    def __getattribute__(self, attr):

        value = super(EvaluableWidget, self).__getattribute__(attr)
        if attr == 'value':
            value = eval(value, globals(), self.context)



widget_mapping = defaultdict(lambda: widgets.TextWidget, {
    'String': widgets.TextWidget,
    'Boolean': widgets.CheckboxWidget,
    'Integer': widgets.IntTextWidget,
    'Double': widgets.FloatTextWidget,
    'Object': EvaluableWidget,

})

param_types = widget_mapping.keys()