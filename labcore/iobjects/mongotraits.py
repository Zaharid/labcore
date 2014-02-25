# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 16:10:18 2014

@author: zah
"""


from IPython.utils.py3compat import iteritems

import mongoengine as mg
from mongoengine.base import BaseField
from mongoengine import fields
from IPython.utils import traitlets
from IPython.utils.traitlets import TraitType, HasTraits, MetaHasTraits

from mongoengine.base.metaclasses import TopLevelDocumentMetaclass as MongoMeta
from bson import objectid



field_map = {
    traitlets.Bool: fields.BooleanField,
    traitlets.Float: fields.FloatField,
    traitlets.Int: fields.IntField,
    traitlets.Instance: fields.ReferenceField,

}

def set_field(field_class, key):
    return field_class(
        db_field = key
    )
    
    
class Meta(MongoMeta, MetaHasTraits):
    def __new__(mcls, name, bases, classdict):
        traits_class = MetaHasTraits.__new__(mcls, name, bases, classdict)
        _dbtraits = []
        field_dict={}        
        for key, value in iteritems(classdict):
            if isinstance(value, TraitType):
                field_spec = value._metadata.get('db', False)
                if field_spec:
                    if isinstance(field_spec, BaseField):
                        field = field_spec
                    elif isinstance(field_spec, type):
                        field = set_field(field_spec, key)
                    else:
                        field = set_field(field_map.get(value.__class__, 
                                                fields.DynamicField), key)
                
                dbkey = key+"_db"
                field_dict[dbkey] = field
                    
                _dbtraits += [(key, dbkey)]
        
        classdict.update(field_dict)
        metadic = classdict.get('meta',{})
        metadic['allow_inheritance'] = True
        if not 'collection' in metadic:
            metadic['collection'] =  ''.join('_%s' % c if c.isupper() else c
                                         for c in name).strip('_').lower()
        classdict['meta'] = metadic
        mongo_class = MongoMeta.__new__(mcls, name, bases, classdict)
        
        d = dict(traits_class.__dict__)
        d.update(dict(mongo_class.__dict__))
        
        d['_dbtraits'] = _dbtraits 
        return type.__new__(mcls, name, bases, d)
        

class EmbeddedReferenceField(object):
    def __init__(self, document, field, id_name = "_id", **field_options):
        self.document = document
        self.field = field
        self.id_name = id_name
        self.field_options = field_options
        
def makeprop(key,value):
    def getter(self):
        query_dict = {
            "%s__%s"%(value.field,value.id_name): getattr(self, "_"+key)
        }
        print query_dict
        print value.document
        return value.document.objects(**query_dict)
                
    def setter(self, obj):
        field_key = "_"+key
        uid = getattr(obj, value.id_name)
        setattr(self,field_key, uid)
    return property(getter, setter)

class MetaWithEmbedded(type):
    def __new__(mcls, cls_name, bases, classdict):
        for key,value in classdict.items():
            if isinstance(value, EmbeddedReferenceField):
                field = fields.ObjectIdField(**value.field_options)
                field_key = '_'+key
                classdict[field_key] = field  
                classdict[key] =makeprop(key,value)
                classdict['_idfield'] = value.id_name
        metadic = classdict.get('meta',{})
        if not 'collection' in metadic:
            metadic['collection'] =  ''.join('_%s' % c if c.isupper() else c
                                         for c in cls_name).strip('_').lower()
        metadic['allow_inheritance'] = True
        classdict['meta'] = metadic
        #Dont know how to call super here...
        superclass = mcls.__mro__[1]
        return superclass.__new__(mcls, cls_name, bases, classdict)

def meta_extends(name, meta, base):
    metaname = base.__name__ + meta.__name__
    base_meta = type.__new__(type, metaname, (base.__metaclass__,), dict(meta.__dict__))
    return base_meta(name, (base,), {})
    


Document = meta_extends('Document', MetaWithEmbedded, mg.Document)

EmbeddedDocument = meta_extends('EmbeddedDocument',MetaWithEmbedded, mg.EmbeddedDocument)
        
                 
                
#We can extend this class
TraitDocument = Meta('TraitsDocument', (HasTraits, mg.Document),{})
#ZtDocument = MetaWithEmbedded('ZDocument', (HasTraits, mg.Document),{})

#Init has to be set here because it isn't easy to have a py3-compatible
#class with metaclass.     
def td__init__(self, **kwargs):
    mg.Document.__init__(self, **kwargs)
    HasTraits.__init__(self, **kwargs)
    
    def change_field(name, old, new):
        setattr(self, name+'_db',new)
        
    for (key, dbkey) in self.__class__._dbtraits:
        val = getattr(self, dbkey)
        if val is not None:
            setattr(self, key, val)
        if key in kwargs:
            setattr(self, dbkey, kwargs[key])
        self.on_trait_change(change_field, key)
TraitDocument.__init__ = td__init__
            



class Test(TraitDocument):
    meta = {'collection': 'test',
            'index_cls': False
    }
    
    def __init__(self):
        print ("tdaexis")
        super(Test,self).__init__()
    
    f = traitlets.Bool(db=True)
    g = traitlets.Any(db=fields.DynamicField)
    h = fields.DynamicField()
    
    def __str__(self):
        d = {'f':self.f,'g':self.g, 'h':self.h}
        return str(d)


