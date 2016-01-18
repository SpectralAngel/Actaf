# -*- coding: utf8 -*-
#
# Copyright 2015 by Carlos Flores <cafg10@gmail.com>
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
from sqlobject import AND

from model import Deduced, Cotizacion, Affiliate

escalafon = Cotizacion.get(1)
inprema = Cotizacion.get(2)
upn = Cotizacion.get(3)
comasol = Cotizacion.get(10)
comasol_jubilados = Cotizacion.get(11)


def corregir_deduccion(deduccion):
    print('Corrigiendo Deduccion {0} de {1} de {2}'.format(
        deduccion.month, deduccion.year, deduccion.amount
    ))
    deduccion.cotizacion = inprema


def procesar_deduccion(deduccion):
    afiliado = deduccion.affiliate
    if afiliado.jubilated is None:
        return
    if afiliado.jubilated.month <= deduccion.month \
            and afiliado.jubilated.year == deduccion.year \
            and deduccion.cotizacion != inprema:

        corregir_deduccion(deduccion)

    if afiliado.jubilated.year < deduccion.year \
            and deduccion.cotizacion != inprema:
        corregir_deduccion(deduccion)


if __name__ == '__main__':
    afiliados = Affiliate.selectBy(cotizacion=inprema)

    deducciones = afiliados.throughTo.deduced.filter(AND(
        Deduced.q.year == 2015
    ))

    [procesar_deduccion(deduccion) for deduccion in deducciones]
