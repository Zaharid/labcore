# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 18:42:58 2014

@author: zah
"""

import models

i1 = models.Parameter(name = "i1")
i2 = models.Parameter(name = "i2")
o1 = models.Parameter(name = "o1")
o2 = models.Parameter(name = "o2")

io = models.IOSimple(name = "IO")
io.inputs = [i1,i2]
io.outputs = [o1,o2]

io.save()                