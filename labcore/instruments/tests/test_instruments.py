# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 21:06:04 2014

@author: zah
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Mar  8 21:58:59 2014

@author: zah
"""
import unittest
from labcore.mongotraits.tests.base import BaseTest
from labcore.instruments import device_comm
from labcore.instruments.models import BaseInstrument, Instrument




class Test_base(BaseTest):
    def setUp(self):
        super(Test_base, self).setUp()
        device_comm.test_mode()
        self.base = BaseInstrument(name = "Base Instrument")

        self.ins = Instrument(name = "My Instrument",
                              base_instrument = self.base
                              ,device_id = "TEST DEVICE")
        self.base.save()
        self.ins.save()

    def test_command_propagation(self):

        #print "ins base instrument is %s" % self.ins.base_instrument
        desc = "Description c0"
        self.base.create_command(name = "c0", command_string = "c0?",
                                 description = desc)
        #reloaded_ins = Instrument.objects.get(pk = self.ins.pk)
        self.ins.prepare()
        self.assertEqual(self.ins.c0(), 'c0?')
        cdesc = self.ins._command_names['c0'].description
        self.assertEqual(cdesc, desc)

        self.ins.create_command(name = "c1", command_string = "c2cs")

        self.base.refresh()
        c1 = self.base._command_names["c1"]
        self.assertEqual(c1.command_string, "c2cs")

    def test_command_execution(self):
         self.base.create_command(name = 'c0',
                 command_string = "query c0 {param1} {param2}?",
                 description = "My base command description")

         self.base.create_command(name = 'c1',
                 command_string = "query c1 {p1} {p2}?",
                 description = "My other command desc.")



         self.base.save()
         ins2 = Instrument(name = "I2",
                     base_instrument = self.base ,device_id = "TEST DEVICE 2")


         ins2.save()
         ins2.prepare()

         ins2.create_command(name = 'c2',
                 command_string = "query c2 {x1} {x2} {x3}?",
                 description = "3 params!")

         self.assertEqual(ins2.c0('1','2'), "query c0 1 2?")

         self.assertEqual(ins2.c1(p1 = 0, p2 = 2), "query c1 0 2?")

         self.assertRaises(TypeError, ins2.c1(p1 = 0, p2 = 2))

         self.assertEqual(ins2.c2(x1 = 2, x2 = 4, x3 = 8),
                          "query c2 2 4 8?")


         c2_ins2 = ins2._command_names["c2"]
         c2_base = self.base._command_names["c2"]
         self.assertEqual(c2_ins2.description, c2_base.private_description)



    def test_load(self):
        self.ins.prepare("PRODUCT 0")

    def test_default_values(self):
        self.ins.prepare("PRODUCT 0")
        self.ins.create_command(name = "cdef",
                                command_string = "{p0} {pdef} {spdef}?",
                                defaults = {'pdef':'xx', 'spdef':'yy'})
        self.assertEqual(self.ins.cdef(0), "0 xx yy?")
        self.assertEqual(self.ins.cdef(0, spdef = 'jj'), "0 xx jj?")
        self.assertEqual(self.ins.cdef(0, spdef = 'jj', pdef = ''), "0  jj?")
        self.assertEqual(self.ins.cdef(0, 1 , 2), "0 1 2?")

    def test_commad_access(self):
        self.ins.prepare("PRODUCT 0")
        self.ins.create_command(name = "cdef",
                                command_string = "{p0} {pdef} {spdef}?",
                                defaults = {'pdef':'xx', 'spdef':'yy'})
        self.ins.cdef.command.command_string = "xx"
        self.ins.cdef.command.save()
        self.ins.make_interface()
        self.assertEqual(self.ins.cdef(), 'xx')
        self.assertFalse(self.ins.cdef.command.inputs)



if __name__ == '__main__':
    unittest.TestLoader().loadTestsFromTestCase(Test_base).debug()