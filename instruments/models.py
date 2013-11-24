# -*- coding: utf-8 -*-
from string import Formatter

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.core.exceptions import ObjectDoesNotExist
#from django.db.models import signals

from zutils.utils import make_signature


import utils
import device_comm
from errors import InstrumentError
# Create your models here.


COMMAND_TYPES = (
    ('W', "Write"),
    ('A', "Ask"),
    ('B', "Ask Raw"),
                 
)



class AbstractInstrument(models.Model):
    class Meta:
        abstract = True
        
    #id = models.AutoField(primary_key=True)
    name = models.CharField(max_length = 256, unique = True)
    base_instrument = models.ForeignKey('BaseInstrument', 
                                        null = True, blank = True)
    commands = generic.GenericRelation('Command')
    
    def add_command(self, command):
        if not self.pk:
            self.save()
        if not command.pk:
            command.instrument = self
            command.save()
        else:
            raise ValueError("Command must not be bound.")

    def create_command(self, *args, **kwargs):
        c = Command(*args, **kwargs)        
        self.add_command(c)
        
    def load_from_base(self):
        #print self
        #print self.base_instrument
        if self.base_instrument:
            #print "Adding commands"
            for command in self.base_instrument.commands.all():
                if not self.commands.filter(name = command.name).exists():
                    command.pk = None
                    command.instrument = self
                    command.save()
        
    
    def __unicode__(self):
        return self.name

@utils.autoconnect        
class BaseInstrument(AbstractInstrument):
    def post_save(self, **kwargs):
        self.load_from_base()
    

@utils.autoconnect
class Instrument(AbstractInstrument):

    
    device_id = models.CharField(max_length = 256,
                                 null = True, unique = True, blank = True)
    
    #interface = models.ForeignKey(Interface)
    #commands = models.ManyToManyField(Command)
    
    def make_command_function(self, command):
        attrname = utils.normalize_name(command.name)
        #if not hasattr(self, attrname):
        commandcall = command.make_callable(self)            
        setattr(self, attrname, commandcall)
        #else:
        #    raise ValueError("Name %s is already an instrument attribute")

    def add_command(self, command):
        
        super(Instrument, self).add_command(command)
        #print "Command %s added" % command
        self.make_command_function(command)


    def make_interface(self):
        allcommands = self.commands.all()
        for command in allcommands:
            self.make_command_function(command)
        
    def post_save(self, **kwargs):
        self.load_from_base()
        

#==============================================================================
#     def post_init(self, **kwargs):
#         try:
#             self.prepare()
#         except InstrumentError:
#             pass
#==============================================================================
                
        
    
    def associate(self, device_id, device):
        if self.device_id and self.device_id != device_id:
            raise ValueError("""Instrument already has the device id %s.
                Cannot associate with %s"""%(self.device_id, device_id))
                
        self.device_id = device_id
        self.device = device
        self.save()
        device.is_controlled = True
        self.make_interface()
        #self.prepare()

    def load_device(self):
        allins = device_comm.find_all()
        if self.device_id in allins:
            devobj = device_comm.next_not_controlled(self.device_id)
            if not devobj:
                return False
                
            self.associate(self.device_id, devobj.device)
            return True
        else:
            return False
    
    def prepare(self):
        if self.load_device() and self.id:
            self.load_from_base()
        else:
           raise InstrumentError("Cannot prepare device."
               "Save it to the DB first.")



@utils.autoconnect
class Command(models.Model):
    name = models.CharField(max_length = 128)
    command_string = models.CharField(max_length = 1024)
    
    command_type = models.CharField(max_length = 1, choices = COMMAND_TYPES, 
                                    blank = True)
                                    
    def __init__(self, *args ,**kwargs):
        print args
        print kwargs
        super(Command, self).__init__(*args, **kwargs)
        if 'description' in kwargs:
            print "DESCRIPTIOON"
            self.description = kwargs['description']
        self._base_command = None
                                        
   
    @property
    def base_command(self):
        if self._base_command:
            return self._base_command
        bins = self.instrument.base_instrument
        if bins:
            try:
                self._base_command = bins.commands.get(name = self.name)
                return self._base_command
            except  ObjectDoesNotExist:
                return None
        return None
            
        
    content_type = models.ForeignKey(ContentType)                                
    object_id = models.PositiveIntegerField()                                
    instrument = generic.GenericForeignKey()
    
    
        
    private_description = models.TextField(default = "", blank = True)
    
    @property
    def description(self):
        if self.base_command:
            return self.base_command.private_description
        else:
            return self.private_description
            
    @description.setter     #analysis:ignore   
    def description(self, value):
        bc = self.base_command
        if bc:
            self.base_command.private_description = value
            self.base_command.save()
        else:
            self.private_description = value
    
    class ParamFinder(object):
        def __init__(self, command):
            self.command = command
        def __getitem__(self, key):
            return self.command.parameter_set.get(name = key)
            
    @property
    def parameters(self):
        return Command.ParamFinder(self)
    
    
    def save_params(self):
        f = Formatter()
        tokens = f.parse(self.command_string)
        
        param_names = []
        for (_ , param_name, _ , _) in tokens:
            if param_name is not None:
                self.parameter_set.get_or_create(name = param_name)
                param_names += [param_name]
            
                
        self.parameter_set.exclude(name__in = param_names).delete()
                
    def make_callable(self, instrument):
        
        params = self.parameter_set.all()
        argnames = []
        allnames = []
        kwargdefaults = {}
        for param in params:
            if param.default_value:
                kwargdefaults[param.name] = param.default_value
            else:
                argnames += [param.name]
            allnames += [param.name]
                
        ct = self.command_type
        if ct == "W":
            instrf = instrument.device.write
        elif ct == "A":
            instrf = instrument.device.ask
        elif ct == "B":
            instrf = instrument.device.ask_raw
        
        #f_factory is needed so that variables get bundled in f.
        def f_factory(command_string, loc_instrf, loc_argnames):

            def f(*args, **kwargs):
    
                argdict = {argname: arg 
                    for argname, arg in zip(loc_argnames, args)}
                        

                
                argdict.update(kwargs)

                instruction = command_string.format(**argdict)
                
                retval = loc_instrf(instruction)
                
                return retval
            
            return f
            
        s = self.command_string
       
        f = f_factory(s, instrf, argnames)        
                
        f.__doc__ = "%s\n%s\nThe query for this command is:\n%s" % (
                        self.description,
                        self.private_description,
                        self.command_string)
                                
        #print ("Making callable for %s" % self.command_string)
        return make_signature(f, argnames, kwargdefaults)
        
            
    def pre_save(self, **kwargs):
        if not self.command_type:
            if self.command_string.endswith('?'):
                self.command_type = "A"
            else:
                self.command_type = "W"
        
        
        bins = self.instrument.base_instrument
        if bins and not bins.commands.filter(name = self.name).exists():
            newcommand = Command(
                            name = self.name,
                            command_string = self.command_string, 
                            description = self.description)
            
            bins.add_command(newcommand)
            #self.base_command = newcommand
                
        
    
    def post_save(self, **kwargs):
        self.save_params()
        if self.base_command:
            self.base_command.save()
        
           
    


    def __unicode__(self):
        return self.name
        
class Parameter(models.Model):
    command = models.ForeignKey(Command, null = False)
    name = models.CharField(max_length = 128)
    default_value = models.CharField(max_length = 128, blank = True)
    description = models.TextField(default = "", blank = True)
    
    
    def __unicode__(self):
        return self.name


    