#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# process.py
# This file is part of TaMan
#
# Copyright (C) 2009 - Carlos Flores
#
# TaMan is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# TaMan is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TaMan; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, 
# Boston, MA  02110-1301  USA

from decimal import Decimal

import database
import core
from model import *

def start(parser, dia, escalafon=False, cotizacion='INPREMA'):
	
	"""Inicia el proceso de actualización de las aportaciones utilizando la
	planilla recibida"""
	
	accounts = dict()
	for account in database.get_accounts():
		
		accounts[account] = dict()
		accounts[account]['number'] = 0
		accounts[account]['amount'] = Decimal(0)
	
	updater = core.Updater(database.get_obligation(dia.year, dia.month, escalafon),
							accounts, dia)
	
	updater.register_account(database.get_loan_account(), 'loan')
	updater.register_account(database.get_cuota_account(), 'cuota')
	updater.register_account(database.get_incomplete_account(), 'incomplete')
	updater.register_account(database.get_exceding_account(), 'exceding')
	
	# Cambiar por un par de acciones que muestren progreso
	for income in parser.parse():
		updater.update(income)
	
	reporte = None
	if escalafon == False:
		reporte = database.create_other_report(accounts, dia.year, dia.month, cotizacion)
	else:
		reporte = database.create_report(accounts, dia.year, dia.month)
	
	return reporte

def inprema(archivo, fecha):
	
	"""Incializa la actualización de las aportaciones mediante la planilla de
	INPREMA"""
	
	affiliates = database.get_affiliates_by_payment("INPREMA", True)
	afiliados = dict()

	for a in affiliates:
	
		inprema = None
		try:
			inprema = int(a.escalafon)
		except Exception, e:
			print e.message
	
		afiliados[inprema] = a

	parser = core.ParserINPREMA(archivo, afiliados)

	reporte = start(parser, fecha)

