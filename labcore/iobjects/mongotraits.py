# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 16:10:18 2014

@author: zah
"""


from IPython.utils.py3compat import iteritems, PY3

import mongoengine as mg
from mongoengine import fields
from IPython.utils import traitlets
from IPython.utils.traitlets import TraitType, HasTraits, MetaHasTraits

from mongoengine.base.metaclasses import TopLevelDocumentMetaclass as MongoMeta

mg.connect('test')

class Meta(MongoMeta, MetaHasTraits):
  
    def __new__(mcls, name, bases, classdict):
        
        traits_class = MetaHasTraits.__new__(mcls, name, bases, classdict)
        _dbtraits = []
        field_dict={}        
        for key, value in iteritems(classdict):
            if isinstance(value, TraitType):
                field = value._metadata.get('db')
                if field:
                    dbkey = key+"_db"
                    field_dict[dbkey] = field(
                    #name = name,
                    #default = getattr(traits_class.traits, name).default
                    )
                    
                    _dbtraits += [(key, dbkey)]
        
        classdict.update(field_dict)
        metadic = classdict.get('meta',{})
        metadic['allow_inheritance'] = True
        classdict['meta'] = metadic
        mongo_class = MongoMeta.__new__(mcls, name, bases, classdict)
        #print mongo_class.__dict__
        
        d = dict(traits_class.__dict__)
        d.update(dict(mongo_class.__dict__))
        #print d
        def __init__(self, **kwargs):
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
        
        
        d['__init__'] = __init__
        
        d['_dbtraits'] = _dbtraits 
        return type.__new__(mcls, name, bases, d)



TraitDocument = Meta('TraitsDocument', (HasTraits, mg.Document),{})
   
            



class Nideconia(TraitDocument):
    
    f = traitlets.Any(db=fields.DynamicField)
    g = traitlets.Any(db=fields.DynamicField)
    h = fields.DynamicField()
    
    def __unicode__(self):
        d = {'f':self.f,'g':self.g, 'h':self.h}
        return unicode(d)


