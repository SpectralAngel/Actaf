#!/usr/bin/env python
# -*- coding: utf8 -*-

import database
import unicodecsv
from multiprocessing import Process, Pool

def escribir_banco(banco):
    
    afiliados = database.get_affiliates_by_banco(banco.id, 1, True)
    #afiliados = filter((lambda a: a.cuenta != None), afiliados)
    
    lineas = map((lambda a: [str(a.id), u"{0} {1}".format(a.firstName, a.lastName), a.cardID, str(a.get_monthly()), str(a.cuenta)]), afiliados)
    lineas = filter((lambda l: l[0]!=None and l[1]!=None and l[2]!=None and l[3]!=None), lineas)
    planilla = unicodecsv.UnicodeWriter(open(u'{0}.csv'.format(banco.nombre), 'wb'))
    map((lambda l: planilla.writerow(l)), lineas)

if __name__ == "__main__":
    with Pool() as pool:
        
        bancos = database.get_bancos()
        pool.map(escribir_banco, bancos)
