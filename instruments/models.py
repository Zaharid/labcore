from string import Formatter

from django.db import models
#from django.db.models import signals

from zutils.utils import make_signature


import utils

# Create your models here.


COMMAND_TYPES = (
    ('W', "Write"),
    ('A', "Ask"),
    ('B', "Ask Raw"),
                 
)



@utils.autoconnect
class Command(models.Model):
    name = models.CharField(max_length = 128)
    command_string = models.CharField(max_length = 1024)
    
    command_type = models.CharField(max_length = 1, choices = COMMAND_TYPES, 
                                    blank = True)
    
    
    
    description = models.TextField(default = "", blank = True)
    
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
    
        def f(*args, **kwargs):
            argdict = {argname: arg 
                for argname, arg in zip(allnames, args)}
                    

            
            argdict.update(kwargs)
            
          
            
            instruction = self.command_string.format(**argdict)
            
            retval = instrf(instruction)
            
            return retval
            
                
                
        f.__doc__ = "%s\nThe query for this command is:\n%s"%(self.description,
                                self.command_string)
        return make_signature(f, argnames, kwargdefaults)
        
        
    def pre_save(self):
        if not self.command_type:
            if self.command_string.endswith('?'):
                self.command_type = "A"
            else:
                self.command_type = "W"
    
    def post_save(self):
        self.save_params()
    


    def __unicode__(self):
        return self.name
        
class Parameter(models.Model):
    command = models.ForeignKey(Command, null = False)
    name = models.CharField(max_length = 128)
    default_value = models.CharField(max_length = 128, blank = True)
    description = models.TextField(default = "", blank = True)
    
    
    def __unicode__(self):
        return self.name
        



class Interface(models.Model):
    name = models.CharField(max_length = 128)
    module = models.CharField(max_length = 128)
    def __unicode__(self):
        return self.name

@utils.autoconnect
class Instrument(models.Model):

    name = models.CharField(max_length = 256)
    interface = models.ForeignKey(Interface)
    commands = models.ManyToManyField(Command)
    
    def make_command_function(self, command):
        attrname = utils.normalize_name(command.name)
        if not hasattr(self, attrname):
            commandcall = command.make_callable(self)            
            setattr(self, attrname, commandcall)
        else:
            raise ValueError("Name %s is already an instrument attribute")

    
    
    def make_interface(self):
        allcommands = self.commands_set.all()
        for command in allcommands:
            self.make_command_function(command)
        
    
    def __unicode__(self):
        return self.name
        
    def post_init(self):
       self.load_instrument()
       self.make_interface()
        
    def load_instrument(self):
         print self.name
    
    