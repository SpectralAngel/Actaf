# -*- coding: utf8 -*-
#
# process.py
# Copyright 2009 - 2013 by Carlos Flores <cafg10@gmail.com>
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
from datetime import datetime

import database
import core
import argparse

def start(parser, dia, inprema=True, cotizacion=2):
    
    """Inicia el proceso de actualización de las aportaciones utilizando la
    planilla recibida"""
    
    print("Iniciando proceso de Actualizacion, esto puede tardar mucho tiempo")
    
    accounts = dict()
    for account in database.get_accounts():
        
        accounts[account] = dict()
        accounts[account]['number'] = 0
        accounts[account]['amount'] = Decimal(0)
    
    updater = core.Actualizador(database.get_obligation(dia.year, dia.month,
                                                        inprema), accounts, dia)
    
    updater.registrar_cuenta(database.get_loan_account(), 'prestamo')
    updater.registrar_cuenta(database.get_cuota_account(), 'cuota')
    updater.registrar_cuenta(database.get_incomplete_account(), 'incomplete')
    updater.registrar_cuenta(database.get_exceding_account(), 'excedente')
    
    # Cambiar por un par de acciones que muestren progreso
    parsed = parser.parse()
    map((lambda i: updater.update(i)), parsed)
    
    reporte = None
    if inprema:
        reporte = database.create_other_report(accounts, dia.year, dia.month,
                                               cotizacion)
    else:
        reporte = database.create_report(accounts, dia.year, dia.month)
    
    print("Proceso de actualización Exitoso!")
    
    return reporte

def inprema(archivo, fecha):
    
    """Incializa la actualización de las aportaciones mediante la planilla de
    INPREMA"""
    
    affiliates = database.get_affiliates_by_payment(2, True)
    print(affiliates.count())
    afiliados = dict()
    
    for a in affiliates:
        
        inprema = None
        try:
            inprema = int(a.escalafon)
        except Exception, e:
            print("Error en afiliado {0}: {1}".format(a.id, e.message))
        afiliados[inprema] = a
    
    parser = core.AnalizadorINPREMA(archivo, afiliados)
    
    reporte = start(parser, fecha)
    
    return reporte

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("fecha",
                        help=u"Fecha en que se efectuarán los cobros")
    args = parser.parse_args()
    fecha = datetime.strptime(args.fecha, "%Y%m%d").date()
    
    inprema("inprema.csv", fecha)
