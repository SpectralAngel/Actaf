#!/usr/bin/python
# -*- coding: utf8 -*-
#
# inprema.py
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

import csv
import database
import core
from generators import INPREMA
from datetime import date

def extraer_cambios():
    
    affiliates = database.get_affiliates_by_payment(2, True)
    afiliados = dict()
    
    generator = INPREMA(afiliados, date(2013,5,1))
    generator.output()
    
    for a in affiliates:
    
        inprema = None
        try:
            inprema = int(a.escalafon)
        except Exception:
            pass
        
        afiliados[inprema] = a
    
    cambios = dict()
    for afiliado in afiliados:
        a = afiliados[afiliado]
        cambios[afiliado] = core.Extraccion(a, a.get_monthly())
        if not a.active:
            cambios[afiliado].cantidad = 0
            cambios[afiliado].marca = 'C'
    
    parser = core.AnalizadorINPREMA('inprema.csv', afiliados)
    
    for income in parser.parse():
        try:
            if income.cantidad == cambios[int(income.afiliado.escalafon)].cantidad:
                del cambios[int(income.afiliado.escalafon)]
            elif income.cantidad != cambios[int(income.afiliado.escalafon)].cantidad:
                cambios[int(income.afiliado.escalafon)].marca = 'R'
        except Exception:
            print "{0} {1}".format(income.afiliado.escalafon, type(income.afiliado.escalafon))
    
    del cambios[None]
    
    dexter = csv.writer(open('dexter.csv', 'w+b'))
    
    for numero in cambios:
        print cambios[numero]
        dexter.writerow(cambios[numero].list())

if __name__ == "__main__":
    
    extraer_cambios()
