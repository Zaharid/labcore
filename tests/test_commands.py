# -*- coding: utf-8 -*-

from instruments.models import Command
from django.test import TestCase

class CommandTestCase(TestCase):
    def setUp(self):
        Command.objects.create(name = "c#test", command_string = "xxx {p1}, {p2}",
                               description = "Be good")
    def test_params_managed(self):
        c = Command.objects.get(name="c#test")
        self.assertEqual(c.parameter_set.count(),2)
    def tearDown(self):
        Command.objects.get(name = "c#test").delete()
        