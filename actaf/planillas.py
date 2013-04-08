#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# planillas.py
#
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

import database
import unicodecsv
from multiprocessing import Pool

def escribir_banco(banco):
    
    afiliados = database.get_affiliates_by_banco(banco.id, 1, True)
    #afiliados = filter((lambda a: a.cuenta != None), afiliados)
    
    lineas = map((lambda a: [str(a.id), u"{0} {1}".format(a.firstName, a.lastName), a.cardID, str(a.get_monthly()), str(a.cuenta)]), afiliados)
    lineas = filter((lambda l: l[0]!=None and l[1]!=None and l[2]!=None and l[3]!=None), lineas)
    planilla = unicodecsv.UnicodeWriter(open(u'{0}.csv'.format(banco.nombre), 'wb'))
    map((lambda l: planilla.writerow(l)), lineas)

if __name__ == "__main__":
    
    pool = Pool()
    
    bancos = database.get_bancos()
    pool.map(escribir_banco, bancos)
    
