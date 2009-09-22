#!/usr/bin/env python
# -*- coding: utf-8 -*-

import database
from datetime import date
import process
import core
from model import *

if __name__ == '__main__':
	
	try:
		import psyco
		psyco.full()
	except ImportError:
		pass
	
	affiliates = database.get_affiliates_by_payment("INPREMA")
	afiliados = dict()
	
	for a in affiliates:
		
		inprema = None
		try:
			inprema = int(a.escalafon)
		except Exception, e:
			print e.message
		
		afiliados[inprema] = a
	
	print afiliados
	
	hoy = date.today()
	
	parser = core.ParserINPREMA(open('inprema.csv'), afiliados)
	
	reporte = process.start(parser, hoy, True)

