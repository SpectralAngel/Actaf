#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# institutos.py
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

import model
import csv
from sqlobject.main import SQLObjectNotFound

kw = dict()


def agregar_instituto(linea):

    try:

        kw['municipio'] = model.Municipio.get(linea[0])
        kw['nombre'] = linea[1]
        return model.Instituto(**kw)

    except SQLObjectNotFound:

        print(u"Identidad no encontrada {0}".format(linea[0]))

    except ValueError as e:

        print (u"Error no especificado {0}: {1}".format(e, linea))


if __name__ == '__main__':

    reader = csv.reader(open('institutos.csv'))
    map(agregar_instituto, reader)
