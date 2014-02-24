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
        classdict['meta'] = metadic
        mongo_class = MongoMeta.__new__(mcls, name, bases, classdict)
        
        d = dict(traits_class.__dict__)
        d.update(dict(mongo_class.__dict__))
        
        d['_dbtraits'] = _dbtraits 
        return type.__new__(mcls, name, bases, d)



#We can extend this class
TraitDocument = Meta('TraitsDocument', (HasTraits, mg.Document),{})

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


