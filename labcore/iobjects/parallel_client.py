# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 16:45:11 2014

@author: zah
"""
from IPython.parallel import Client

client = None
view = None

client_map = {'instruments':0, 'server':1, 'local':2}

def targets(key):
    return [client_map[key]]


def load_client():
    global client, view
    client = Client()
    view = client.load_balanced_view()
    client.block = False
    client[:].use_dill()
    
