#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# comasol.py
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

import database
from multiprocessing import Pool
import argparse
from datetime import datetime


def revertir(afiliado, day):
    print("Revirtiendo {0}".format(afiliado.id))

    for loan in afiliado.loans:

        for pay in loan.pays:

            if pay.day == day and pay.receipt == 'Planilla':
                print("Revirtiendo pago {0}".format(pay.id))
                pay.revert()
                loan.reconstruirSaldo()

    for deduced in afiliado.deduccionesBancarias:
        print(
        "Revisando deduccion {0} {1} {2}".format(deduced.id, deduced.month,
                                                 deduced.year))
        if deduced.year == day.year and deduced.month == day.month:
            print("Revirtiendo deduccion {0}".format(deduced.id))
            if deduced.account.id == 1:
                afiliado.remove_cuota(day.year, day.month)
            deduced.destroySelf()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("fecha",
                        help=u"Fecha en que se efectuaronn los pagos a revertir")
    parser.add_argument("banco", help=u"Banco de los cobros a revertir")
    args = parser.parse_args()

    fecha = datetime.strptime(args.fecha, "%Y%m%d").date()
    banco = database.Banco.get(int(args.banco))

    afiliados = database.get_affiliates_by_banco(banco, 1, True)

    for afiliado in afiliados:
        revertir(afiliado, fecha)
