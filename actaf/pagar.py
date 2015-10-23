# !/usr/bin/env python
# -*- coding: utf8 -*-
#
# pagar.py
#
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

import argparse
from datetime import datetime
from decimal import Decimal

import database
import parsers

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("fecha",
                        help=u"Fecha en que se efectuarán los cobros")
    parser.add_argument("cobro")
    parser.add_argument("archivo")
    parser.add_argument("banco")
    args = parser.parse_args()

    fecha = datetime.strptime(args.fecha, "%Y%m%d").date()
    cobro = datetime.strptime(args.cobro, "%Y%m%d").date()
    banco = database.Banco.get(int(args.banco))
    archivo = args.archivo

    accounts = {}
    for account in database.get_accounts():
        accounts[account] = {'number': 0, 'amount': Decimal()}

    Parser = getattr(parsers, banco.parser)
    parser = Parser(fecha, archivo, banco)
    parsed = parser.output()

    updater = parsers.ActualizadorBancario(
        database.get_obligation(fecha.year, fecha.month),
        accounts, fecha, banco, cobro,
        database.get_compliment(fecha.year, fecha.month, True),
        database.get_compliment(fecha.year, fecha.month, False))

    updater.registrar_cuenta(database.get_loan_account(), 'prestamo')
    updater.registrar_cuenta(database.get_cuota_account(), 'cuota')
    updater.registrar_cuenta(database.get_incomplete_account(), 'incomplete')
    updater.registrar_cuenta(database.get_exceding_account(), 'excedente')
    updater.registrar_cuenta(database.get_inprema_account(), 'complemento')
    print(u"Actualizando {0}".format(banco.nombre))

    [updater.update(i, banco.cuota) for i in parsed]
