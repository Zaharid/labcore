# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 16:10:18 2014

@author: zah
"""
import weakref

from IPython.utils.py3compat import iteritems, string_types

import mongoengine as mg
import mongoengine.base
from mongoengine.base import BaseField, get_document, _document_registry
from mongoengine import fields
from IPython.utils import traitlets
from IPython.utils.traitlets import TraitType, HasTraits, MetaHasTraits

from bson import objectid



RECURSIVE_REFERENCE_CONSTANT = 'self'

field_map = {
    traitlets.Bool: fields.BooleanField,
    traitlets.Float: fields.FloatField,
    traitlets.Int: fields.IntField,
    traitlets.Instance: fields.ReferenceField,

}

class MongoTraitsError(Exception):
    pass

def set_field(field_class, key):
    return field_class(
        db_field = key
    )
    
    
class TraitsDBMeta(MetaHasTraits):
    """
    Allows subclassing Mongoengine classes and IPython HasTraits classes.
    Alsom the Traits with db=True or db = Field metadata field will be
    syncronized with a Mongoengine field called traitname_db. In order to 
    produce a __new__ class, the mongometa variable must be set appropiately.
    """
    mongometa = None
    def __new__(mcls, name, bases, classdict):
        if mcls.mongometa is None:
            raise(TypeError("You must specify mongometa"))
            
        
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
        mongo_class = mcls.mongometa.__new__(mcls, name, bases, classdict)
        
        traits_class = MetaHasTraits.__new__(mcls, name, bases, classdict)
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
    
    def __init__(self, document_type, field, obj_type = None, id_name = 'id', 
                 **field_options):
       
        self.document_type_obj = document_type
        self.field = field
        self.obj_type_obj = obj_type
        self.id_name = id_name
        self.field_options = field_options
        
    @property
    def document_type(self):
        return self.resolve_model(self.document_type_obj)
    
    @property
    def obj_type(self):
        if self.obj_type_obj is None:
            #Suppose it's a list with embedded reference.
            self.obj_type_obj = self.document_type._fields[self.field].field.document_type
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
    """Metaclass that allows classes that implement it to use the 
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
            try:
                uid = getattr(obj, value.id_name)
            except AttributeError:
                raise MongoTraitsError("The document %s does not have the requested id field: %s"
                    %(obj, value.id_name))
            setattr(self,idkey, uid)
        return property(getter, setter)
        
    def __new__(mcls, cls_name, bases, classdict):
        #Cant change classdoct size while iterationg
        d = {}
        for key,value in classdict.items():
            if isinstance(value, EmbeddedReferenceField):
                field = fields.ObjectIdField(**value.field_options)
                field_key = '_'+key
                d[field_key] = field
                d[key] =mcls.makeprop(key,value)
                d['_idfield'] = value.id_name
        classdict.update(d)
        return super(MetaWithEmbedded, mcls).__new__(mcls, cls_name, bases, classdict)
        

class SingleId(type):
    _id_prop = 'id'
    def __init__(mcls, class_name, bases, class_dict):
        mcls._iddict = weakref.WeakValueDictionary()
        super(SingleId,mcls).__init__(class_name, bases, class_dict)
    def __call__(self, *args, **kwargs):
        ins = super(SingleId,self).__call__(*args, **kwargs)
        uid = getattr(ins, ins.__class__._id_prop, None)
        if uid is not None:
            if uid in ins.__class__._iddict:
                ins = ins.__class__._iddict[uid]
            else:
                ins.__class__._iddict[uid] = ins
        return ins

class AutoID(object):
    _autoid_prop = 'id'
    def __init__(self, *args, **kwargs):
        super(AutoID,self).__init__(*args,**kwargs)
        idprop = self.__class__._autoid_prop
        try:
            uid = getattr(self,idprop)
        except AttributeError:
            pass
        else:
            if uid is None:
                uid = objectid.ObjectId()
            


class AbstractMeta(SingleId, MetaWithEmbedded, TraitsDBMeta):
    pass
 
#Subclassing of mongo metaclasses doesn't have an effect other that make python
#stop complaining.       
class DocumentMeta(AbstractMeta, type(mg.Document)):
    mongometa = type(mg.Document)

class EmbeddedDocumentMeta(AbstractMeta, type(mg.EmbeddedDocument)):
    mongometa = type(mg.EmbeddedDocument)
        

def meta_extends(name, meta, base):
    metaname = base.__name__ + meta.__name__
    base_meta = type.__new__(type, metaname, (base.__metaclass__,),
                             dict(meta.__dict__))
    return base_meta(name, (base,), {})

#This is ugly but compatible with Python 2 and 3
    
def _td__init__(self,*args,**kwargs):
    """
    Initialize the trait_db fields to track the traits.
    """
    print ("tdinit")
    super(self.__class__._superguard,self).__init__(*args, **kwargs)
    
    
    def change_field(name, old, new):
        setattr(self, name+'_db',new)
        
    for (key, dbkey) in self.__class__._dbtraits:
        val = getattr(self, dbkey)
        if val is not None:
            setattr(self, key, val)
        if key in kwargs:
            setattr(self, dbkey, kwargs[key])
        self.on_trait_change(change_field, key)

_d = {
    '__init__': _td__init__,
    'meta':{'abstract':True}
}
#Turns out _d is modiffied by these lines.
Document = DocumentMeta('Document', (mg.Document, HasTraits), dict(_d))
Document._superguard = Document 

EmbeddedDocument = EmbeddedDocumentMeta('EmbeddedDocument', 
                                        (AutoID,mg.EmbeddedDocument, HasTraits), 
                                        dict(_d))
EmbeddedDocument._superguard = EmbeddedDocument 

mongoengine.base._document_registry = {}                                       
