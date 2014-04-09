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
from datetime import date

from sqlobject import AND

import unicodecsv
import model


if __name__ == '__main__':
    afiliados = model.Affiliate.selectBy(active=True)
    afiliados = ([str(a.cardID),
                  a.firstName + ' ' + a.lastName,
                  str(a.get_birthday()),
                  a.cotizacion.nombre,
                  str(a.get_cotizado()),
                  str(a.aportaciones()),
                  str(a.get_cuota(date(2013, 12, 01))), ]
                 for a in afiliados)
    planilla = unicodecsv.UnicodeWriter(open(u'cnbs-activos.csv', 'wb'))
    map((lambda l: planilla.writerow(l)), afiliados)

    afiliados = model.Affiliate.select(
        AND(model.Affiliate.q.desactivacion >= date(2011, 01, 01),
            model.Affiliate.q.desactivacion <= date(2013, 12, 31),
            model.Affiliate.q.active==False)
    )
    afiliados = ([str(a.cardID), a.firstName + ' ' + a.lastName, str(a.get_birthday())]
                 for a in afiliados)
    planilla = unicodecsv.UnicodeWriter(open(u'cnbs-fallecidos.csv', 'wb'))
    map((lambda l: planilla.writerow(l)), afiliados)
