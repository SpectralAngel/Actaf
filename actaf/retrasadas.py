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
from datetime import date
from multiprocessing import Pool

import model
import database

years = {}


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

        kw = {'account': years[self.anio][self.mes]['cuenta'],
              'amount': years[self.anio][self.mes]['obligacion'],
              'retrasada': True, 'months': 1, 'affiliate': self.afiliado,
              'mes': self.mes, 'anio': self.anio}

        # Version para TurboAffiliate

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

    first_year = model.CuotaTable.select().min('year')
    current_year = date.today().year
    current_month = date.today().month

    obligaciones = None
    cuenta = None

    for n in range(first_year, current_year + 1):
        years[n] = {}
        for m in range(1, 13):
            if n == current_year and m >= current_month:
                break
            years[n][m] = {}

            try:
                years[n][m]['cuenta'] = model.CuentaRetrasada.selectBy(mes=m, anio=n).getOne().account
                years[n][m]['obligacion'] = model.Obligation.selectBy(month=m, year=n).sum('amount')
            except:
                print n, m

    creacion = Retrasada.crear_extra
    print("Obteniendo Retrasadas")
    retrasadas = procesar_retrasadas(1)
    print("Creando extras")
    map(creacion, retrasadas)
