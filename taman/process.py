#!/usr/bin/env python
# -*- coding: utf8 -*-
# core.py
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

import database
import core
from decimal import Decimal
from model import *

scheme = 'mysql://root:gustavito@localhost/afiliados2?debug=1'
connection = connectionForURI(scheme)
sqlhub.processConnection = connection

def start(parser, dia, no_escalafon=False):
	
	accounts = dict()
	for account in database.get_accounts():
		
		accounts[account] = dict()
		accounts[account]['number'] = 0
		accounts[account]['amount'] = Decimal(0)
	
	updater = core.Updater(database.get_obligation(dia.year, dia.month),
							accounts, dia)
	
	updater.register_account(database.get_loan_account(), 'loan')
	updater.register_account(database.get_cuota_account(), 'cuota')
	updater.register_account(database.get_incomplete_account(), 'incomplete')
	updater.register_account(database.get_exceding_account(), 'exceding')
	
	# Cambiar por un par de acciones que muestren progreso
	for income in parser.parse():
		updater.update(income)
	
	reporte = None
	if no_escalafon == True: database.create_other_report(accounts, dia.year, dia.month, 'INPREMA')
	else: reporte = database.create_report(accounts, dia.year, dia.month)
	
	return reporte

