#!/usr/bin/python
# -*- coding: utf8 -*-

import database
import core
from model import *

def extraer_cambios():
	
	affiliates = database.get_affiliates_by_payment('INPREMA')
	afiliados = dict()
	
	for a in affiliates:
	
		inprema = None
		try: inprema = int(a.escalafon)
		except Exception, e: pass
		
		afiliados[inprema] = a
	
	obligacion = database.get_obligation(10, 2009, True)
	obligacion = 228
	print obligacion
	cambios = dict()
	for afiliado in afiliados: cambios[afiliado] = afiliados[afiliado].get_monthly() + obligacion
	
	parser = parser = core.ParserINPREMA('inprema.csv', afiliados)
	
	for income in parser.parse():
		try:
			if income.amount == cambios[int(income.affiliate.escalafon)]:
			
				del cambios[int(income.affiliate.escalafon)]
		
		except Exception, e:
			print "%s %s" % (income.affiliate.escalafon, type(income.affiliate.escalafon))
	
	for numero in cambios: print "%s %s" % (numero, cambios[numero])
	print len(cambios)

if __name__ == "__main__":
	
	extraer_cambios()

