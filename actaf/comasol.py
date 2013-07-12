#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# comasol.py
#
# Copyright 2012 by Carlos Flores <cafg10@gmail.com>
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
from decimal import Decimal

kw = dict()
kw['account'] = model.Account.get(684)

def agregar(linea):
    
    try:
        
        kw['affiliate'] = model.Affiliate.selectBy(cardID=linea[0]).limit(1).getOne()
        kw['months'] = -1
        kw['amount'] = Decimal(linea[1])
        return model.Extra(**kw)
        
    except SQLObjectNotFound:
        
        print(u"Identidad no encontrada {0}".format(linea[0]))
    
    except ValueError as e:
        
        print (u"Error no especificado {0}: {1}".format(e, linea))

if __name__ == '__main__':
    
    reader = csv.reader(open('comasol.csv'))
    map(agregar, reader)
