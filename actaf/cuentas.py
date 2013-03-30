#!/usr/bin/python
# -*- coding: utf8 -*-
#
# cuentas.py
#
# Copyright 2010 by Carlos Flores <cafg10@gmail.com>
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
import csv
from sqlobject import connectionForURI
from sqlobject import sqlhub

scheme = 'mysql://asura:$a1ntcro$$@172.16.10.68/afiliados?charset=utf8'
connection = connectionForURI(scheme)
sqlhub.processConnection = connection

def escalafon():
    afo = database.get_affiliates_by_payment(1)
    
    afiliados = dict()
    
    for a in afo:
        if a.cardID == None:
            continue
        afiliados[a.cardID.replace('-','')] = a
    
    cuentas = csv.reader(open('cuentas.csv'))
    
    for linea in cuentas:
        
        if linea[0] in afiliados:
            afiliado = afiliados[linea[0]]
            banco = int(linea[3])
            cuenta = int(linea[4].strip('ABCDEFGHIJKMNLOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- '))
            
            afiliado.informacionBancaria(banco, cuenta)
            print afiliado.banco, afiliado.cuenta

def actualizar(linea):
    
    afiliado = database.get_affiliate(linea[0])
    afiliado.cuenta = linea[2]

if __name__ == "__main__":
    
    #escalafon()
    cuentas = csv.reader(open('cuentas.csv'))
    map(actualizar, cuentas)
