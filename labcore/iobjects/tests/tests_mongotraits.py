# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:26:40 2014

@author: zah
"""
import nose
import unittest

from labcore.iobjects.tests.common import Doc, EmbDoc,Partner
from labcore.iobjects.tests.base import MongoTest

class Test_base(MongoTest):
    def test_bassic(self):
        refs = [EmbDoc(name = i) for i in "xyzt"]
        t = Doc()
        t.refs = refs
        assert(refs[0].id is not None)
        x = Partner(name = "p")
        x.ref = refs[3]
        t.partner = x
        assert(t.partner.ref.id == refs[3].id)
        t.save()
        self.assertTrue(Doc.objects.all()[0].id == t.id)
        del(t)
        t2 = Doc.objects.all()[0]
        self.assertTrue(t2.partner.ref.id == refs[3].id)

    def test_traits(self):
        doc = Doc()

        def ns(): pass
        ns.x = None
        def fchanged():
            ns.x = 'OK'
        doc.on_trait_change(fchanged ,name = 'f')
        self.assertIsNone(ns.x)
        doc.f = True
        self.assertEqual(ns.x, 'OK')

    def test_init(self):
        embdoc = EmbDoc()
        p = Partner(ref = embdoc)
        self.assertTrue(p.ref is embdoc)

if __name__ == '__main__':
    unittest.TestLoader().loadTestsFromTestCase(Test_base).debug()