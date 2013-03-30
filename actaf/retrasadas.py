#!/usr/bin/env python
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
        
        # Version para SGAM
        # cuenta = model.CuentaRetrasada.get_by(mes=self.mes,anio=self.anio)
        # obligaciones = model.Obligacion.query.filter_by(model.Obligacion.mes=self.mes,
        #                                                model.Obligacion.Anio=self.anio).all()
        
        # Version para TurboAffiliate
        if self.anio == None or self.mes == None:
            return
        
        obligaciones = None
        cuenta = None
        try:
            cuenta = model.CuentaRetrasada.selectBy(mes=self.mes, anio=self.anio).getOne()
            obligaciones = model.Obligation.selectBy(month=self.mes, year=self.anio)
        except:
            print self.anio, self.mes
        
        # SGAM
        # obligacion = sum(o.cantidad for o in obligaciones)
        
        # TA
        if obligaciones == None:
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
        
        # Version para SGAM
        # kw['cuenta'] = cuenta.cuenta
        # kw['cantidad'] = obligacion
        # kw['retrasada'] = True
        # kw['meses'] = 1
        # kw['afiliado'] = self.afiliado
        
        model.Extra(**kw)
        #print extra
        # extra.flush()

def crear_retrasada(afiliado):
    
    cuota = afiliado.get_delayed()
    if cuota is None:
        return Retrasada(afiliado, None, None)
    
    mes = cuota.delayed()
    anio = cuota.year
     
    # SGAM
    # cuota = afiliado.obtener_retrasada()
    # if cuota is None:
    #   continue
    #
    # mes = cuota.retrasada()
    # anio = cuota.anio
    
    return Retrasada(afiliado, anio, mes)

def procesar_retrasadas(cotizacion):
    
    # version para TurboAffiliate
    afiliados = database.get_affiliates_by_payment(cotizacion, True)
    # version para SGAM
    # afiliados = model.Afiliado.query.filter_by(cotizacion=cotizacion)
    
    return map(crear_retrasada, afiliados)

if __name__ == '__main__':
    
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    
    creacion = Retrasada.crear_extra
    print "Obteniendo Retrasadas"
    retrasadas = procesar_retrasadas(1)
    print "Creando extras"
    map(creacion, retrasadas)
    #for retrasada in procesar_retrasadas(1):
    
    #    retrasada.crear_extra()
