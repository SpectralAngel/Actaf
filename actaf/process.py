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
import argparse
from sqlobject import sqlhub

import database
import core


def start(parser, dia, inprema=True, cotizacion=2):
    """Inicia el proceso de actualización de las aportaciones utilizando la
    planilla recibida"""

    print(u"Iniciando proceso de Actualizacion, esto puede tardar mucho tiempo")

    accounts = {}
    for account in database.get_accounts():
        accounts[account] = {'number': 0, 'amount': Decimal()}

    updater = core.Actualizador(database.get_obligation(dia.year, dia.month,
                                                        inprema), accounts, dia)

    updater.registrar_cuenta(database.get_loan_account(), 'prestamo')
    updater.registrar_cuenta(database.get_cuota_account(), 'cuota')
    updater.registrar_cuenta(database.get_incomplete_account(), 'incomplete')
    updater.registrar_cuenta(database.get_exceding_account(), 'excedente')

    # Cambiar por un par de acciones que muestren progreso
    parsed = parser.parse()

    conn = sqlhub.getConnection()
    transaction = conn.transaction()
    sqlhub.processConnection = transaction
    try:
        [updater.update(i, True) for i in parsed]
        transaction.commit()
    except Exception:
        transaction.rollback()
        transaction.begin()
        raise

    print(u"Proceso de actualización Exitoso!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fecha",
                        help=u"Fecha en que se efectuarán los cobros")
    parser.add_argument("archivo")
    args = parser.parse_args()
    fecha = datetime.strptime(args.fecha, "%Y%m%d").date()

    affiliates = database.get_affiliates_by_payment(2, True)

    print(affiliates.count())

    parser = core.AnalizadorCSV(args.archivo, affiliates)

    start(parser, fecha)
