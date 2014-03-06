# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 16:49:39 2014

@author: zah
"""
import unittest
from collections import Counter

from labcore.iobjects.models import (IOGraph, IONode, Link, IOSimple, Input,
                                     Output,)
from labcore.iobjects.tests.base import MongoTest

class Test_base(MongoTest):

    def setUp(self):
        super(Test_base, self).setUp()
        g =  IOGraph()
        ions = []
        for i in range(5):
            io = IOSimple(name = "io%d"%i)
            i1 = Input(name = "i1")
            i2 = Input(name = "i2")
            o1 = Output(name = "o1")
            o2 = Output(name = "o2")
            io.inputs = [i1,i2]
            io.outputs = [o1,o2]
            io.save()
            ion = IONode(io)
            ions += [ion]
            ion.save()

        g.nodes = ions
        g.bind( ions[0], 'o1', ions[1], 'i1')
        g.bind( ions[1], 'o1', ions[2], 'i1')
        g.bind( ions[1], 'o2', ions[3], 'i2')
        g.bind( ions[3], 'o2', ions[4], 'i2')
        g.bind( ions[2], 'o1', ions[4], 'i1')

        g.save()
        for ion in ions: ion.save()
        self.g = g
        self.ions = ions

    def test_update_iobject(self):
        g = IOGraph.objects.all()[0]
        print list(g.links)[0].fr



    def test_free(self):
        g = self.g
        ions = self.ions
        self.assertEqual(Counter(ions[0].inputs),Counter(ions[0].free_inputs))
        self.assertEqual(Counter(ions[4].outputs),Counter(ions[4].free_outputs))
        self.assertFalse(list(ions[4].free_inputs))


    def test_binding(self):
        g = self.g
        ions = self.ions
        self.assertEqual(len(list(g.links)), 5)
        #Needs to copy the list as can't delete while iterating.
        for link in list(g.links):
            g.remove_link(link)
            del(link)

        self.assertEqual(g.build_graph().edges(),[])
        g.bind( ions[2], 'o1', ions[0], 'i1')

        self.assertRaises(ValueError,g.bind,ions[0], 'o1', ions[2], 'i1')
        g.unbind( ions[2], 'o1', ions[0], 'i1')

        self.assertEqual(g.build_graph().edges(),[])



if __name__ == '__main__':
    unittest.TestLoader().loadTestsFromTestCase(Test_base).debug()