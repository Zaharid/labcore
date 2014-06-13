# -*- coding: utf-8 -*-
"""
Created on Sun Jun  1 21:34:35 2014

@author: zah
"""
from IPython.utils.html import widgets

def command_widget(commands):
    cont = widgets.ContainerWidget(description = "Commands")
    children = []
    for command in commands:
        w = widgets.S
        children.append()