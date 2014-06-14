# -*- coding: utf-8 -*-
from collections import OrderedDict
from string import Formatter

from IPython.utils import traitlets as t
from IPython.html import widgets
from labcore.iobjects import models as iobjs
from labcore.mongotraits import documents

from labcore.utils import make_signature
from labcore.widgets import widgetrepr

from labcore.instruments import utils
from labcore.instruments import device_comm
from labcore.instruments.errors import InstrumentError
# Create your models here.


COMMAND_TYPES = (
    ("Write"),
    ("Ask"),
    ("Ask Raw"),

)

def _find_bases():
    return OrderedDict((item.name, item) for item in BaseInstrument.find())


class AbstractInstrument(documents.Document):
    """This class holds the common methods of BaseInstrument and Instrument."""


    #id = models.AutoField(primary_key=True)
    name = t.Unicode(order = -1)
#    base_instrument = models.ForeignKey('BaseInstrument',
#                                        null = True, blank = True)
    base_instrument = documents.Reference(__name__+'.BaseInstrument',
                                          choose_from=_find_bases)
    #commands = generic.GenericRelation('Command')
    commands = t.List(documents.Reference(__name__+'.Command'))

    def __init__(self, *args, **kwargs):
        super(AbstractInstrument, self).__init__(*args, **kwargs)
        for command in self.commands:
            if command.instrument is None:
                command.instrument = self
            if command.instrument != self:
                raise InstrumentError("Command defined for another instrument.")

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


    def command_form(self, **kwargs):
        wr =  Command.AddCommandWR(Command, instrument = self,
                                   default_values = kwargs)
        wr.create_object()


    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.name
    class WidgetRepresentation(documents.Document.WidgetRepresentation):
        varname_map = 'name'
            



class BaseInstrument(AbstractInstrument):

    _class_tag = True

    def save(self, *args, **kwargs):
        super(BaseInstrument, self).save(*args, **kwargs)
        self.load_from_base()

class Instrument(AbstractInstrument):

    _class_tag = True

    device_id = t.Unicode()

    device = None

    #interface = models.ForeignKey(Interface)
    #commands = models.ManyToManyField(Command)

    def make_command_function(self, command):
        attrname = utils.normalize_name(command.name)
        commandcall = command.make_callable(self)
        setattr(self, attrname, commandcall)

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
class Command(iobjs.IObjectBase, documents.Document):
    command_string = t.Unicode()

    command_type = t.Enum(values = COMMAND_TYPES)

    private_description = t.Unicode(widget = widgets.TextareaWidget)

    instrument = documents.Reference(AbstractInstrument)

    def __init__(self, *args ,**kwargs):
        self._base_command = None
        self._description = kwargs.pop('description', None)
        self._defaults = kwargs.pop('defaults', {})
        super(Command, self).__init__(*args, **kwargs)


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
        if instrument.device:
            ct = self.command_type
            if ct == "Write":
                instrf = instrument.device.write
            elif ct == "Ask":
                instrf = instrument.device.ask
            elif ct == "Ask Raw":
                instrf = instrument.device.ask_raw
        else:
            raise InstrumentError("Needs to connect be connected \
                                    to a device on initialization.")
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

    def __str__(self):
        return self.name

    class WidgetRepresentation(widgetrepr.WidgetRepresentation):
        hidden_fields = ('imputs', 'outputs')

    class AddCommandWR(WidgetRepresentation):
        hidden_fields = ('inputs', 'outputs', 'instrument')
        def __init__(self, cls, instrument, *args, **kwargs):
            self.instrument = instrument
            super(Command.AddCommandWR, self).__init__(cls, *args,**kwargs)
        def new_object(self):
            values = self.read_form()
            command = Command(instrument = self.instrument, **values)
            if self.instrument is not None:
                self.instrument.add_command(command)
            return command

        def create_description(self):
            return "Add to %s" % self.instrument

