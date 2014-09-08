#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# comasol.py
#
# Copyright 2014 by Carlos Flores <cafg10@gmail.com>
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
import argparse
from datetime import datetime

account = database.get_inprema_account()


def revertir(afiliado, day):
    #print("Revirtiendo afiliado {0}".format(afiliado.id))

    for loan in afiliado.loans:

        for pay in loan.pays:

            if pay.day == day and pay.receipt == 'Planilla' and pay.amount == Decimal('178.68'):
                print("Revirtiendo pago {0}".format(pay.id))
                pay.revert()
                loan.reconstruirSaldo()

    for deduced in afiliado.deduccionesBancarias:
        if deduced.year == day.year and deduced.month == day.month and deduced.amount == Decimal('178.68'):
            print(
                "Revisando deduccion {0} {1} {2}".format(deduced.id,
                                                         deduced.month,
                                                         deduced.year))
            print("Revirtiendo deduccion {0}".format(deduced.id))
            deduced.account = account


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("fecha",
                        help=u"Fecha en que se efectuaronn los pagos a revertir")
    parser.add_argument("banco", help=u"Banco de los cobros a revertir")
    args = parser.parse_args()

    fecha = datetime.strptime(args.fecha, "%Y%m%d").date()
    banco = database.Banco.get(int(args.banco))

    afiliados = database.get_affiliates_by_banco(banco, True)

    for a in afiliados:
        revertir(a, fecha)
