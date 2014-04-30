# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 19:34:49 2014

@author: zah
"""
from __future__ import print_function

import os
import sys
import shutil
import codecs
import datetime
import webbrowser

import sympy

from jinja2 import Environment, PackageLoader
from IPython.utils import traitlets

from labcore.mongotraits import documents
#from labcore.reporttools import htmlf

env = Environment(loader = PackageLoader(__name__, 'templates'))

STATIC = os.path.join(os.path.dirname(__file__), 'static')

class Result(documents.Document):

    title = traitlets.Unicode()
    smalltitle = traitlets.Unicode()

    value = traitlets.Any()
    date = traitlets.Instance(datetime.datetime)

    def __init__(self, *args, **kwargs):
        super(Result, self).__init__(*args, **kwargs)
        if self.date is None:
            self.date = datetime.datetime.now()

    def _result_html(self):
        if hasattr(self.value, '__html__'):
            return self.value.__html__()
        if hasattr(self.value, '__repr_html__'):
            return self.value.__repr_html__()
        elif isinstance(self.value, sympy.Expr):
            return sympy.latex(self.value)
        else:
            return str(self.value)

    def __repr_html__(self):
        template = env.get_template('base_report.html')
        return template.render(report = self)


class Report(documents.Document):
    title = traitlets.Unicode()
    results = traitlets.List(documents.Reference(Result))
    date = traitlets.Instance(datetime.datetime)

    def __init__(self, *args, **kwargs):
        super(Report, self).__init__(*args, **kwargs)
        if self.date is None:
            self.date = datetime.datetime.now()

    def __html__(self):
        template = env.get_template('report_base.html')
        return template.render(report = self)

    def make_report(self, report_folder,openbrowser = True):
        save_html_report(self.__html__(), report_folder,
                         openbrowser=openbrowser)



def save_html_report(output, report_folder, openbrowser = True):
    fname = os.path.join(report_folder, "report.html")
    try:
        with codecs.open(fname, 'w', encoding = 'utf-8') as f:
            f.write(output)
    except IOError as e:
        print("ERROR. Could not write file %s" % fname, file = sys.stderr)
        raise e
    
    staticdest = os.path.join(report_folder,'static')
    if not os.path.isdir(staticdest):
        try:
            shutil.copytree(STATIC, staticdest)
        except IOError as e:
            print("ERROR. Could not copy static folder to %s"
                    % (report_folder), file = sys.stderr)
            raise e
    
    if openbrowser:
        webbrowser.open(os.path.abspath(f.name))

