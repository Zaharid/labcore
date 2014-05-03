# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 16:49:39 2014

@author: zah
"""
import unittest
from collections import Counter

from labcore.mongotraits import Q

from labcore.iobjects.models import (IOGraph, IONode, Link, IOSimple, Input,
                                     Output,)
from labcore.iobjects.tests.base import BaseTest

class Test_base(BaseTest):

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
            #io.save()
            ion = IONode(io)
            ions += [ion]

        g.nodes = ions
        g.bind( ions[0], 'o1', ions[1], 'i1')
        g.bind( ions[1], 'o1', ions[2], 'i1')
        g.bind( ions[1], 'o2', ions[3], 'i2')
        g.bind( ions[3], 'o2', ions[4], 'i2')
        g.bind( ions[2], 'o1', ions[4], 'i1')
        for ion in ions:
            ion.save()
        g.save()

        self.g = g
        self.ions = ions

#==============================================================================
#     def test_update_iobject(self):
#         io2 = IOSimple.find_one(Q(name  ='io2'))
#         print ("IO2 inputs: %r"%(io2.inputs,))
#         Input._idrefs.data ={}
#         Output._idrefs.data = {}
#         io2.inputs = ()
#         io2.outputs = ()
#         #io2.save()
#         #del io2
#         import pdb; pdb.set_trace()
#         g = next(IOGraph.find())
#         nd = g.nodes[2]
#         self.assertFalse(nd.inlinks)
#         self.assertFalse(nd.outlinks)
#==============================================================================

    def test_hash(self):
        for n1 in self.g.nodes:
            for n2 in self.g.nodes:
                self.assertTrue(not (n1==n2)^(hash(n1)==hash(n2)))

        for l1 in self.g.links:
            for l2 in self.g.links:
                self.assertFalse((l1 == l2) ^ (hash(l1)== hash(l2)))



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
    
    def h(a,b):
        return a-b
    
#==============================================================================
#     @iobject
#     def f(x,y):
#         return x+y
#==============================================================================
    
    def test_decorator(self):
        pass
        #self.assertEqual(self.f(2,2),4)



if __name__ == '__main__':
    unittest.TestLoader().loadTestsFromTestCase(Test_base).debug()