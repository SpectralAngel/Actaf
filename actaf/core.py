#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# core.py
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

from decimal import Decimal
import csv
import database
import retrasadas

hundred = Decimal("100")

class Ingreso(object):
    
    """Almacena el afiliado y la deduccion realizada para registrar los cobros
    en el sistema"""
    
    def __init__(self, afiliado, cantidad):
        
        self.afiliado, self.cantidad = (afiliado, cantidad)

class Analizador(object):
    
    """Extrae los datos de la planilla de Escalafon y los convierte en
    una representación interna de los cobros"""
    
    def __init__(self, filename, affiliates):
    
        self.file = open(filename)
        self.affiliates = affiliates
        self.parsed = list()
    
    def parse(self):
        
        """Se encarga de tomar linea por linea cada uno de los codigos de
        Identidad y asignarle la cantidad deducida, entregandola en una lista
        de :class:`Ingreso`"""
        
        for line in self.file:

            amount = Decimal(str(line[94:111])) / hundred
            card = str(line[6:10] + '-' + line[10:14] + '-' + line[14:19])
            try:
                afiliado = database.Affiliate.selectBy(cardID=card).getOne()
                self.parsed.append(Ingreso(afiliado, amount))
            except:
                print("Error de parseo no se encontro la identidad %s" % card)
        
        return self.parsed

class AnalizadorINPREMA(object):
    
    """Extrae los datos de la planilla de INPREMA y los convierte en
    una representación interna de los cobros"""
    
    def __init__(self, filename, affiliates):
        
        self.reader = csv.reader(open(filename))
        self.affiliates = affiliates
        self.parsed = list()
    
    def parse(self):
        
        """Se encarga de tomar linea por linea cada uno de los códigos de
        cobro y asignarle la cantidad deducida, entregandola en una lista
        de :class:`Ingreso`"""
        
        perdidos = 0
        for row in self.reader:
            
            amount = Decimal(row[2])
            cobro = int(row[0])
            try:
                self.parsed.append(Ingreso(self.affiliates[cobro], amount))
            
            except:
                perdidos += 1
                print("Error de parseo no se encontro la identidad %s" % cobro)
                
        print perdidos
        return self.parsed

class Actualizador(object):
    
    """Actualiza estados de cuenta de acuerdo a los datos entregados por
    :class:`Ingreso` registrando los motivos por los cuales se efectuó un
    determinado cobro"""
    
    def __init__(self, obligacion, accounts, day):
        
        self.obligacion = obligacion
        self.cuentas = accounts
        self.day = day
        self.registro = dict()
    
    def registrar_cuenta(self, account, name):
        
        """Registra una cuenta para usarla como destino especifico"""
        
        self.registro[name] = account
    
    def update(self, ingreso):
        
        """Actualiza el estado de cuenta de acuerdo a un :class:`Ingreso`"""
        
        self.cuota(ingreso)
        
        for loan in ingreso.afiliado.loans:
            self.prestamo(loan, ingreso)
            
        for reintegro in ingreso.afiliado.reintegros:
            self.reintegros(reintegro, ingreso)
        
        self.extra(ingreso)
        if ingreso.cantidad > 0:
            
            self.excedente(ingreso)
    
    def cuota(self, ingreso):
        
        """Acredita la cuota de aportacion en el estado de cuenta"""
        
        if ingreso.cantidad >= self.obligacion:

            self.cuentas[self.registro['cuota']]['amount'] += self.obligacion
            self.cuentas[self.registro['cuota']]['number'] += 1
            afiliado = database.get_affiliate(ingreso.afiliado.id)
            afiliado.pay_cuota(self.day.year, self.day.month)
            ingreso.cantidad -= self.obligacion
            database.create_deduction(ingreso.afiliado, self.obligacion, self.registro['cuota'])
    
    def reintegros(self, reintegro, ingreso):
        
        """Acredita los reintegros en el estado de cuenta"""
        
        if ingreso >= reintegro.monto and not reintegro.pagado:
            
            ingreso -= reintegro.monto
            self.cuentas[reintegro.cuenta] += reintegro.monto
            reintegro.deduccion(self.day)
    
    def extra(self, ingreso):
        
        """Acredita las deducciones extra en el estado de cuenta"""
        
        extras = sum(e.amount for e in ingreso.afiliado.extras)
        # La cantidad remanente excede o es igual a la cantidad sumada de todas
        # las extras
        if ingreso.cantidad >= extras:
            ingreso.cantidad -= extras
            for extra in ingreso.afiliado.extras:
                self.cuentas[extra.account]['amount'] += extra.amount
                self.cuentas[extra.account]['number'] += 1
                extra.act()
        # La cantidad solo cubre parcialmente las extras
        else:
            for extra in ingreso.afiliado.extras:
                if ingreso.cantidad >= extra.amount:
                    ingreso.cantidad -= extra.amount
                    self.cuentas[extra.account]['amount'] += extra.amount
                    self.cuentas[extra.account]['number'] += 1
                    extra.act()
    
    def excedente(self, ingreso):
        
        """Guarda registro acerca de las cantidades extra que han sido deducidas
        por el sistema, estas serán las devoluciones a efectuar en el mes."""
        
        self.cuentas[self.registro['excedente']]['amount'] += ingreso.cantidad
        self.cuentas[self.registro['excedente']]['number'] += 1
        database.create_deduction(ingreso.afiliado, ingreso.cantidad, self.registro['excedente'])

    def prestamo(self, prestamo, ingreso):
        
        """Actualiza los estados de cuenta de prestamos del afiliado"""
        
        if ingreso.cantidad == 0:
            return
        
        payment = prestamo.get_payment()
        
        # pagar la cuota de prestamo completa
        if ingreso.cantidad >= payment:
            
            database.efectuar_pago(prestamo, payment, self.day)
            
            self.cuentas[self.registro['prestamo']]['amount'] += payment
            self.cuentas[self.registro['prestamo']]['number'] += 1
            ingreso.cantidad -= payment
            database.create_deduction(ingreso.afiliado, payment, self.registro['prestamo'])
        # Cobrar lo que queda en las deducciones y marcalo como cuota incompleta
        # de prestamo
        else:
            database.efectuar_pago(prestamo, ingreso.cantidad, self.day)
            self.cuentas[self.registro['incomplete']]['amount'] += ingreso.cantidad
            self.cuentas[self.registro['incomplete']]['number'] += 1
            database.create_deduction(ingreso.afiliado, ingreso.cantidad, self.registro['incomplete'])
            ingreso.cantidad = 0

class Corrector(object):
    
    def __init__(self, loans):
    
        self.corregir = open('correcciones.txt', 'w')
        self.prestamos = database.get_all_loans()
        
    def corregir_prestamos(self):
    
        for prestamo in self.prestamos:
            
            futuro = prestamo.future()
            if futuro == list():
                self.corregir.write(str(prestamo.id))
                self.corregir.write('\n')
                continue
            
            ultimo_pago = futuro[-1]['payment']
            ultimo_mes = futuro[-1]['enum']
            if ultimo_pago < prestamo.payment and ultimo_mes == prestamo.months:
                prestamo.debt += ((prestamo.payment - ultimo_pago) * 2 / 3).quantize(Decimal("0.01"))
                print "Corregido prestamo %s" % prestamo.id

class ReportLine(object):
    
    """Representacion interna de los valores a deducir en la planilla de
    Escalafon"""
    
    def __init__(self, affiliate, amount):
        
        self.amount = amount
        self.afiliado = affiliate
    
    def __str__(self):
    
        total = self.amount * Decimal(100)
        zeros = '%(#)018d' % {"#":total}
        if self.afiliado.cardID == None:
            return str()
        return self.afiliado.cardID.replace('-', '') + '0011' + zeros

class Generador(object):
    
    """Permite generar la planilla de Escalafon a partir de los estados de
    cuenta de los afiliados"""
    
    def __init__(self, year, month):
        
        self.year = year
        self.month = month
        self.lines = list()
        self.filename = "./%(year)s%(month)02dCOPEMH.txt" % {'year':self.year, 'month':self.month}
    
    def crear_retrasadas(self):
        
        """Crea las cuotas retrasadas para los afiliados"""
        
        for retrasada in retrasadas.procesar_retrasadas('Escalafon'):
    
            retrasada.crear_extra()
    
    def procesar_afiliados(self):
        
        """Calcula las cantidades a pagar por los afiliados"""
        
        afiliados = database.get_affiliates_by_payment("Escalafon", True)
        
        for afiliado in afiliados:
        
            line = ReportLine(afiliado, afiliado.get_monthly())
            self.lines.append(line)
    
    def escribir_archivo(self):
        
        """Escribe el archivo de cobros que se enviará"""
        
        f = open(self.filename, 'w')
        start = "%(year)s%(month)02d" % {'year':int(self.year), 'month':int(self.month)}
        vacio = str()
        for line in self.lines:
            str_line = str(line)
            if str_line == vacio:
                continue
            l = start + str_line + "\n"
            f.write(l)
    
    def agregar_ayuda_medica(self):
        
        """Agrega una Ayuda Médica aprobada a todos los afiliados de Escalafón"""
        
        afiliados = database.get_affiliates_by_payment("Escalafon", True)
        kw = dict()
        kw['account'] = database.get_help_account()
        kw['amount'] = 50
        kw['months'] = 1
        
        for afiliado in afiliados:
            
            kw['affiliate'] = afiliado
            database.Extra(**kw)

class Extraccion(object):
    
    def __init__(self, afiliado, cantidad):
        
        self.afiliado = afiliado
        self.cantidad = cantidad
        self.marca = 'N'
    
    def list(self):
        
        return [self.afiliado.escalafon, self.cantidad, self.marca]
    
    def __str__(self):
        
        return self.afiliado.escalafon + ' ' + str(self.cantidad) + ' ' + self.marca