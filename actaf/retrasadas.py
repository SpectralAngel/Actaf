# !/usr/bin/env python
# -*- coding: utf8 -*-
#
# retrasada.py
#
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

import model
import database


class Retrasada(object):
    def __init__(self, afiliado, anio, mes):

        self.afiliado = afiliado
        self.anio = anio
        self.mes = mes

    def list(self):

        return [self.afiliado, self.anio, self.mes]

    def crear_extra(self):

        if self.anio is None or self.mes is None:
            return

        obligaciones = None
        cuenta = None
        try:
            cuenta = model.CuentaRetrasada.selectBy(mes=self.mes,
                                                    anio=self.anio).getOne()
            obligaciones = model.Obligation.selectBy(month=self.mes,
                                                     year=self.anio)
        except:
            print self.anio, self.mes

        # TA
        if obligaciones is None:
            print self.anio, self.mes
            return

        obligacion = sum(o.amount for o in obligaciones)

        kw = dict()

        # Version para TurboAffiliate
        kw['account'] = cuenta.account
        kw['amount'] = obligacion
        kw['retrasada'] = True
        kw['months'] = 1
        kw['affiliate'] = self.afiliado
        kw['mes'] = self.mes
        kw['anio'] = self.anio

        model.Extra(**kw)


def crear_retrasada(afiliado):
    cuota = afiliado.get_delayed()
    if cuota is None:
        return Retrasada(afiliado, None, None)

    mes = cuota.delayed()
    anio = cuota.year

    return Retrasada(afiliado, anio, mes)


def procesar_retrasadas(cotizacion):
    # version para TurboAffiliate
    afiliados = database.get_affiliates_by_payment(cotizacion, True)

    return map(crear_retrasada, afiliados)


if __name__ == '__main__':

    try:
        import psyco

        psyco.full()
    except ImportError:
        pass

    creacion = Retrasada.crear_extra
    print("Obteniendo Retrasadas")
    retrasadas = procesar_retrasadas(1)
    print("Creando extras")
    map(creacion, retrasadas)
    retrasadas = procesar_retrasadas(10)
    map(creacion, retrasadas)
    retrasadas = procesar_retrasadas(3)
    map(creacion, retrasadas)
