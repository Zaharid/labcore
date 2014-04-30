# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 13:55:58 2014

@author: zah
"""

import unittest

from labcore.mongotraits.tests.base import BaseTest

from labcore.reporttools import Result, Report

class Test(BaseTest):
    def setUp(self):
        super(Test, self).setUp()
        r1 = Result(value = 33, title = "Result for R1", smalltitle = "r1")
        r2 = Result(value = "patata", title = "Result for R2", smalltitle = "r2")
        r3 = Result(value = "32", title = "Result for R3", smalltitle = "r3")
        self.results = [r1,r2,r3]
        self.rep = Report(title = "my report", results = self.results)
    def test_open(self):
        self.rep.make_report('/tmp')



if __name__ == '__main__':
    unittest.TestLoader().loadTestsFromTestCase(Test).debug()