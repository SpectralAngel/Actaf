#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# process.py
# Copyright 2009, 2010 by Carlos Flores <cafg10@gmail.com>
# This file is part of Actaf.
#
# Actaf is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Actaf is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Actaf.  If not, see <http://www.gnu.org/licenses/>.

from decimal import Decimal

import database
import core

def start(parser, dia, inprema=True, cotizacion='INPREMA'):
    
    """Inicia el proceso de actualización de las aportaciones utilizando la
    planilla recibida"""
    
    print "Iniciando proceso de Actualizacion, esto puede tardar mucho tiempo"
    
    accounts = dict()
    for account in database.get_accounts():
        
        accounts[account] = dict()
        accounts[account]['number'] = 0
        accounts[account]['amount'] = Decimal(0)
    
    updater = core.Actualizador(database.get_obligation(dia.year, dia.month, inprema),
                            accounts, dia)
    
    updater.registrar_cuenta(database.get_loan_account(), 'prestamo')
    updater.registrar_cuenta(database.get_cuota_account(), 'cuota')
    updater.registrar_cuenta(database.get_incomplete_account(), 'incomplete')
    updater.registrar_cuenta(database.get_exceding_account(), 'excedente')
    
    # Cambiar por un par de acciones que muestren progreso
    for income in parser.parse():
        updater.update(income)
    
    reporte = None
    if inprema:
        reporte = database.create_other_report(accounts, dia.year, dia.month, cotizacion)
    else:
        reporte = database.create_report(accounts, dia.year, dia.month)
    
    print "Proceso de actualización Exitoso!"
    
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

    parser = core.AnalizadorINPREMA(archivo, afiliados)

    reporte = start(parser, fecha)
    
    return reporte
