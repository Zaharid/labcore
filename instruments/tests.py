# -*- coding: utf-8 -*-

from instruments.models import Command
from instruments.device_adapters import TestDevice
from django.test import TestCase

class CommandTestCase(TestCase):
    def setUp(self):
        Command.objects.create(name = "c#test", command_string = "xxx {p1}, {p2}",
                               description = "Be good")
    def test_params_managed(self):
        c = Command.objects.get(name="c#test")
        self.assertEqual(c.parameter_set.count(),2)
        
        
        p1 = c.parameters["p1"]
        p1.default_value = u'5'
        p1.save()
        c.command_string = "yyy {p1} {p3} {p5}"
        c.save()
        
        self.assertEqual(c.parameter_set.get(name = 'p1').default_value, '5')
        self.assertEqual(c.parameter_set.count(),3)
    
    
        
    def test_callable_help(self):
        c = Command.objects.get(name="c#test")
        def ins():pass
        ins.device = TestDevice()
        f  =  c.make_callable(ins)
        doclines =  f.__doc__.split('\n')
        self.assertEqual(doclines[0], c.description)
        self.assertEqual(doclines[2], c.command_string)
    
    def tearDown(self):
        print "Tear Down"
        Command.objects.get(name = "c#test").delete()
        