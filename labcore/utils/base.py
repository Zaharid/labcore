# -*- coding: utf-8 -*-
import re
import keyword

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
    exec(evalstr, gl, locals())
    
    return functools.wraps(f)(signed_f) #analysis:ignore
