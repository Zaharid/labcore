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
                                    default = 'A')
    
    
    
    description = models.TextField(default = "", blank = True)
    
    
    def get_params(self):
        f = Formatter()
        tokens = f.parse(self.command_string)
        for (_ , param_name, _ , _) in tokens:
            if param_name is not None:
                param = Parameter(name = param_name, command = self)
                param.save()
                
    
    def post_save(self):
        self.get_params()
    
    
    def __call__(self, instrument, parameters):
        pass
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
    
    