# -*- coding: utf-8 -*-
from django.test import TestCase

from instruments  import device_comm
from instruments.models import BaseInstrument, Instrument, Command, Parameter


class TestModelLogic(TestCase):
    def setUp(self):
        device_comm.test_mode()
        self.base = BaseInstrument.objects.create(name = "Base Instrument")
        
        self.ins = Instrument.objects.create(name = "My Instrument",
                              base_instrument = self.base
                              ,device_id = "TEST DEVICE")
    
    def test_command_propagation(self):
        
        
        #print "ins base instrument is %s" % self.ins.base_instrument
        desc = "Description c0"
        self.base.create_command(name = "c0", command_string = "c0?",
                                 description = desc)
        #reloaded_ins = Instrument.objects.get(pk = self.ins.pk)
        self.ins.prepare()
        self.assertEqual(self.ins.c0(), 'c0?')
        cdesc = self.ins.commands.get(name = "c0").description
        self.assertEqual(cdesc, desc)
        
        self.ins.create_command(name = "c1", command_string = "c2cs")

        reloaded_base = BaseInstrument.objects.get(pk = self.base.pk)
        c1 = reloaded_base.commands.get(name = "c1")
        self.assertEqual(c1.command_string, "c2cs")
    
    def test_command_execution(self):
         self.base.create_command(name = 'c0', 
                 command_string = "query c0 {param1} {param2}?",
                 description = "My base command description")
                 
         self.base.create_command(name = 'c1', 
                 command_string = "query c1 {p1} {p2}?",
                 description = "My other command desc.")
        
         
         
         self.base.save()        
         ins2 = Instrument.objects.create(name = "I2", 
                     base_instrument = self.base ,device_id = "TEST DEVICE 2")
                     
        
         ins2.prepare()
         
         ins2.create_command(name = 'c2', 
                 command_string = "query c2 {x1} {x2} {x3}?",
                 description = "3 params!")
         
         self.assertEqual(ins2.c0('1','2'), "query c0 1 2?")
         
         self.assertEqual(ins2.c1(p1 = 0, p2 = 2), "query c1 0 2?")
         
         self.assertRaises(TypeError, ins2.c1(p1 = 0, p2 = 2))
         
         self.assertEqual(ins2.c2(x1 = 2, x2 = 4, x3 = 8),
                          "query c2 2 4 8?")
         
                 
         c2_ins2 = ins2.commands.get(name = "c2")
         c2_base = self.base.commands.get(name = "c2")
         self.assertEqual(c2_ins2.description, c2_base.private_description)
        
    
        
    def test_load(self):
        self.ins.prepare("PRODUCT 0")
    
    def test_default_values(self):
        self.ins.prepare("PRODUCT 0")
        self.ins.create_command(name = "cdef", 
                                command_string = "{p0} {pdef}?",
                                defaults = {'pdef':'xx'})
        self.assertEqual(self.ins.cdef(0), "0 xx?")
    
    def tearDown(self):
        Instrument.objects.all().delete()
        BaseInstrument.objects.all().delete()
        
#==============================================================================
# 
# class CommandTestCase(TestCase):
#     def setUp(self):
#         Command.objects.create(name = "c#test", command_string = "xxx {p1}, {p2}?",
#                                description = "Be good")
#     def test_params_managed(self):
#         c = Command.objects.get(name="c#test")
#         self.assertEqual(c.parameter_set.count(),2)
#         
#         
#         p1 = c.parameters["p1"]
#         p1.default_value = u'5'
#         p1.save()
#         c.command_string = "yyy {p1} {p3} {p5}"
#         c.save()
#         
#         self.assertEqual(c.parameter_set.get(name = 'p1').default_value, '5')
#         self.assertEqual(c.parameter_set.count(),3)
#     
#     
#         
#     def test_callable(self):
#         c = Command.objects.get(name="c#test")
#         p = c.parameters['p2']
#         p.default_value = 'C'
#         p.save()
#         c.save()
#         
#         def ins():pass
#         ins.device = TestDevice()
#         
#         
#         f  =  c.make_callable(ins)
#         doclines =  f.__doc__.split('\n')
#         self.assertEqual(doclines[0], c.description)
#         self.assertEqual(doclines[2], c.command_string)
#         self.assertEqual(f("A", "B"), "xxx A, B?")
#         self.assertEqual(f("A"), "xxx A, C?")
#     
#     def tearDown(self):
#         Command.objects.get(name = "c#test").delete()
#         
# class InstrumentTestcase(TestCase):
#     def setUp(self):
#         instr = Instrument.objects.create(name = "test_instrument")
#         c = Command.objects.create(name = "my command",
#             command_string = "p1: {p1}; p2:{p2}?", 
#             description = "My test command")
#         c.save()
#                     
#         
#         instr.save()
#     
#     def test_command_callable(self):
#         instr = Instrument.objects.get(name = "test_instrument")
#         c = Command.objects.get(name = "my command")
#         instr.add_command(c)
#         
#         self.assertTrue(hasattr(instr, 'my_command'))
#         self.assertEqual(instr.my_command(p1='A', p2= 'B'), "p1: A; p2:B?")
#         
#         c2 = c = Command.objects.create(name = "second command",
#             command_string = "p3: {p3}; p4:{p4}?", 
#             description = "My other command")
#         instr.add_command(c2)
#         self.assertEqual(instr.second_command('C', 'D'), "p3: C; p4:D?")
#         
#         instr.create_command(name = "c3", command_string = "-", 
#                              description = "desc")
#         c3 = instr.commands.get(name = 'c3')
#==============================================================================
# #==============================================================================
#         doclines =  instr.c3.__doc__.split('\n')
#         self.assertEqual(doclines[0], c3.description)
#         
#==============================================================================
