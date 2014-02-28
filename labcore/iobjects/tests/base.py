# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 14:12:46 2014

@author: zah
"""

import unittest
import mongoengine as mg
from mongoengine.connection import _get_db

class MongoTest(unittest.TestCase):
    def setUp(self):
        mg.connect('test')
        db = _get_db()
        db.connection.drop_database('test')
        
    def tearDown(self):
        db = _get_db()
        db.connection.drop_database('test')
        mg.connection.disconnect()