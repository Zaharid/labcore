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




class AbstractTraitsDBMeta(type):
    """
    Allows subclassing Mongoengine classes and IPython HasTraits classes.
    Alsom the Traits with db=True or db = Field metadata field will be
    syncronized with a Mongoengine field called traitname_db.
    """
    @staticmethod
    def set_field(field_class, key):
        return field_class(
            db_field = key
        )
    
    def __new__(mcls, name, bases, classdict):
        _dbtraits = []
        field_dict={}
        for key, value in iteritems(classdict):
            if isinstance(value, TraitType):
                field_spec = value._metadata.get('db', False)
                if field_spec:
                    if isinstance(field_spec, BaseField):
                        field = field_spec
                    elif isinstance(field_spec, type):
                        field = mcls.set_field(field_spec, key)
                    else:
                        field = mcls.set_field(field_map.get(value.__class__,
                                                fields.DynamicField), key)

                dbkey = key+"_db"
                field_dict[dbkey] = field

                _dbtraits += [(key, dbkey)]

        classdict.update(field_dict)
        classdict['_dbtraits'] = _dbtraits
        return super(AbstractTraitsDBMeta,mcls).__new__(mcls, name,
                    bases, classdict)



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
    def _dbkey(key):
        return key + "_db"
    @staticmethod    
    def _objref(key):
        return key + "_ref"    
    @staticmethod
    def makeprop(key,value):
        """Returns the property for a field name (key) and the
        corresponding `EmbeddedReferenceField` object (value) to be added to
        the appropiate entry."""
        
        def getter(self):
            ref = getattr(self, MetaWithEmbedded._objref(key), None)
            if ref:
                return ref
            c = value.document_type._get_collection()
            f = value.field
            idf = value.id_name
            idval = getattr(self, MetaWithEmbedded._dbkey(key))
            if not idval:
                return None
            query = {'%s.%s'%(f,idf):idval}
            projection = {'%s.$'%f:1,"_id":0}
            mgobj = c.find_one(query, projection)['%s'%f][0]

            return value.obj_type(**mgobj)
            
        def getter2(self):
            f = value.field
            idf = value.id_name
            idval = getattr(self, MetaWithEmbedded._dbkey(key))
            query = {"%s__%s"%(f, idf) : idval}
            print(query)
            doc = value.document_type.objects.get(**query)
            return getattr(doc, f)[0]

        def setter(self, obj):
            try:
                uid = getattr(obj, value.id_name)
            except AttributeError:
                raise MongoTraitsError("The document %s does not have the requested id field: %s"
                    %(obj, value.id_name))
            setattr(self,MetaWithEmbedded._dbkey(key), uid)
            setattr(self, MetaWithEmbedded._objref(key), obj)
        return property(getter, setter)

    def __new__(mcls, cls_name, bases, classdict):
        #Cant change classdoct size while iterationg
        d = {}
        for key,value in classdict.items():
            if isinstance(value, EmbeddedReferenceField):
                field = fields.ObjectIdField(**value.field_options)
                field_key = mcls._dbkey(key)
                d[field_key] = field
                d[key] =mcls.makeprop(key,value)
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
                setattr(self, idprop, uid)



class AbstractMeta(SingleId, MetaWithEmbedded, AbstractTraitsDBMeta, MetaHasTraits):
    pass



class DocumentMeta(AbstractMeta, type(mg.Document)):
    pass

class EmbeddedDocumentMeta(AbstractMeta, type(mg.EmbeddedDocument)):
    pass


#This is ugly but compatible with Python 2 and 3

def _td__init__(self,*args,**kwargs):
    """
    Initialize the trait_db fields to track the traits.
    """
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
Document = DocumentMeta('Document', (AutoID, mg.Document, HasTraits), dict(_d))
Document._superguard = Document

EmbeddedDocument = EmbeddedDocumentMeta('EmbeddedDocument',
                                    (AutoID, mg.EmbeddedDocument, HasTraits),
                                     dict(_d))
EmbeddedDocument._superguard = EmbeddedDocument
