# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 18:42:58 2014

@author: zah
"""

import iobjects

i1 = iobjects.Parameter(name = "i1")
i2 = iobjects.Parameter(name = "i2")
o1 = iobjects.Parameter(name = "o1")
o2 = iobjects.Parameter(name = "o2")

io = iobjects.IObject(name = "IO")
io.inputs = [i1,i2]
io.outputs = [o1,o2]

io.save()                