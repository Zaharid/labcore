# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 16:10:18 2014

@author: zah
"""
import weakref

from IPython.utils.py3compat import iteritems, string_types

import mongoengine as mg
from mongoengine.base import BaseField, get_document
from mongoengine import fields
from IPython.utils import traitlets
from IPython.utils.traitlets import TraitType, HasTraits, MetaHasTraits

from mongoengine.base.metaclasses import TopLevelDocumentMetaclass as MongoMeta

RECURSIVE_REFERENCE_CONSTANT = 'self'

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
    
    
class TraitsDBMeta(MongoMeta, MetaHasTraits):
    """
    Allows subclassing Mongoengine classes and IPython HasTraits classes.
    Alsom the Traits with db=True or db = Field metadata field will be
    syncronized with a Mongoengine field called traitname_db.
    """
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
    """Field that allows reference to embedded objects.
     
    Parameters
    ----------
    
    document : 
        The document in whose collection to search fot the regerence.
    
    field :
        The field of `document` that stores the references.
    
    obj_type :
        The type of the EmbeddedDocument.
    
    id_name :
        The namos of the field that stores the id reference. `obj_type` must
        implement this field.
    """
    
    def __init__(self, document_type, field, obj_type = None, id_name = "_id", 
                 **field_options):
       
        self.document_type_obj = document_type
        self.field = field
        if obj_type is None:
            #Suppose it's a list with embedded reference.
            obj_type = self.document._fields[field].field.document_type
        self.obj_type_obj = obj_type
        self.id_name = id_name
        self.field_options = field_options
        
    @property
    def document_type(self):
        return self.resolve_model(self.document_type_obj)
    
    @property
    def obj_type(self):
        return self.resolve_model(self.obj_type_obj)
    
    @staticmethod
    def resolve_model(obj):
        if isinstance(obj, string_types):
            if obj == RECURSIVE_REFERENCE_CONSTANT:
                #self.document_type_obj = self.owner_document
                raise NotImplementedError("Can't refer to self.")
            else:
                obj = get_document(obj)
        return obj
        


class MetaWithEmbedded(type):
    """Metaclass who allows classes that implement it to use the 
    `EmbeddedReferenceField`. To be used with the mongoengine classes it has to
    go trough `meta_extends` to inherit from the appropiate metaclass."""
    @staticmethod
    def makeprop(key,value):
        """Returns the property for a field name (key) and the 
        corresponding `EmbeddedReferenceField` object (value) to be added to
        the appropiate entry."""
        idkey = "_"+key
        def getter(self):
            c = value.document_type._get_collection()
            f = value.field
            idf = value.id_name
            idval = getattr(self, idkey)
            mgobj = c.find_one({'%s.%s'%(f,idf):idval},
                               {'%s.$'%f:1,"_id":0})['%s'%f][0]
                               
            return value.obj_type(**mgobj)
                    
        def setter(self, obj):
            uid = getattr(obj, value.id_name)
            setattr(self,idkey, uid)
        return property(getter, setter)
        
    def __new__(mcls, cls_name, bases, classdict):
        for key,value in classdict.items():
            if isinstance(value, EmbeddedReferenceField):
                field = fields.ObjectIdField(**value.field_options)
                field_key = '_'+key
                classdict[field_key] = field
                classdict[key] =mcls.makeprop(key,value)
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
    base_meta = type.__new__(type, metaname, (base.__metaclass__,),
                             dict(meta.__dict__))
    return base_meta(name, (base,), {})
    


Document = meta_extends('Document', MetaWithEmbedded, mg.Document)

EmbeddedDocument = meta_extends('EmbeddedDocument',MetaWithEmbedded, 
                                mg.EmbeddedDocument)
        
                 
                

TraitDocument = TraitsDBMeta('TraitsDocument', (HasTraits, mg.Document),{})

    
def td__init__(self, **kwargs):
    """
    Initialize the trait_db fields to track the traits.
    """
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
            
class SingleId(type):
    id_prop = 'id'
    def __init__(mcls, class_name, bases, class_dict):
        mcls._iddict = weakref.WeakValueDictionary()
        super(SingleId,mcls).__init__(class_name, bases, class_dict)
    def __call__(self, *args, **kwargs):
        ins = super(SingleId,self).__call__(*args, **kwargs)
        uid = getattr(ins, ins.__class__.id_prop, None)
        if uid is not None:
            if uid in ins.__class__._iddict:
                print ins
                ins = ins.__class__._iddict[uid]
                print ins
            else:
                ins.__class__._iddict[uid] = ins
                print ins.__class__._iddict
        return ins

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

class A():
    import itertools
    ids = itertools.cycle((1,2))
    def __init__(self):
        self.id = next(A.ids)
        print self.id
        super(A,self).__init__()
A = SingleId('A', (),A.__dict__)
class B():
    pass
B=SingleId('B', (),B.__dict__)
