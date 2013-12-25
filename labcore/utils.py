'''
Created on Apr 1, 2013

@author: zah
'''
import sys
import os
import os.path as osp
import functools
import pickle
import webbrowser
import tempfile
import re

import keyword


class Bunch(dict):
    """A convenience class that allows accessing dict keys with the dot syntax,
    ie mybunch['key'] and mybunch.key."""
    def __init__(self, **kw):
        dict.__init__(self, kw)
        self.__dict__ = self

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)
        self.__dict__ = self
        

def openhtml(htmltext):
    """Open the given html text in the browser"""
    t = tempfile.NamedTemporaryFile(delete = False)
    t.write(htmltext)
    webbrowser.open(t.name)



def make_signature(f, argss = None, kwargs = None):
    """Return a function that does the same as f but has the signature given by
    the list of strings 'argss' and the dict 'kwargs'."""
    valid = re.compile(r'[\_0-9a-zA-Z]+$')
    def check_valid(item):
        assert item == str(item), "Arguments must me strings."
        assert re.match(valid, item), "Argument must be letters, numbers"
        " and underscore only."
        assert item not in keyword.kwlist, "Argument can't be a keyword"
        return True
        

    argstr = ""
    if argss is not None:
        argstr = ", ".join([arg for arg in argss if check_valid(arg)])
    kwarglist = []
    exekw = []
    exestr = argstr[:]
    
    if kwargs:
        for key, value in kwargs.iteritems():
           check_valid(key)
           kwarglist.append("%s = %r"%(key, value))
           exekw.append("%s = %s" % (key,key))
           
        if argstr: argstr += ", "   
        exestr = argstr +  ", ".join(exekw)      
        argstr = argstr +   ", ".join(kwarglist)
    
 
    evalstr = "def signed_f({0}): return f({1})".format(argstr,exestr)
    gl = {"f":f}
    exec evalstr in gl, locals()
    
    return functools.wraps(f)(signed_f) #analysis:ignore

    
def save_obj(obj, name = 'clf'):
    "One liner for saving a python object"
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
        
def load_obj(name = 'clf'):
    "One liner for loading a python object"
    with open('obj/' + name + '.pkl', 'r') as f:
        return pickle.load(f)

    
    
def django_shell(project_loc = '.', settingsmodule = None):
    """Loads the project settingd and puts the project in path.
    This should be equivalent to manage.py shell."""
    base_path = osp.abspath(project_loc)
    if settingsmodule is None:
        settingsmodule = osp.basename(base_path) + ".settings"
    sys.path.append(base_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settingsmodule)
    
    