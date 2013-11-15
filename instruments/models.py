from string import Formatter

from django.db import models
#from django.db.models import signals


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
    
    
    def save_params(self):
        f = Formatter()
        tokens = f.parse(self.command_string)
        oldparams = Parameter.objects.filter(command = self)
        oldparams.delete()
        for (_ , param_name, _ , _) in tokens:
            if param_name is not None:
                param = Parameter(name = param_name, command = self)
                param.save()
        
                
    def make_callable(self, instrument):
        
        params = Parameter.objects.filter(command = self)
        argnames = []
        kwargdefaults = {}
        for param in params:
            if param.default_value:
                kwargdefaults[param.name] = param.default_value
            else:
                argnames += [param.name]
        
        def f(*args, **kwargs):
            argdict = {argname: arg 
                for argname, arg in zip(argnames.argvalues)}
                    
            formatdict = argdict.update(kwargs)
            instruction = self.command_string.format(**formatdict)
            
            if self.commaand_type == "W":
                retval = instrument.device.write(instruction)
            elif self.commaand_type == "A":
                retval = instrument.device.ask(instruction)
            elif self.commaand_type == "B":
                retval = instrument.device.ask_raw(instruction)
            
            return retval
            
                
                
        f.__doc__ = self.description
        
    def pre_save(self):
        print self.command_type
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
    
    def __unicode__(self):
        return self.name
        
    def post_init(self):
       self.load_instrument()
        
    def load_instrument(self):
         print self.name
    
    