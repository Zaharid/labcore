# -*- coding: utf-8 -*-
"""
Created on Thu May  1 02:21:26 2014

@author: zah
"""
import unittest
from labcore.iobjects.models import (IOGraph, IONode, Link, IOSimple, Input,
                                     Output,iobject, IObject)
from labcore.iobjects.tests.base import BaseTest



class TestIODecorator(BaseTest):
    
    def test_decorator(self):
        @iobject
        def f(a,b):
            return a+b
        self.assertEqual(f(2,3),5)
        node = IONode(iobject = f)
        self.assertEqual(node.run(a=8,b=1)['output'],9)
        node.save()
        del node
        newnode = IONode.find_one()
        self.assertEqual(newnode.run(a=3,b=1)['output'],4)
        
        
if __name__ == '__main__':
    unittest.TestLoader().loadTestsFromTestCase(TestIODecorator).debug()