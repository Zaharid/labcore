# -*- coding: utf-8 -*-
from collections import OrderedDict
from string import Formatter

from labcore.mongotraits import documents
from IPython.utils import traitlets as t
from labcore.iobjects import models as iobjs
#==============================================================================
#
# from django.db import models
# from django.contrib.contenttypes.models import ContentType
# from django.contrib.contenttypes import generic
#
# from django.core.exceptions import ObjectDoesNotExist
#==============================================================================
#from django.db.models import signals

from labcore.utils import make_signature


import utils
import device_comm
from errors import InstrumentError
# Create your models here.


COMMAND_TYPES = (
    ("Write"),
    ("Ask"),
    ("Ask Raw"),

)



class AbstractInstrument(documents.Document):
    """This class holds the common methods of BaseInstrument and Instrument."""


    #id = models.AutoField(primary_key=True)
    name = t.Unicode()
#    base_instrument = models.ForeignKey('BaseInstrument',
#                                        null = True, blank = True)
    base_instrument = documents.Reference(__name__+'.BaseInstrument')
    #commands = generic.GenericRelation('Command')
    commands = t.List(documents.Reference(__name__+'.Command'))

    @property
    def _command_names(self):
        return {command.name : command for command in self.commands}

    def add_command(self, command):
        """Sets the instrument of **command** to the instrument and saves
        it."""
        command.instrument = self
        self.commands = self.commands + [command,]

        self.save()
        command.save()

    def create_command(self, *args, **kwargs):
        """High level method for adding a command to an instrument.

        ***args** and ***kwawgs** are passed to the **Command** constructor."""
        c = Command(*args, **kwargs)
        self.add_command(c)

    def load_from_base(self):
        """Pulls the commands from the base of this instrument and saves
        them."""
        #print self
        #print self.base_instrument
        if self.base_instrument:
            #print "Adding commands"
            for command in self.base_instrument.commands:
                if not command.name in self._command_names:
                   newcommand = Command(
                            name = command.name,
                            command_string = command.command_string,
                            command_type = command.command_type,
                            instrument = self)
                   self.commands = self.commands + [command,]
                   newcommand.save()




    def __unicode__(self):
        return self.name

#@utils.autoconnect
class BaseInstrument(AbstractInstrument):
    def save(self, *args, **kwargs):
        super(BaseInstrument, self).save(*args, **kwargs)
        self.load_from_base()

#@utils.autoconnect
class Instrument(AbstractInstrument):


    device_id = t.Unicode()

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
        allcommands = self.commands
        for command in allcommands:
            self.make_command_function(command)

    def save(self, *args, **kwargs):
        super(Instrument, self).save(*args, **kwargs)
        self.load_from_base()


#==============================================================================
#     def post_init(self, **kwargs):
#         try:
#             self.prepare()
#         except InstrumentError:
#             pass
#==============================================================================



    def associate(self, device):
        if self.device_id and self.device_id != device.model:
            raise ValueError("""Instrument already has the device id %s.
                Cannot associate with %s"""%(self.device_id, device.model))

        self.device_id = device.model
        self.device = device
        self.save()
        device.is_controlled = True
        self.make_interface()
        #self.prepare()

    def load_device(self, product_id = None):

        allins = device_comm.find_all()

        if self.device_id in allins:
            if product_id is None:
                devobj = device_comm.next_not_controlled(self.device_id)
            else:
                devobj = device_comm.get_device(self.device_id, product_id)
            if not devobj:
                return False

            self.associate(devobj.device)
            return True
        else:
            return False

    def prepare(self, product_id = None):
        """Loads the instrument device and any new commands from the base.

        Use this to make the instrument operational after loading it from the
        db."""
        if self.load_device(product_id = product_id) and self.indb:
            self.load_from_base()
        else:
           raise InstrumentError("Cannot prepare device."
               "Save it to the DB first and ensure a compatible instrument "
               "is connected.")



#TODO:Processors.
#@utils.autoconnect
class Command(iobjs.IObject):
    command_string = t.Unicode()

    command_type = t.Enum(values = COMMAND_TYPES)

    private_description = t.Unicode()


    @property
    def base_command(self):
        if self._base_command:
            return self._base_command
        bins = self.instrument.base_instrument
        if bins:
            try:
                self._base_command = bins._command_names[self.name]
                return self._base_command
            except  KeyError:
                return None
        return None


    #content_type = models.ForeignKey(ContentType)
    #object_id = models.PositiveIntegerField()
    #instrument = generic.GenericForeignKey()
    instrument = documents.Reference(AbstractInstrument)


    @property
    def description(self):
        if self._description:
            return self._description
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

    def __init__(self, *args ,**kwargs):
        self._base_command = None
        self._description = kwargs.pop('description', None)
        self._defaults = kwargs.pop('defaults', {})
        super(Command, self).__init__(*args, **kwargs)


    def save_params(self):
        f = Formatter()
        tokens = f.parse(self.command_string)

        params = []
        for (_ , param_name, _ , _) in tokens:
            if param_name is not None:
                if param_name in self.inputdict:
                    param = self.inputdict[param_name]
                else:
                    param = iobjs.Input(name=param_name)
                if param_name in self._defaults:
                    param.default = self._defaults[param_name]
                params += [param]
        self.inputs = params


    def make_callable(self, instrument):

        params = self.inputs
        argnames = []
        allnames = []
        kwargdefaults = OrderedDict()
        for param in params:
            if param.default is not None:
                kwargdefaults[param.name] = param.default
            else:
                argnames += [param.name]
            allnames += [param.name]

        ct = self.command_type
        if ct == "Write":
            instrf = instrument.device.write
        elif ct == "Ask":
            instrf = instrument.device.ask
        elif ct == "Ask Raw":
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
        f.command = self
        return make_signature(f, argnames, kwargdefaults)


    def pre_save(self):
        if not self.command_type:
            if self.command_string.endswith('?'):
                self.command_type = "Ask"
            else:
                self.command_type = "Write"
        self.make_base()
        if self._description is not None:
            self.description = self._description

    def make_base(self):
        bins = self.instrument.base_instrument
        if bins and not self.name in bins._command_names:
            newcommand = Command(
                            name = self.name,
                            command_string = self.command_string,
                            command_type = self.command_type)

            bins.add_command(newcommand)

    def post_save(self):
        self.save_params()
        if self.base_command:
            self.base_command.save()

    def save(self, *args ,**kwargs):
        self.pre_save()
        super(Command,self).save(*args, **kwargs)
        self.post_save()

    def __unicode__(self):
        return self.name
