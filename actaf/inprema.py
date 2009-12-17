#!/usr/bin/python
# -*- coding: utf8 -*-

import csv
import database
import core

def extraer_cambios():
	
	affiliates = database.get_affiliates_by_payment('INPREMA')
	afiliados = dict()
	
	for a in affiliates:
	
		inprema = None
		try:
			inprema = int(a.escalafon)
		except Exception, e:
			pass
		
		afiliados[inprema] = a
	
	obligacion = database.get_obligation(12, 2009, True)
	obligacion = 228
	cambios = dict()
	for afiliado in afiliados:
		a = afiliados[afiliado]
		cambios[afiliado] = core.Extraccion(a, a.get_monthly() + obligacion)
		if not a.active:
			cambios[afiliado].cantidad = 0
			cambios[afiliado].marca = 'C'
	
	parser = core.ParserINPREMA('inprema.csv', afiliados)
	
	for income in parser.parse():
		try:
			if income.amount == cambios[int(income.affiliate.escalafon)].cantidad:
				del cambios[int(income.affiliate.escalafon)]
			elif income.amount != cambios[int(income.affiliate.escalafon)].cantidad:
				cambios[int(income.affiliate.escalafon)].marca = 'R'
		except Exception, e:
			print "%s %s" % (income.affiliate.escalafon, type(income.affiliate.escalafon))
	
	del cambios[None]
	
	dexter = csv.writer(open('dexter.csv', 'w'))
	
	for numero in cambios:
		print cambios[numero]
		dexter.writerow(cambios[numero].list())

if __name__ == "__main__":
	
	extraer_cambios()
