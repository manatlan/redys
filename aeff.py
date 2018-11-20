#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,sys,re

def test(*a):
    print()

import inspect
sig = inspect.signature(test)
ba = sig.bind(10, 20)
print(sig.parameters,ba.args)
#~ test(*ba.args, **ba.kwargs)
