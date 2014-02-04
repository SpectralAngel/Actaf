# -*- coding: utf8 -*-
#
# cuenta.py
# Copyright 2013 by Carlos Flores <cafg10@gmail.com>
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

from datetime import datetime

import database
import argparse
import csv
from decimal import Decimal
from core import Ingreso
import parsers

def obtener_afiliado(afiliado):
    
    return database.get_affiliate(int(afiliado[0]))

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("fecha",
                        help=u"Fecha en que se efectuarán los cobros")
    parser.add_argument("archivo")
    parser.add_argument("banco")
    args = parser.parse_args()
    
    fecha = datetime.strptime(args.fecha, "%Y%m%d").date()
    banco = database.Banco.get(int(args.banco))
    archivo = args.archivo
    
    reader = csv.reader(open(archivo))
    li = database.get_affiliates_by_banco(banco)
    afiliados = dict()
    for a in li:
        afiliados[a.cuenta] = a
    perdidos = 0
    parsed = list()
    
    for row in reader:
        
        amount = Decimal(row[2].replace(',', ''))
        afiliado = None
        cuenta = row[0].replace('-', '')
        if not cuenta in afiliados:
            perdidos += 1
            print("Error de parseo no se encontro la cuenta {0}".format(cuenta))
        else:
            afiliado = afiliados[cuenta]
        if afiliado:
            parsed.append(Ingreso(afiliado, amount))
    
    accounts = dict()
    for account in database.get_accounts():
        
        accounts[account] = dict()
        accounts[account]['number'] = 0
        accounts[account]['amount'] = Decimal(0)
    
    updater = parsers.Actualizador(database.get_obligation(fecha.year, fecha.month),
                            accounts, fecha, banco)
    
    updater.registrar_cuenta(database.get_loan_account(), 'prestamo')
    updater.registrar_cuenta(database.get_cuota_account(), 'cuota')
    updater.registrar_cuenta(database.get_incomplete_account(), 'incomplete')
    updater.registrar_cuenta(database.get_exceding_account(), 'excedente')
    
    print("Iniciando Actualizacion")
    
    map((lambda i: updater.update(i)), parsed)
