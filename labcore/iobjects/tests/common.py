# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 22:08:15 2014

@author: zah
"""
import itertools
import mongoengine.fields as fields
from IPython.utils import traitlets

from labcore.iobjects.mongotraits import (Document,
    EmbeddedDocument, EmbeddedReferenceField, AutoID)

class Partner(EmbeddedDocument):
    name = fields.StringField()
    ref = EmbeddedReferenceField('Doc', 'refs')

class Doc(AutoID, Document):

    ids = itertools.cycle((1,2))
    def __init__(self, *args, **kwargs):
        super(Doc,self).__init__(*args, **kwargs)
        self.uid = next(Doc.ids)
    uid = traitlets.Any(db = True)
    f = traitlets.Bool(db=True)
    eid = fields.ObjectIdField()

    g = traitlets.Any(db=fields.DynamicField)
    h = fields.DynamicField()
    refs = fields.ListField(fields.EmbeddedDocumentField('EmbDoc'))
    partner = fields.EmbeddedDocumentField('Partner')

    def __str__(self):
        d = {'f':self.f,'g':self.g, 'h':self.h}
        return str(d)

class EmbDoc(EmbeddedDocument):
    eid = fields.ObjectIdField()
    name = fields.StringField()


