# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:26:40 2014

@author: zah
"""
import itertools

import mongoengine as mg
import mongoengine.fields as fields
from IPython.utils import traitlets
from mongotraits import Document, EmbeddedDocument, EmbeddedReferenceField



class TDoc(Document):
    
    ids = itertools.cycle((1,2))
    def __init__(self):       
        super(TDoc,self).__init__()
        self.uid = next(TDoc.ids)
    uid = traitlets.Any(db = True)
    f = traitlets.Bool(db=True)
    g = traitlets.Any(db=fields.DynamicField)
    h = fields.DynamicField()
    refs = fields.ListField(fields.EmbeddedDocumentField('TEDoc'))
    
    def __str__(self):
        d = {'f':self.f,'g':self.g, 'h':self.h}
        return str(d)

class TEDoc(EmbeddedDocument):
    id = fields.ObjectIdField()
    name = fields.StringField()

class Partner(EmbeddedDocument):
    name = fields.StringField()
    ref = EmbeddedReferenceField(TDoc, 'refs')
    

def setUp():
    mg.connect('test')
        
def test_bassic():
    t = TDoc()
    
def tearDown():
    mg.connection.disconnect()