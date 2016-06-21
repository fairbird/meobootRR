#!/usr/bin/python 

import sys, meoboot

if len(sys.argv) < 3:
	pass
else:
	meoboot.MeobootMainEx(sys.argv[1], sys.argv[2], sys.argv[3])

