# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:26:40 2014

@author: zah
"""

import mongoengine as mg
import mongoengine.fields as fields
from IPython.utils import traitlets

from labcore.iobjects.mongotraits import (Document, 
    EmbeddedDocument, EmbeddedReferenceField)

from .common import TDoc, TEDoc,Partner


def setUp():
    mg.connect('test')
        
def test_bassic():
    refs = [TEDoc(name = i) for i in "xyzt"]
    t = TDoc()
    t.refs = refs
    x = Partner(name = "p")
    x.ref = refs[3]
    t.partner = x
    t.save()
    assert(t.partner.ref is refs[3])
    
def tearDown():
    mg.connection.disconnect()