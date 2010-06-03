#!/usr/bin/python
# -*- coding: utf8 -*-
#
# model.py
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

import copy
from sqlobject import (SQLObject, UnicodeCol, StringCol, DateCol, CurrencyCol,
                       MultipleJoin, ForeignKey, IntCol, DecimalCol, BoolCol,
                       DatabaseIndex, SQLObjectNotFound, connectionForURI, sqlhub)
from decimal import Decimal
from datetime import date
import math

scheme = 'mysql://asura:$a1ntcro$$@172.16.10.68/afiliados'
connection = connectionForURI(scheme)
sqlhub.processConnection = connection

dot01 = Decimal(".01")
Zero = Decimal(0)
Zeros = Decimal(0)

################################################################################
# Clases Especificas del Negocio
################################################################################

class Affiliate(SQLObject):

    """Representa un miembro de la institución, cada afiliado puede tener
    Prestamos, tiene Cuota mensual que es Deducido por planilla o pagado en
    ventanilla en algunos casos.
    
    Ademas, puede deducirsele por diferentes métodos, como ser:
        
        * Escalafon
        * UPN
        * INPREMA
        * Ventanilla
        * Ministerio de Educación.
    
    El afiliado puede asistir a diferentes eventos de la institucion como ser
    asambleas, elecciones u otras actividades extraordinarias que se programen.
    
    Es necesario para efectuar los diversos cobros:
        
        1. Escalafon: Número de Identidad.
        2. INPREMA: Número de cobro.
        3. UPN: Número de empleado.
    
    Algunos datos son requeridos para obtener información estadistica acerca de
    la institución.
    """

    firstName = UnicodeCol(length="100")
    lastName = UnicodeCol(length="100")
    cardID = UnicodeCol(length=15, default="")
    gender = UnicodeCol(length=1, varchar=False)
    birthday = DateCol(default=date.today)
    birthPlace = UnicodeCol()
    
    address = UnicodeCol(default="")
    phone = UnicodeCol(default="")
    
    state = UnicodeCol(length=50, default="")
    school = UnicodeCol(length=255, default="")
    school2 = UnicodeCol(length=255, default="")
    town = UnicodeCol(length=50, default="")
    
    joined = DateCol(default=date.today)
    active = BoolCol(default=True, notNone=True)
    
    # Reason for deactivation
    reason = UnicodeCol(default="Renuncia", length=50)
    
    escalafon = UnicodeCol(length=11)
    inprema = UnicodeCol(length=11)
    jubilated = DateCol(default=date.today)
    
    payment = UnicodeCol(default="Ventanilla", length=20)
    
    cuotaTables = MultipleJoin("CuotaTable", orderBy='year')
    """Historial de aportaciones"""
    loans = MultipleJoin("Loan", orderBy='startDate')
    """Préstamos activos"""
    payedLoans = MultipleJoin("PayedLoan", orderBy='startDate')
    """Préstamos cancelados"""
    extras = MultipleJoin("Extra")
    """Deducciones extra a efectuar"""
    deduced = MultipleJoin("Deduced", orderBy=['year', 'month'])
    """Deducciones efectuadas por planilla en un mes y año"""
    observaciones = MultipleJoin('Observacion')
    """Observaciones acerca de actividad en un afiliado"""
    solicitudes = MultipleJoin('Solicitud')
    """Solicitudes de Préstamo ingresada"""
    reintegros = MultipleJoin('Reintegro')
    """Reintegros a efectuar"""
    muerte = DateCol(default=date.today)
    """Fecha de Fallecimiento"""
    desactivacion = DateCol(default=date.today)
    """Fecha de Desactivación"""
    
    def get_monthly(self):
        
        extras = sum(e.amount for e in self.extras)
        loans = sum(l.get_payment() for l in self.loans)
        reintegros = sum(r.monto for r in self.reintegros if not r.pagado)
        
        return extras + loans + reintegros + self.get_cuota()
    
    def get_cuota(self):
        
        hoy = date.today()
        obligations = Obligation.selectBy(month=hoy.month, year=hoy.year)
        
        obligation = Decimal(0)
        obligation += sum(o.amount for o in obligations if self.payment != 'INPREMA')
        obligation += sum(o.inprema for o in obligations if self.payment == 'INPREMA')
        
        return obligation
    
    def populate(self, year):
        kw = dict()
        for n in range(1, 13):
            kw["month%s" % n] = False
        return kw
    
    def complete(self, year):
        kw = dict()
        kw['affiliate'] = self
        kw['year'] = year
        CuotaTable(**kw)
    
    def payment_check(self, string):
        
        return self.payment == string
    
    def get_delayed(self):
        
        for cuota in self.cuotaTables:
            
            if cuota.delayed() != Zero:
                
                return cuota
        
        return None
    
    def pay_cuota(self, year, month):
        
        table = None
        
        try:
            table = CuotaTable.selectBy(affiliate=self,year=year).getOne()
        except SQLObjectNotFound:
            kw = dict()
            kw['affiliate'] = self
            kw['year'] = year
            table = CuotaTable(**kw)
        
        table.pay_month(month)
    
    def remove_cuota(self, year, month):
        
        table = None
        
        try:
            table = CuotaTable.selectBy(affiliate=self,year=year).getOne()
        except SQLObjectNotFound:
            kw = dict()
            kw['affiliate'] = self
            kw['year'] = year
            table = CuotaTable(**kw)
        
        table.remove_month(month)
    
    def aportaciones(self):
    
        return sum(table.pagado() for table in self.cuotaTables)
    
    def deuda_prestamo(self):
        
        """Returns the amount debt by payment"""
        
        return sum(loan.debt() for loan in self.loans)
    
    def debt(self):
        
        return sum(table.deuda() for table in self.cuotaTables)
    
    def solvent(self, year):
        
        table = [table for table in self.cuotaTables if table.year == year][0]
        
        return table.all()
    
    def multisolvent(self, year):
        
        for cuota in self.cuotaTables:
            if cuota.year > year:
                break
            if not cuota.todos():
                return False
        return True
    
    def remove(self):
        
        for table in self.cuotaTables:
            table.destroySelf()
        
        for loan in self.loans:
            loan.remove()
        
        self.destroySelf()
    
    def get_month(self, year, month):
        
        try:
            table = CuotaTable.selectBy(affiliate=self,year=year).getOne()
            return getattr(table, "month%s" % month)
        except:
            return False
    
    def link(self, year, month):
        
        return "/affiliate/posteo/?how=%s&year=%s&month=%s&code=%s" % (self.payment, year, month, self.id)
    
    def get_age(self):
        
        return (date.today() - self.birthday).days / 365

class CuentaRetrasada(SQLObject):
    
    account = ForeignKey('Account')
    mes = IntCol()
    anio = IntCol()

class CuotaTable(SQLObject):
    
    """Contains the payed months as Boolen values"""
    
    affiliate = ForeignKey("Affiliate")
    year = IntCol()
    affiliateYear = DatabaseIndex("affiliate", "year", unique=True)
    
    month1 = BoolCol(default=False)
    month2 = BoolCol(default=False)
    month3 = BoolCol(default=False)
    month4 = BoolCol(default=False)
    month5 = BoolCol(default=False)
    month6 = BoolCol(default=False)
    month7 = BoolCol(default=False)
    month8 = BoolCol(default=False)
    month9 = BoolCol(default=False)
    month10 = BoolCol(default=False)
    month11 = BoolCol(default=False)
    month12 = BoolCol(default=False)
    
    def periodo(self):
        
        (start, end) = (1, 13)
        
        if self.affiliate.joined.year == self.year:
            start = self.affiliate.joined.month
        
        if self.year == date.today().year:
            end = date.today().month - 1
        
        if end == 0:
            end = 1
        
        return start, end
    
    def todos(self):
        
        """Verifica si el afiliado ha realizado todos los pagos del año"""
        
        inicio, fin = self.periodo()
        for n in range(inicio, fin):
            if not getattr(self, 'mes%s' % n):
                return False
        
        return True
    
    def vacio(self):
        
        """Responde si el afiliado no ha realizado pagos durante el año"""
        
        inicio, fin = self.periodo()
        for n in range(inicio, fin):
            if getattr(self, 'mes%s' % n):
                return False
        
        return True
    
    def cantidad(self, mes):
        
        total = Zero
        os = Obligation.selectBy(year=self.year,month=mes)
        
        if self.affiliate.payment == "INPREMA" and not self.affiliate.jubilated is None:
            if self.affiliate.jubilated.year < self.year:
                total = sum(o.inprema for o in os)
            elif self.affiliate.jubilated.year == self.year:
                total += sum(o.amount for o in os if mes < self.affiliate.jubilated.month)
                total += sum(o.inprema for o in os if mes >= self.affiliate.jubilated.month)
            elif self.affiliate.jubilated.year > self.year:
                total = sum(o.amount for o in os)
        else:
            total = sum(o.amount for o in os)
        
        return total
    
    def pago_mes(self, mes, periodo=None):
        
        """Muestra la cantidad pagada en el mes especificado"""
        
        if periodo == None:
            inicio, fin = self.periodo()
            periodo = range(inicio, fin)
        
        if not mes in periodo:
            return Zero
        
        if not getattr(self, 'month%s' % mes):
            return Zero
        
        return self.cantidad(mes)
    
    def deuda_mes(self, mes, periodo=None):
        
        """Muestra la cantidad debida en el mes especificado"""
        
        if periodo == None:
            inicio, fin = self.periodo()
            periodo = range(inicio, fin)
        
        if not mes in periodo:
            return Zero
        
        if getattr(self, 'month%s' % mes):
            return Zero
        
        return self.cantidad(mes)
    
    def deuda(self):
        
        """Obtiene la cantidad total debida durante el año"""
        
        inicio, fin = self.periodo()
        periodo = range(inicio, fin)
        return sum(self.deuda_mes(mes, periodo) for mes in periodo)
    
    def pagado(self):
        
        """Obtiene la cantidad total pagada durante el año"""
        
        inicio, fin = self.periodo()
        periodo = range(inicio, fin)
        return sum(self.pago_mes(mes, periodo) for mes in periodo)
    
    def delayed(self):
        
        if self.affiliate.joined == None:
            return Zero
        
        """Obtiene el primer mes en el que no se haya efectuado un pago en las
        aportaciones.
        """
        
        inicio, fin = self.periodo()
        for n in range(inicio, fin):
            if not getattr(self, 'month%s' % n):
                return n
        
        return Zero
    
    def edit_line(self, month):
        text = ' name="month%s"' % month
        if getattr(self, "month%s" % month):
            return text + ' checked'
        else:
            return text + ' '
    
    def pay_month(self, month):
        setattr(self, "month%s" % month, True)
    
    def remove_month(self, month):
        setattr(self, "month%s" % month, False)
    
    def all(self):
        
        return self.todos()
    
    def empty(self):
        
        return self.vacio()

class Loan(SQLObject):

    """Data concerning to Loans"""
    
    affiliate = ForeignKey("Affiliate")
    
    capital = CurrencyCol(default=0, notNone=True)
    letters = UnicodeCol()
    debt = CurrencyCol(default=0, notNone=True)
    payment = CurrencyCol(default=0, notNone=True)
    interest = DecimalCol(default=20, notNone=True, size=4, precision=2)
    months = IntCol()
    last = DateCol(default=date.today)
    number = IntCol(default=0)
    offset = IntCol(default=0)
    
    startDate = DateCol(notNone=True, default=date.today)
    aproved = BoolCol(default=False)
    
    pays = MultipleJoin("Pay", orderBy="day")
    deductions = MultipleJoin("Deduction")
    aproval = ForeignKey("User")
    
    def percent(self):
    
        x = (Decimal(self.debt) * Decimal(100)).quantize(dot01)
        total = x / Decimal(self.capital).quantize(dot01)
        return total
    
    def get_payment(self):
    
        if self.debt < self.payment and self.number != self.months - 1:
            return self.debt
        return self.payment
    
    def start(self):
    
        self.debt = self.capital
    
    def pagar(self, amount, receipt, day=date.today(), libre=False):
        
        """Carga un nuevo pago para el préstamo
        
        Dependiendo de si se marca como libre de intereses o no, calculará el
        interés compuesto a pagar
        """
        
        kw = dict()
        kw['amount'] = Decimal(amount).quantize(dot01)
        kw['day'] = day
        kw['receipt'] = receipt
        kw['loan'] = self
        
        # La cantidad a pagar es igual o mayor que la deuda del préstamo, por
        # lo tanto se considera la ultima cuota y no se cargaran intereses
        if(self.debt <= amount):
            
            self.last = kw['day']
            kw['capital'] = kw['amount']
            # Register the payment in the database
            Pay(**kw)
            # Remove the loan and convert it to PayedLoan
            self.remove()
            return True
        
        # Otherwise calculate interest for the loan's payment
        if libre:
            kw['interest'] = 0
        else:
            kw['interest'] = (self.debt * self.interest / 1200).quantize(dot01)
        
        # Increase the loans debt by the interest
        self.debt += kw['interest']
        # Decrease debt by the payment amount
        self.debt -= kw['amount']
        # Calculate how much money was used to pay the capital
        kw['capital'] = kw['amount'] - kw['interest']
        # Change the last payment date
        self.last = day
        # Register the payment in the database
        Pay(**kw)
        # Increase the number of payments by one
        self.number += 1
        
        if self.debt == 0:
            self.remove()
            return True
        
        self.compensar()
        
        return False
    
    def refinanciar(self, pago, solicitud, cuenta, usuario, descripcion):
        
        self.pagar(pago, "Liquidacion", solicitud.entrega, True)
        
        prestamo = solicitud.prestamo(usuario)
        
        kw = dict()
        kw['account'] = cuenta
        kw['amount'] = pago
        kw['name'] = kw['account'].name
        kw['loan'] = prestamo
        kw['description'] = descripcion
        
        Deduction(**kw)
        
        return prestamo
    
    def net(self):
        
        """Obtains the amount that was given to the affiliate in the check"""
        
        return self.capital - sum(d.amount for d in self.deductions)
    
    def total_deductions(self):
        
        return sum(d.amount for d in self.deductions)
    
    def remove(self):
        
        kw = dict()
        kw['id'] = self.id
        kw['affiliate'] = self.affiliate
        kw['capital'] = self.capital
        kw['letters'] = self.letters
        kw['interest'] = self.interest
        kw['months'] = self.months
        kw['last'] = self.last
        kw['startDate'] = self.startDate
        kw['payment'] = self.payment
        payed = PayedLoan(**kw)
        
        for pay in self.pays:
            pay.remove(payed)
        
        for deduction in self.deductions:
            deduction.remove(payed)
        
        self.destroySelf()
    
    def future(self):
        
        debt = copy.copy(self.debt)
        li = list()
        months = {
            1:'Enero', 2:'Febrero', 3:'Marzo', 
            4:'Abril', 5:'Mayo', 6:'Junio', 
            7:'Julio', 8:'Agosto', 9:'Septiembre', 
            10:'Octubre', 11:'Noviembre', 12:'Diciembre'
        }
        start = self.startDate.month + self.offset
        if self.startDate.day == 24 and self.startDate.month == 8:
            start += 1
        year = self.startDate.year
        for n in range(1, self.months - self.number + 2):
            kw = dict()
            kw['number'] = "%s/%s" % (n + self.number, self.months)
            kw['month'] = self.number + n + start
            kw['enum'] = self.number + n
            kw['year'] = year
            while kw['month'] > 12:
                kw['month'] = kw['month'] - 12
                kw['year'] += 1
            kw['month'] = "%s %s" % (months[kw['month']], kw['year'])
            kw['interest'] = Decimal(debt * self.interest / 1200).quantize(dot01)
            if debt <= self.payment:
                kw['amount'] = 0
                kw['capital'] = debt
                kw['payment'] = kw['interest'] + kw['capital']
                li.append(kw)
                break
            kw['capital'] = self.payment - kw['interest']
            debt = debt + kw['interest'] - self.payment
            kw['amount'] = debt
            kw['payment'] = kw['interest'] + kw['capital']
            li.append(kw)
        return li
    
    def compensar(self):
        
        futuro = self.future()
        if futuro == list():
            return
        
        ultimo_pago = futuro[-1]['payment']
        ultimo_mes = futuro[-1]['enum']
        if ultimo_pago < self.payment and ultimo_mes == self.months:
            self.debt += ((self.payment - ultimo_pago) * 2 / 3).quantize(dot01)
    
    def totaldebt(self):
        
        return self.debt

class Pay(SQLObject):
    
    loan = ForeignKey("Loan")
    day = DateCol(default=date.today)
    capital = CurrencyCol(default=0, notNone=True)
    interest = CurrencyCol(default=0, notNone=True)
    amount = CurrencyCol(default=0, notNone=True)
    receipt = UnicodeCol(length=50)
    
    def remove(self, payedLoan):
        
        kw = dict()
        kw['payedLoan'] = payedLoan
        kw['day'] = self.day
        kw['capital'] = self.capital
        kw['interest'] = self.interest
        kw['amount'] = self.amount
        kw['receipt'] = self.receipt
        kw['month'] = self.month
        self.destroySelf()
        OldPay(**kw)
    
    def revert(self):
        
        self.loan.debt += self.capital
        self.loan.number -= 1
        self.destroySelf()

class Account(SQLObject):
    
    """Simple Account made for affiliate handling"""
    
    name = StringCol()
    code = IntCol(alternateID=True)
    loan = BoolCol(default=False)
    
    extras = MultipleJoin("Extra")
    retrasadas = MultipleJoin("CuentaRetrasada")

class Extra(SQLObject):
    
    """Represents a Deduction that will be made"""
    
    affiliate = ForeignKey("Affiliate")
    amount = CurrencyCol(default=0)
    months = IntCol(default=1)
    retrasada = BoolCol(default=False)
    account = ForeignKey("Account")
    mes = IntCol(default=None)
    anio = IntCol(default=None)
    
    def act(self, decrementar=True):
        
        if decrementar:
            self.months -= 1
        self.to_deduced()
        if self.months == 0:
            self.destroySelf()
    
    def to_deduced(self):
        
        kw = dict()
        kw['amount'] = self.amount
        kw['affiliate'] = self.affiliate
        kw['account'] = self.account
        
        if self.retrasada:
            
            cuota = self.affiliate.get_delayed()
            month, year = (None, None)
            if not cuota is None:
                month = cuota.delayed()
                year = cuota.year
                cuota.pay_month(month)
            kw['detail'] = "Cuota Retrasada %s de %s" % (month, year)
        
        Deduced(**kw)
    
    def to_other(self):
        
        kw = dict()
        kw['amount'] = self.amount
        kw['affiliate'] = self.affiliate
        kw['account'] = self.account
        OtherDeduced(**kw)
    
    def manual(self):
        
        self.to_other()
        self.act()

class Deduction(SQLObject):
    
    loan = ForeignKey("Loan")
    name = UnicodeCol()
    amount = CurrencyCol()
    account = ForeignKey("Account")
    description = UnicodeCol()
    
    def remove(self, payedLoan):
        
        kw = dict()
        kw['payedLoan'] = payedLoan
        kw['name'] = self.name
        kw['amount'] = self.amount
        kw['account'] = self.account
        kw['description'] = self.description
        PayedDeduction(**kw)
        self.destroySelf()

class PayedLoan(SQLObject):
    
    affiliate = ForeignKey("Affiliate")
    capital = CurrencyCol(default=0, notNone=True)
    letters = StringCol()
    payment = CurrencyCol(default=0, notNone=True)
    interest = DecimalCol(default=20, notNone=True, size=4, precision=2)
    months = IntCol()
    last = DateCol(default=date.today)
    startDate = DateCol(notNone=True, default=date.today)
    pays = MultipleJoin("OldPay")
    deductions = MultipleJoin("PayedDeduction")
    
    def remove(self):
        
        [pay.destroySelf() for pay in self.pays]
        [deduction.destroySelf() for deduction in self.deductions]
        self.destroySelf()
    
    def to_loan(self, user):
        
        kw = dict()
        kw['aproval'] = user
        kw['affiliate'] = self.affiliate
        kw['capital'] = self.capital
        kw['interest'] = self.interest
        kw['payment'] = self.payment
        kw['months'] = self.months
        kw['last'] = self.last
        kw['startDate'] = self.startDate
        kw['letters'] = self.letters
        kw['number'] = len(self.pays)
        kw['id'] = self.id
        loan = Loan(**kw)
        
        [pay.to_pay(loan) for pay in self.pays]
        [deduction.to_deduction(loan) for deduction in self.deductions]
        
        self.destroySelf()
        return loan
    
    def net(self):
        
        """Obtains the amount that was given to the affiliate in the check"""
        
        return self.capital - sum(d.amount for d in self.deductions)
    
    def totaldebt(self):
        
        return 0

class OldPay(SQLObject):
    
    payedLoan = ForeignKey("PayedLoan")
    day = DateCol(default=date.today)
    capital = CurrencyCol(default=0, notNone=True)
    interest = CurrencyCol(default=0, notNone=True)
    amount = CurrencyCol(default=0, notNone=True)
    receipt = UnicodeCol(length=50)
    
    def to_pay(self, loan):
        
        kw = dict()
        kw['loan'] = loan
        kw['day'] = self.day
        kw['capital'] = self.capital
        kw['interest'] = self.interest
        kw['amount'] = self.amount
        kw['receipt'] = self.receipt
        kw['month'] = self.month
        Pay(**kw)
        self.destroySelf()

class PayedDeduction(SQLObject):
    
    payedLoan = ForeignKey("PayedLoan")
    name = StringCol()
    amount = CurrencyCol()
    account = ForeignKey("Account")
    description = StringCol()
    
    def to_deduction(self, loan):
        
        kw = dict()
        kw['loan'] = loan
        kw['name'] = self.name
        kw['amount'] = self.amount
        kw['description'] = self.description
        kw['account'] = self.account
        Deduction(**kw)
        self.destroySelf()

class Obligation(SQLObject):
    
    """The description of the Cuota payment"""
    
    name = UnicodeCol(length=100)
    amount = CurrencyCol(default=0, notNone=True)
    inprema = CurrencyCol(default=0, notNone=True)
    month = IntCol()
    year = IntCol()
    account = ForeignKey("Account")
    filiales = CurrencyCol(default=4, notNone=True)

class ReportAccount(SQLObject):
    
    name = name = UnicodeCol(length=100)
    code = IntCol(default=0)
    quantity = IntCol()
    amount = CurrencyCol(default=0)
    postReport = ForeignKey("PostReport")

    def add(self, amount):
        self.amount += amount
        self.quantity += 1

class PostReport(SQLObject):

    year = IntCol()
    month = IntCol()
    reportAccounts = MultipleJoin("ReportAccount", orderBy="name")

    def total(self):
        return sum(r.amount for r in self.reportAccounts)

class Deduced(SQLObject):
    
    affiliate = ForeignKey("Affiliate")
    amount = CurrencyCol(default=0)
    account = ForeignKey("Account")
    detail = UnicodeCol(default="")
    month = IntCol(default=date.today().month)
    year = IntCol(default=date.today().year)

class OtherReport(SQLObject):
    
    year = IntCol()
    month = IntCol()
    payment = UnicodeCol(length=15)
    otherAccounts = MultipleJoin("OtherAccount")

    def total(self):
        return sum(r.amount for r in self.otherAccounts)

class OtherAccount(SQLObject):
    
    account = ForeignKey("Account")
    quantity = IntCol(default=0)
    amount = CurrencyCol(default=0)
    otherReport = ForeignKey("OtherReport")

    def add(self, amount):
        self.amount += amount
        self.quantity += 1

class OtherDeduced(SQLObject):
    
    affiliate = ForeignKey("Affiliate")
    amount = CurrencyCol(default=0)
    account = ForeignKey("Account")

class AuxiliarPrestamo(object):
    
    def __init__(self, id, afiliado, monto, neto, papeleo, aportaciones,
                 intereses, retencion, reintegros):
        
        self.id = id
        self.afiliado = afiliado
        self.monto = monto
        self.neto = neto
        self.papeleo = papeleo
        self.aportaciones = aportaciones
        self.intereses = intereses
        self.retencion = retencion
        self.reintegros = reintegros

class Observacion(SQLObject):
    
    affiliate = ForeignKey("Affiliate")
    texto = UnicodeCol()
    fecha = DateCol(default=date.today)

class Solicitud(SQLObject):
    
    affiliate = ForeignKey("Affiliate")
    ingreso = DateCol(default=date.today)
    entrega = DateCol(default=date.today)
    monto = CurrencyCol(default=0, notNone=True)
    periodo = IntCol(default=12)
    
    def prestamo(self, user):
        
        tipo = Decimal(20) / 1200
        numerado = str(1 - math.pow(tipo + 1, -self.periodo))
        cuota = self.monto * Decimal(tipo / Decimal(numerado))
        
        kw = dict()
        kw['aproval'] = user
        kw['affiliate'] = self.affiliate
        kw['capital'] = self.monto
        kw['interest'] = 20
        kw['payment'] = cuota
        kw['months'] = self.periodo
        kw['last'] = self.entrega
        kw['startDate'] = self.entrega
        kw['letters'] = wording.parse(self.monto).capitalize()
        kw['number'] = 0
        prestamo = Loan(**kw)
        prestamo.start()
        
        return prestamo

class FormaPago(SQLObject):
    
    """Maneras en que se puede efectuar un pago"""
    
    nombre = UnicodeCol(length=15)
    """Nombre de la forma de pago"""

class Reintegro(SQLObject):
    
    """Cobros que debieron regresarse al empleador del afiliado y que deben ser
    cobrados de nuevo"""
    
    affiliate = ForeignKey('Affiliate')
    """:class:`Affiliate` al que pertenece el cobro"""
    emision = DateCol(default=date.today)
    """Fecha en que se emitio el pago del empleador"""
    monto = CurrencyCol()
    """Monto que debe cobrarse"""
    cheque = UnicodeCol(length=10)
    """Cheque bancario utilizado por el empleador para pagar"""
    planilla = UnicodeCol(length=10)
    """Codigo de la planilla enviado por el empleador"""
    motivo = UnicodeCol(length=100)
    """Razón por la cual se debe efectuar el cobro de nuevo"""
    formaPago = ForeignKey("FormaPago", default=FormaPago.get(1))
    """Modo en que se efectuó el cobro"""
    pagado = BoolCol(default=False)
    """Identifica si el reintegro ya ha sido pagado"""
    cancelacion = DateCol(default=date.today)
    """Indica el día en que se efectuó el cobro"""
    cuenta = ForeignKey('Account')
    """Cuenta a la que pertenece el reintegro"""
    
    def cancelar(self, dia=date.today()):
        
        """Marca el :class:`Reintegro` como pagado"""
        
        self.pagado = True
    
    def deduccion(self, dia=date.today()):
        
        """Efectua el pago del :class:`Reintegro` mediante una planilla"""
        
        self.cancelar(dia)
        self.formaPago = FormaPago.get(1)
        
        kw = dict()
        kw['amount'] = self.monto
        kw['affiliate'] = self.afiliado
        kw['account'] = self.cuenta
        kw['month'] = dia.month
        kw['year'] = dia.year
        
        kw['detail'] = "Reintegro %s por %s" % (self.emision.strftime('%d/%m/%Y'), self.motivo)
        
        Deduced(**kw)
    
    def revertir(self):
        
        """Revierte el pago del :class:`Reintegro`"""
        
        self.pagado = False
