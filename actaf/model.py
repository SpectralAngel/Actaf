# -*- coding: utf8 -*-
#
# model.py
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

import copy
from dateutil.relativedelta import relativedelta
from sqlobject import (SQLObject, UnicodeCol, StringCol, DateCol, CurrencyCol,
                       MultipleJoin, ForeignKey, IntCol, DecimalCol, BoolCol,
                       DatabaseIndex, SQLObjectNotFound, connectionForURI,
                       DateTimeCol, RelatedJoin, sqlhub, SQLMultipleJoin)
from decimal import Decimal
from datetime import date, datetime
import math
import calendar

scheme = 'mysql://turboaffiliate:TQV8wUp6@172.16.10.87/afiliados?charset=utf8'
connection = connectionForURI(scheme)
sqlhub.processConnection = connection

dot01 = Decimal(".01")
Zero = Decimal(0)
Zeros = Decimal(0)

# ###############################################################################
# Clases Especificas del Negocio
################################################################################

months = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo',
    4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre',
    10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


class Departamento(SQLObject):
    nombre = UnicodeCol(length=50, default=None)
    municipios = MultipleJoin('Municipio')
    afiliados = MultipleJoin('Affiliate')
    usuarios = RelatedJoin("User")


class Municipio(SQLObject):
    departamento = ForeignKey('Departamento')
    nombre = UnicodeCol(length=50, default=None)
    afiliados = MultipleJoin('Affiliate')
    viaticos = MultipleJoin('Viatico')


class Instituto(SQLObject):
    municipio = ForeignKey('Municipio')
    nombre = UnicodeCol(length=50, default=None)
    afiliados = MultipleJoin('Affiliate')


class Casa(SQLObject):
    """Sucursal del COPEMH

    Representa un lugar físico donde se encuentra una sede del COPEMH.
    """

    nombre = UnicodeCol(length=20, default=None)
    direccion = UnicodeCol(length=255)
    telefono = UnicodeCol(length=11)
    activa = BoolCol(default=True)
    prestamos = MultipleJoin("Loan")
    usuarios = MultipleJoin("User")


class Cotizacion(SQLObject):
    nombre = UnicodeCol(length=50, default=None)
    jubilados = BoolCol(default=True)
    usuarios = RelatedJoin("User")
    afiliados = MultipleJoin("Affiliate")
    bank_main = BoolCol(default=False)
    alternate = BoolCol(default=True)
    normal = BoolCol(default=True)
    ordering = UnicodeCol(length=50, default='lastName')


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

    Algunos datos son requeridos para obtener información estadística acerca de
    la institución.
    @DynamicAttrs
    """

    firstName = UnicodeCol(length=100)
    """Nombre del Afiliado"""
    lastName = UnicodeCol(length=100)
    """Apellidos del Afiliado"""
    cardID = UnicodeCol(length=15, default=None)
    """Identidad del afiliado"""
    gender = UnicodeCol(length=1, varchar=False)
    birthday = DateCol(default=date.today)
    birthPlace = UnicodeCol(length=100, default=None)

    address = UnicodeCol(default=None)
    phone = UnicodeCol(default=None)

    departamento = ForeignKey('Departamento', default=Departamento.get(19))
    municipio = ForeignKey('Municipio', default=Municipio.get(299))
    instituto = ForeignKey('Instituto', default=None)

    state = UnicodeCol(length=50, default=None)
    school = UnicodeCol(length=255, default=None)
    town = UnicodeCol(length=50, default=None)

    joined = DateCol(default=date.today)
    """Fecha en que se unio a la organización"""
    active = BoolCol(default=True, notNone=True)
    """Indica si el afiliado se encuentra activo o no"""
    reason = UnicodeCol(default=None, length=50)
    """Razon por la que fue desactivado el afiliado"""
    escalafon = UnicodeCol(length=11, default=None)
    inprema = UnicodeCol(length=11, default=None)
    jubilated = DateCol(default=None)

    payment = UnicodeCol(default="Ventanilla", length=20)
    cotizacion = ForeignKey('Cotizacion')
    """Método de Cotización"""

    cuotaTables = MultipleJoin("CuotaTable", orderBy='year')
    autoseguros = MultipleJoin("AutoSeguro", orderBy='year')
    """Historial de aportaciones"""
    loans = MultipleJoin("Loan", orderBy='startDate')
    """Préstamos activos"""
    payedLoans = MultipleJoin("PayedLoan", orderBy='startDate')
    """Préstamos cancelados"""
    extras = MultipleJoin("Extra")
    """Deducciones extra a efectuar"""
    deduced = MultipleJoin("Deduced", orderBy=['-year', '-month'])
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
    cuenta = UnicodeCol(default=None)
    """Número de cuenta bancaria"""
    banco = IntCol(default=None)
    """Código del Banco"""
    email = UnicodeCol(default=None)
    autorizacion = BoolCol(default=False, notNone=True)
    sobrevivencias = MultipleJoin("Sobrevivencia", joinColumn="afiliado_id")
    devoluciones = MultipleJoin("Devolucion", joinColumn="afiliado_id")
    funebres = MultipleJoin("Funebre", joinColumn="afiliado_id")
    seguros = MultipleJoin("Seguro", joinColumn="afiliado_id")
    inscripciones = MultipleJoin("Inscripcion", joinColumn="afiliado_id")
    depositos = MultipleJoin("Deposito", joinColumn="afiliado_id")
    deduccionesBancarias = MultipleJoin("DeduccionBancaria",
                                        joinColumn="afiliado_id",
                                        orderBy=['-year', '-month'])
    banco_completo = BoolCol(default=False, notNone=True)
    autorizaciones = MultipleJoin('Autorizacion')
    logs = MultipleJoin('Logger')
    bancario = UnicodeCol(default=None)
    last = CurrencyCol(default=Zero)

    def tiempo(self):

        """Permite mostrar el tiempo que tiene el afiliado de ser parte de la
        organizacion"""

        if self.joined is None:
            return 1

        return (date.today() - self.joined).days / 365

    def get_banco(self):

        if self.banco is None:
            return None

        return Banco.get(self.banco)

    def get_monthly(self, day=date.today(), bank=False, loan_only=False):

        """Obtiene el pago mensual que debe efectuar el afiliado"""

        if loan_only:
            return self.get_prestamo()

        total = sum(e.amount for e in self.extras)
        # loans = sum(l.get_payment() for l in self.loans)
        # reintegros = sum(r.monto for r in self.reintegros if not r.pagado)

        for reintegro in self.reintegros:
            if reintegro.pagado:
                break
            total += reintegro.monto

        if bank:
            total += self.get_bank_cuota(day)
        else:
            total += self.get_cuota(day)

        if self.cotizacion.bank_main or self.banco_completo:
            total += self.get_prestamo()

        return total

    def get_cuota(self, day=date.today()):

        """Obtiene la cuota de aportación que el :class:`Affiliate` debera pagar
        en el mes actual"""

        obligations = Obligation.selectBy(month=day.month, year=day.year)

        if self.cotizacion.jubilados and self.cotizacion.alternate:
            return obligations.sum('inprema_compliment')

        obligation = Zero
        if self.cotizacion.normal:
            obligation += obligations.sum('amount')

        if self.cotizacion.jubilados:
            obligation += obligations.sum('inprema')

        if self.cotizacion.alternate:
            obligation += obligations.sum('alternate')

        return obligation

    def get_bank_cuota(self, day=date.today()):

        """Obtiene la cuota de aportación que el :class:`Affiliate` debera pagar
        en el mes actual"""

        obligations = Obligation.selectBy(month=day.month, year=day.year)

        obligation = Zero
        if self.banco_completo:
            if not self.cotizacion.jubilados:
                obligation += obligation.sum('amount_compliment')
            if self.cotizacion.jubilados:
                obligation += obligation.sum('inprema')
            if not self.cotizacion.alternate:
                obligation += obligations.sum('amount')
        else:
            if not self.cotizacion.jubilados:
                obligation += obligations.sum('amount')

            if self.cotizacion.jubilados:
                obligation = obligations.sum('inprema')

            if not self.cotizacion.alternate:
                obligation = obligations.sum('amount_compliment')

        return obligation

    def get_prestamo(self):

        loans = Decimal(0)
        # Cobrar solo el primer préstamo
        for loan in self.loans:
            loans = loan.get_payment()
            break

        return loans

    def populate(self, year):

        kw = dict()
        for n in range(1, 13):
            kw["month{0}".format(n)] = False
        return kw

    def complete(self, year):

        """Agrega un año de aportaciones al estado de cuenta del afiliado"""

        kw = dict()
        kw['affiliate'] = self
        kw['year'] = year
        CuotaTable(**kw)

    def complete_compliment(self, year):

        """Agrega un año de aportaciones al estado de cuenta del afiliado"""

        kw = dict()
        kw['affiliate'] = self
        kw['year'] = year
        AutoSeguro(**kw)

    def get_delayed(self):

        for cuota in self.cuotaTables:
            if cuota.delayed() != Zero:
                return cuota
        return None

    def obtenerAportaciones(self, year):
        cuota = None
        try:
            cuota = CuotaTable.selectBy(affiliate=self, year=year).getOne()
        except SQLObjectNotFound:

            # Esto evita crear un año de aportaciones incorrecto
            if year < self.joined.year:
                return None

            kw = dict()
            kw['affiliate'] = self
            kw['year'] = year
            cuota = CuotaTable(**kw)
        return cuota

    def pagar_cuota(self, mes, anio):

        self.obtenerAportaciones(anio).pagar_mes(mes)

    def pay_cuota(self, year, month):

        self.obtenerAportaciones(year).pagar_mes(month)

    def remove_cuota(self, year, month):

        self.obtenerAportaciones(year).remove_month(month)

    def aportaciones(self):

        return sum(table.pagado() for table in self.cuotaTables)

    def deuda_prestamo(self):

        """Muestra la deuda por préstamos"""

        return sum(loan.debt() for loan in self.loans)

    def debt(self):

        return sum(table.deuda() for table in self.cuotaTables)

    def solvent(self, year):

        return self.obtenerAportaciones(year).all()

    def multisolvent(self, year, gracia=False):

        for cuota in self.cuotaTables:
            if cuota.year > year:
                break
            if not cuota.todos(gracia=gracia):
                return False
        return True

    def remove(self):

        [table.destroySelf() for table in self.cuotaTables]

        [loan.remove() for loan in self.loans]

        self.destroySelf()

    def get_month(self, year, month):

        table = self.obtenerAportaciones(year)

        # en caso que el afiliado sea de afiliación más reciente que el año
        # solicitado
        if table is None:
            return False

        return getattr(table, "month{0}".format(month))

    def get_age(self):

        return (date.today() - self.birthday).days / 365

    def get_phone(self):

        if self.phone is not None:
            phone = self.phone.replace('-', '').replace('/', '')
            if len(phone) > 11:
                return phone[:11]
            return phone

        return ""

    def get_email(self):

        if self.email is not None:
            return self.email

        return ""

    def recibos(self):

        return Recibo.selectBy(afiliado=self.id)

    def recibos_sps(self):

        return ReciboSPS.selectBy(afiliado=self.id)

    def recibos_ceiba(self):

        return ReciboCeiba.selectBy(afiliado=self.id)


class Autorizacion(SQLObject):
    affiliate = ForeignKey("Affiliate")
    fecha = DateCol(default=date.today)
    banco = ForeignKey("Banco")


class CuentaRetrasada(SQLObject):
    account = ForeignKey('Account')
    mes = IntCol()
    anio = IntCol()


class CuotaTable(SQLObject):
    """Contains the payed months as Boolean values"""

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

    def periodo(self, retrasada=False, gracia=False):

        (start, end) = (1, 13)

        if self.affiliate.joined.year == self.year:
            start = self.affiliate.joined.month

        if self.year == date.today().year:
            if retrasada:
                end = date.today().month
            else:
                if gracia:
                    end = date.today().month - 4
                else:
                    end = date.today().month + 1
        else:
            if gracia:
                end = 8

        if end <= 0:
            end = 1

        return start, end

    def todos(self, gracia=False):

        """Verifica si el afiliado ha realizado todos los pagos del año"""

        inicio, fin = self.periodo(gracia=gracia)
        for n in range(inicio, fin):
            if not getattr(self, 'month{0}'.format(n)):
                return False

        return True

    def vacio(self):

        """Responde si el afiliado no ha realizado pagos durante el año"""

        inicio, fin = self.periodo()
        for n in range(inicio, fin):
            if getattr(self, 'month{0}'.format(n)):
                return False

        return True

    def cantidad(self, mes):

        total = Zero
        os = Obligation.selectBy(year=self.year, month=mes)

        if (self.affiliate.cotizacion.jubilados and
                not self.affiliate.jubilated is None):

            if self.affiliate.jubilated.year < self.year:
                total = sum(o.inprema for o in os)

            elif self.affiliate.jubilated.year == self.year:
                total += sum(o.amount for o in os
                             if mes < self.affiliate.jubilated.month)

                total += sum(o.inprema for o in os
                             if mes >= self.affiliate.jubilated.month)

            elif self.affiliate.jubilated.year > self.year:
                total = sum(o.amount for o in os)

        elif self.affiliate.cotizacion.alternate:
            total = sum(o.alternate for o in os)

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

        if not getattr(self, 'month{0}'.format(mes)):
            return Zero

        return self.cantidad(mes)

    def deuda_mes(self, mes, periodo=None):

        """Muestra la cantidad debida en el mes especificado"""

        if periodo == None:
            inicio, fin = self.periodo()
            periodo = range(inicio, fin)

        if not mes in periodo:
            return Zero

        if getattr(self, 'month{0}'.format(mes)):
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

        inicio, fin = self.periodo(retrasada=True)
        for n in range(inicio, fin):
            if not getattr(self, 'month{0}'.format(n)):
                return n

        return Zero

    def edit_line(self, month):
        text = ' name="month{0}"'.format(month)
        if getattr(self, 'month{0}'.format(month)):
            return text + ' checked'
        else:
            return text + ' '

    def pagar_mes(self, mes):
        setattr(self, 'month{0}'.format(mes), True)

    def pay_month(self, month):
        setattr(self, 'month{0}'.format(month), True)

    def remove_month(self, month):
        setattr(self, 'month{0}'.format(month), False)

    def all(self):

        return self.todos()

    def empty(self):

        return self.vacio()


class AutoSeguro(SQLObject):
    """Contains the payed months as Boolean values"""

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

    def periodo(self, retrasada=False, gracia=False):

        (start, end) = (1, 13)

        if self.affiliate.joined.year == self.year:
            start = self.affiliate.joined.month

        if self.year == date.today().year:
            if retrasada:
                end = date.today().month
            else:
                if gracia:
                    end = date.today().month - 4
                else:
                    end = date.today().month + 1
        else:
            if gracia:
                end = 8

        if end <= 0:
            end = 1

        return start, end

    def todos(self, gracia=False):

        """Verifica si el afiliado ha realizado todos los pagos del año"""

        inicio, fin = self.periodo(gracia=gracia)
        for n in range(inicio, fin):
            if not getattr(self, 'month{0}'.format(n)):
                return False

        return True

    def vacio(self):

        """Responde si el afiliado no ha realizado pagos durante el año"""

        inicio, fin = self.periodo()
        for n in range(inicio, fin):
            if getattr(self, 'month{0}'.format(n)):
                return False

        return True

    def cantidad(self, mes):

        total = Zero
        os = Obligation.selectBy(year=self.year, month=mes)

        if (self.affiliate.cotizacion.jubilados and
                not self.affiliate.jubilated is None):

            if self.affiliate.jubilated.year < self.year:
                total = sum(o.inprema_compliment for o in os)

            elif self.affiliate.jubilated.year == self.year:
                total += sum(o.amount_compliment for o in os
                             if mes < self.affiliate.jubilated.month)

                total += sum(o.inprema_compliment for o in os
                             if mes >= self.affiliate.jubilated.month)

            elif self.affiliate.jubilated.year > self.year:
                total = sum(o.amount_compliment for o in os)

        else:
            total = sum(o.amount_compliment for o in os)

        return total

    def pago_mes(self, mes, periodo=None):

        """Muestra la cantidad pagada en el mes especificado"""

        if periodo == None:
            inicio, fin = self.periodo()
            periodo = range(inicio, fin)

        if not mes in periodo:
            return Zero

        if not getattr(self, 'month{0}'.format(mes)):
            return Zero

        return self.cantidad(mes)

    def deuda_mes(self, mes, periodo=None):

        """Muestra la cantidad debida en el mes especificado"""

        if periodo == None:
            inicio, fin = self.periodo()
            periodo = range(inicio, fin)

        if not mes in periodo:
            return Zero

        if getattr(self, 'month{0}'.format(mes)):
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

        if self.affiliate.joined is None:
            return Zero

        """Obtiene el primer mes en el que no se haya efectuado un pago en las
        aportaciones.
        """

        inicio, fin = self.periodo(retrasada=True)
        for n in range(inicio, fin):
            if not getattr(self, 'month{0}'.format(n)):
                return n

        return Zero

    def edit_line(self, month):
        text = ' name="month{0}"'.format(month)
        if getattr(self, 'month{0}'.format(month)):
            return text + ' checked'
        else:
            return text + ' '

    def pagar_mes(self, mes):
        setattr(self, 'month{0}'.format(mes), True)

    def pay_month(self, month):
        setattr(self, 'month{0}'.format(month), True)

    def remove_month(self, month):
        setattr(self, 'month{0}'.format(month), False)

    def all(self):

        return self.todos()

    def empty(self):

        return self.vacio()


class Loan(SQLObject):
    """Guarda los datos que pertenecen a un préstamo personal otorgado a un
    :class:`Affiliate` de la organización

    @DynamicAttrs
    """

    affiliate = ForeignKey("Affiliate")
    casa = ForeignKey("Casa")

    capital = CurrencyCol(default=0, notNone=True)
    letters = UnicodeCol(default=None, length=100)
    debt = CurrencyCol(default=0, notNone=True)
    payment = CurrencyCol(default=0, notNone=True)
    interest = DecimalCol(default=20, notNone=True, size=4, precision=2)
    months = IntCol()
    last = DateCol(default=date.today)
    number = IntCol(default=0)
    offset = IntCol(default=0)

    startDate = DateCol(notNone=True, default=date.today)
    aproved = BoolCol(default=False)
    fecha_mora = DateCol(notNone=True, default=date.today)

    pays = SQLMultipleJoin("Pay", orderBy="day")
    deductions = SQLMultipleJoin("Deduction")
    aproval = ForeignKey("User")
    cobrar = BoolCol(default=True)
    acumulado = CurrencyCol(default=0)

    def percent(self):

        """Calcula cuanto de la deuda se ha cubierto con los pagos"""

        x = (Decimal(self.debt) * Decimal(100)).quantize(dot01)
        total = x / Decimal(self.capital).quantize(dot01)
        return total

    def mora_mensual(self):

        """Calcula el monto que se acumula mensualmente por mora"""

        return self.debt * Decimal("0.02")

    def inicio_mora(self):

        """Calcula la fecha de inicio de cobro de intereses moratorios de
        manera.
        Utiliza la fecha de inicio de mora almacenada en el prestamo en caso
        que esta sea mayor que la fecha en que se inició.
        """

        ultimo = calendar.monthrange(self.fecha_mora.year,
                                     self.fecha_mora.month)[1]
        inicio = date(self.fecha_mora.year, self.fecha_mora.month, ultimo)

        if self.startDate < inicio:
            return self.fecha_mora

        return self.startDate

    def prediccion_pagos_actuales(self):

        """Calcula la cantidad de pagos que el :class:`Loan` deberia tener a
        la fecha de hoy
        """

        return (date.today() - self.inicio_mora()).days / 30

    def pagos_en_mora(self):

        """Calcula la cantidad de pagos que el :class:`Affiliate` no ha
        efectuado desde que se le otorgo el :class:`Loan`"""

        # pagos = self.prediccion_pagos_actuales()
        # Utilizar el número de pagos almacenado, para evitar calcular intereses
        # sobre cuotas pagadas y eliminadas accidentalmente.
        # total = pagos - self.number - 1

        # if total < 0:
        #    return 0

        # return total
        pagos = self.__pago_retrasado() / self.payment
        if pagos < 0:
            return 0

        return pagos

    def __pago_retrasado(self):

        """"Calcula el monto retrasado en base a los pagos en mora"""

        # Disminuir en un mes los pagos requeridos para dar un periodo de gracia
        # debido a retrasos o errores en el sistema, incluyendo aquellos
        # ocasionados por instituciones externas
        monto_proyectado = self.payment * (self.prediccion_pagos_actuales() - 1)
        return monto_proyectado - self.pagado()

    def pago_retrasado(self):

        """Muestra el monto debido en cantidades vencidas a la fecha

        Difiere de :function:__pago_retrasado en que se limitá a calcular hasta
        el monto nominal del :class:`Loan` con sus intereses normales.
        """

        cantidad_pagos = self.prediccion_pagos_actuales() - 1
        if cantidad_pagos > self.months:
            cantidad_pagos = self.months
        monto_proyectado = self.payment * cantidad_pagos
        pago = monto_proyectado - self.pagado()
        if pago < 0:
            return 0
        return pago

    def pago_adelantado(self):

        """Calcula la cantidad monetaria que se ha pagado de forma anticipada"""

        pago = -self.__pago_retrasado()
        if pago < 0:
            return 0
        return pago

    def obtener_mora(self):

        """Calcula el monto a pagar por mora en la siguiente cuota"""

        if self.__pago_retrasado() < 0:
            return 0

        return self.mora_mensual() * self.pagos_en_mora()

    def get_payment(self):

        """Obtiene el cobro a efectuar del prestamo"""

        # if self.debt < self.payment and self.number != self.months - 1:
        #    return self.debt

        return self.payment

    def start(self):

        """Inicia el saldo del préstamo al capital"""

        self.debt = self.capital

    def pagar(self, amount, receipt, day=date.today(), libre=False, remove=True,
              deposito=False, descripcion=None):

        """Carga un nuevo pago para el préstamo

        Dependiendo de si se marca como libre de intereses o no, calculará el
        interés compuesto a pagar.

        En caso de ingresar un pago mayor que la deuda actual del préstamo,
        ingresará el sobrante como intereses y marcará el préstamo como
        pagado.

        :param amount:      El monto pagado
        :param receipt:     Código del comprobante de pago
        :param day:         Fecha en que se realiza el pago
        :param libre:       Indica si el pago contabilizará intereses
        :param remove:      Indica si el pago permitirá que el :class:`Loan`
                            sea enviado a :class:`LoanPayed`
        :param deposito:    Indica si el pago fue un deposito efectuado en banco
        :param descripcion: Una descripción sobre la naturaleza del pago
        """

        kw = dict()
        kw['amount'] = amount = Decimal(amount).quantize(dot01)
        kw['day'] = day
        kw['receipt'] = receipt
        kw['loan'] = self
        kw['deposito'] = deposito
        kw['description'] = descripcion

        # La cantidad a pagar es igual que la deuda del préstamo, por
        # lo tanto se considera la ultima cuota y no se cargaran intereses
        if (self.debt == amount):

            self.last = kw['day']
            kw['capital'] = kw['amount']
            kw['interest'] = 0
            # Register the payment in the database
            Pay(**kw)
            # Remove the loan and convert it to PayedLoan
            if remove:
                self.remove()
            else:
                self.debt -= kw['amount']
            return True

        if libre:
            kw['interest'] = 0
        else:
            kw['interest'] = (self.debt * self.interest / 1200).quantize(dot01)

        # Registra cualquier cantidad mayor a los intereses
        if self.debt < amount:
            kw['interest'] = amount - self.debt

        # Calculate how much money was used to pay the capital
        kw['capital'] = kw['amount'] - kw['interest']
        # Decrease debt by the amount of the payed capital
        self.debt -= kw['capital']
        # Change the last payment date
        # if day.date > self.last:
        self.last = day
        # Register the payment in the database
        Pay(**kw)
        # Increase the number of payments by one
        self.number += 1

        if self.debt <= 0 and remove:
            self.remove()
            return True

        self.compensar()

        return False

    def refinanciar(self, pago, solicitud, cuenta, usuario, descripcion):

        self.pagar(pago, "Liquidacion", solicitud.entrega, True)

        prestamo = solicitud.prestamo(usuario)

        kw = {'account': cuenta, 'amount': pago, 'loan': prestamo,
              'description': descripcion, 'name': cuenta.name}

        Deduction(**kw)

        return prestamo

    def calibrar(self):

        """Permite que los :class:`Pay` efectuados al :class:`Loan` esten
        ordenados en cuanto al valor de su monto en capital e intereses"""

        pagos = map(Pay.calibrar, self.pays)
        fechas = list()
        result = False
        self.debt = self.capital
        for pago in pagos:

            result = self.pagar(amount=pago[1], receipt=pago[2], day=pago[0],
                                descripcion=pago[3])
            fechas.append(pago[0])
            if result:
                break

        if result:
            pagos = filter((lambda p: not p[0] in fechas), pagos)
            for pago in pagos:
                comment = "Sobrante de {0} del pago efectuado el {1}".format(
                    pago[1], pago[0].strftime('%d de %B de %Y'))

                Observacion(affiliate=self.affiliate, texto=comment,
                            fecha=date.today())

    def net(self):

        """Obtains the amount that was given to the affiliate in the check"""

        return self.capital - sum(d.amount for d in self.deductions)

    def total_deductions(self):

        """Muestra el total de las :class:`Deduction` efectuadas a este
        :class:`Loan`"""

        return sum(d.amount for d in self.deductions)

    def remove(self):

        """Convierte un :class:`Loan` en un :class:`PayedLoan`"""

        kw = {'id': self.id, 'affiliate': self.affiliate,
              'capital': self.capital, 'letters': self.letters,
              'interest': self.interest, 'months': self.months,
              'last': self.last, 'startDate': self.startDate,
              'payment': self.payment, 'casa': self.casa}
        payed = PayedLoan(**kw)

        for pay in self.pays:
            pay.remove(payed)

        for deduction in self.deductions:
            deduction.remove(payed)

        self.destroySelf()

        return payed

    def vencimiento(self):

        return self.startDate + relativedelta(months=+self.months)

    def calcular_vencidas(self):

        return (date.today() - self.startDate).days / 30

    def interes_acumulado(self, meses):

        debt = copy.copy(self.debt)
        int_month = self.interest / 1200
        total_interest = Zero
        for n in range(0, meses):

            if debt <= 0:
                break

            interest = Decimal(debt * int_month).quantize(dot01)
            debt = debt + interest - self.payment
            total_interest += interest

        return total_interest

    def future(self):

        """Calcula la manera en que se pagará el préstamo basado en los
        intereses y los pagos actuales"""

        debt = copy.copy(self.debt)
        li = list()
        start = self.startDate.month + self.offset
        if self.startDate.day == 24 and self.startDate.month == 8:
            start += 1
        year = self.startDate.year
        n = 1
        int_month = self.interest / 1200
        while debt > 0:
            kw = {'number': "{0}/{1}".format(n + self.number, self.months),
                  'month': self.number + n + start, 'enum': self.number + n,
                  'year': year}
            # calcular el número de pago

            # Normalizar Meses
            while kw['month'] > 12:
                kw['month'] -= 12
                kw['year'] += 1

            # colocar el mes y el año
            kw['month'] = "{0} {1}".format(months[kw['month']], kw['year'])
            # calcular intereses
            kw['interest'] = Decimal(debt * int_month).quantize(dot01)

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
            n += 1

        return li

    def compensar(self):

        """Recalcula la deuda final utilizando el calculo de pagos futuros
        para evitar perdidas por pagos finales menores a la cuota de préstamo
        pero que deberian mantenerse en el valor de la cuota de préstamo"""

        futuro = self.future()
        if futuro == list():
            return

        ultimo_pago = futuro[-1]['payment']
        ultimo_mes = futuro[-1]['enum']
        if ultimo_pago < self.payment and ultimo_mes == self.months:
            self.debt += ((self.payment - ultimo_pago) * 2 / 3).quantize(dot01)

    def totaldebt(self):

        """Muestra el valor total de la deuda"""

        return self.debt

    def capitalPagado(self):

        """Muestra el valor del capital pagado del :class:`Loan`"""

        return self.pays.sum('capital')

    def pagado(self):

        """Muestra el monto total pagado a este :class:`Loan`"""

        return self.pays.sum('amount')

    def interesesPagados(self):

        return self.pays.sum('interest')

    def reconstruirSaldo(self):

        """Recalcula el valor de la deuda del préstamo en base a los pagos
        efectuados"""

        self.debt = self.capital - self.capitalPagado()


class Pay(SQLObject):
    """Pagos que se han efectuado a un :class:`Loan`

    @DynamicAttrs
    """

    loan = ForeignKey("Loan")
    day = DateCol(default=date.today)
    capital = CurrencyCol(default=0, notNone=True)
    interest = CurrencyCol(default=0, notNone=True)
    amount = CurrencyCol(default=0, notNone=True)
    deposito = BoolCol(default=False)
    receipt = UnicodeCol(length=50)
    description = UnicodeCol(length=100)

    def remove(self, payedLoan):
        kw = {'payedLoan': payedLoan, 'day': self.day, 'capital': self.capital,
              'interest': self.interest, 'amount': self.amount,
              'receipt': self.receipt, 'description': self.description}
        self.destroySelf()
        OldPay(**kw)

    def revert(self):
        self.loan.debt = self.loan.capital - self.loan.capitalPagado() \
                         + self.capital
        self.loan.number -= 1
        self.destroySelf()

    def calibrar(self):
        dia = self.day
        monto = self.amount
        recibo = self.receipt
        descripcion = self.description
        self.revert()
        return dia, monto, recibo, descripcion


class Account(SQLObject):
    """Simple Account made for affiliate handling"""

    name = UnicodeCol()
    loan = BoolCol(default=False)
    extras = MultipleJoin("Extra")
    retrasadas = MultipleJoin("CuentaRetrasada")
    distributions = MultipleJoin("Distribution")


class Distribution(SQLObject):
    account = ForeignKey("Account")
    name = UnicodeCol()
    amount = CurrencyCol(default=0)


class Extra(SQLObject):
    """Represents a Deduction that will be made"""

    affiliate = ForeignKey("Affiliate")
    amount = CurrencyCol(default=0)
    months = IntCol(default=1)
    retrasada = BoolCol(default=False)
    account = ForeignKey("Account")
    mes = IntCol(default=None)
    anio = IntCol(default=None)

    def act(self, decrementar=True, day=date.today(), banco=False,
            cobro=date.today()):

        """Registra que la deducción se efectuó y disminuye la cantidad"""

        if banco:
            self.deduccion_bancaria(day, cobro)
        else:
            self.to_deduced(day=day)

        if decrementar and self.months == 1:
            self.destroySelf()
        if decrementar:
            self.months -= 1
        if self.months == 0:
            self.destroySelf()

    def to_deduced(self, day=date.today()):

        """Registra la deducción convirtiendola en :class:`Deduced`"""

        kw = {'amount': self.amount, 'affiliate': self.affiliate,
              'account': self.account, 'cotizacion': self.affiliate.cotizacion,
              'month': day.month, 'year': day.year}

        if self.retrasada:

            cuota = self.affiliate.get_delayed()
            month, year = (None, None)
            if cuota is not None:
                month = cuota.delayed()
                year = cuota.year
                cuota.pay_month(month)
            kw['detail'] = "Cuota Retrasada {0} de {1}".format(month, year)

        Deduced(**kw)

    def deduccion_bancaria(self, dia=date.today(), cobro=date.today()):

        kw = {'amount': self.amount, 'afiliado': self.affiliate,
              'banco': self.affiliate.get_banco(), 'account': self.account,
              'month': dia.month, 'year': dia.year, 'day': cobro}

        if self.retrasada:

            cuota = self.affiliate.get_delayed()
            month, year = (None, None)
            if cuota is not None:
                month = cuota.delayed()
                year = cuota.year
                cuota.pay_month(month)
            kw['detail'] = "Cuota Retrasada {0} de {1}".format(month, year)

        DeduccionBancaria(**kw)

    def manual(self):

        self.act()


class Deduction(SQLObject):
    loan = ForeignKey("Loan")
    amount = CurrencyCol()
    account = ForeignKey("Account")
    description = UnicodeCol(length=100)

    def remove(self, payedLoan):
        kw = {'payedLoan': payedLoan, 'amount': self.amount,
              'account': self.account, 'description': self.description}
        PayedDeduction(**kw)
        self.destroySelf()


class PayedLoan(SQLObject):
    """Representa un :class:`Loan` al que ya se le han efectuado pagos
    suficientes para cubrir su capital

    @DynamicAttrs
    """

    affiliate = ForeignKey("Affiliate")
    casa = ForeignKey("Casa")
    capital = CurrencyCol(default=0, notNone=True)
    letters = StringCol()
    payment = CurrencyCol(default=0, notNone=True)
    interest = DecimalCol(default=20, notNone=True, size=4, precision=2)
    months = IntCol()
    last = DateCol(default=date.today)
    startDate = DateCol(notNone=True, default=date.today)
    pays = SQLMultipleJoin("OldPay")
    deductions = SQLMultipleJoin("PayedDeduction")
    debt = CurrencyCol(default=0, notNone=True)

    def remove(self):
        [pay.destroySelf() for pay in self.pays]
        [deduction.destroySelf() for deduction in self.deductions]
        self.destroySelf()

    def to_loan(self, user):
        kw = {'aproval': user, 'affiliate': self.affiliate,
              'capital': self.capital, 'interest': self.interest,
              'payment': self.payment, 'months': self.months, 'last': self.last,
              'startDate': self.startDate, 'letters': self.letters,
              'number': self.pays.count(), 'id': self.id, 'casa': self.casa}
        loan = Loan(**kw)

        [pay.to_pay(loan) for pay in self.pays]
        [deduction.to_deduction(loan) for deduction in self.deductions]

        self.destroySelf()
        return loan

    def net(self):
        """Obtains the amount that was given to the affiliate in the check"""

        return self.capital - self.deductions.sum('amount')

    def capitalPagado(self):
        return self.pays.sum('capital')

    def pagado(self):
        return self.pays.sum('amount')

    def interesesPagados(self):
        return self.pays.sum('interest')


class OldPay(SQLObject):
    """Pagos que se han efectuado a un :class:`PayedLoan`

    @DynamicAttrs
    """

    payedLoan = ForeignKey("PayedLoan")
    day = DateCol(default=date.today)
    capital = CurrencyCol(default=0, notNone=True)
    interest = CurrencyCol(default=0, notNone=True)
    amount = CurrencyCol(default=0, notNone=True)
    receipt = UnicodeCol(length=50)
    description = UnicodeCol(length=100)

    def to_pay(self, loan):
        kw = {'loan': loan, 'day': self.day, 'capital': self.capital,
              'interest': self.interest, 'amount': self.amount,
              'receipt': self.receipt, 'description': self.description}
        Pay(**kw)
        self.destroySelf()


class PayedDeduction(SQLObject):
    payedLoan = ForeignKey("PayedLoan")
    amount = CurrencyCol()
    account = ForeignKey("Account")
    description = StringCol()

    def to_deduction(self, loan):
        kw = {'loan': loan, 'amount': self.amount,
              'description': self.description, 'account': self.account}
        Deduction(**kw)
        self.destroySelf()


class Obligation(SQLObject):
    """The description of the Cuota payment"""

    name = UnicodeCol(length=50)
    amount = CurrencyCol(default=0, notNone=True)
    inprema = CurrencyCol(default=0, notNone=True)
    month = IntCol()
    year = IntCol()
    account = ForeignKey("Account")
    filiales = CurrencyCol(default=4, notNone=True)
    inprema_compliment = CurrencyCol(default=0, notNone=True)
    amount_compliment = CurrencyCol(default=0, notNone=True)
    alternate = CurrencyCol(default=0, notNone=True)


class ReportAccount(SQLObject):
    name = UnicodeCol(length=100)
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
    cotizacion = ForeignKey("Cotizacion")
    amount = CurrencyCol(default=0)
    account = ForeignKey("Account")
    detail = UnicodeCol(default="")
    month = IntCol(default=date.today().month)
    year = IntCol(default=date.today().year)


class OtherReport(SQLObject):
    year = IntCol()
    month = IntCol()
    otherAccounts = MultipleJoin("OtherAccount")
    cotizacion = ForeignKey("Cotizacion")

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


class BankReport(SQLObject):
    year = IntCol()
    month = IntCol()
    bankAccounts = MultipleJoin("BankAccount")
    banco = ForeignKey("Banco")

    def total(self):
        return sum(r.amount for r in self.otherAccounts)


class BankAccount(SQLObject):
    account = ForeignKey("Account")
    amount = CurrencyCol(default=0)
    bankReport = ForeignKey("BankReport")

    def add(self, amount):
        self.amount += amount
        self.quantity += 1


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

        kw = {'aproval': user, 'affiliate': self.affiliate,
              'capital': self.monto, 'interest': 20, 'payment': cuota,
              'months': self.periodo, 'last': self.entrega,
              'startDate': self.entrega, 'number': 0}
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
    formaPago = ForeignKey("FormaPago")
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
        self.cancelacion = dia

    def deduccion(self, dia=date.today()):
        """Efectua el pago del :class:`Reintegro` mediante una planilla"""

        self.cancelar(dia)
        self.formaPago = FormaPago.get(1)

        kw = {'amount': self.monto, 'affiliate': self.affiliate,
              'account': self.cuenta, 'month': dia.month, 'year': dia.year,
              'detail': "Reintegro {0} por {0}".format(
                  self.emision.strftime('%d/%m/%Y'),
                  self.motivo)}

        Deduced(**kw)

    def deduccion_bancaria(self, dia=date.today(), cobro=date.today()):
        self.cancelar(dia)
        self.formaPago = FormaPago.get(1)

        kw = {'amount': self.monto, 'afiliado': self.affiliate,
              'banco': self.affiliate.get_banco(), 'account': self.cuenta,
              'month': dia.month, 'year': dia.year, 'day': cobro,
              'detail': "Reintegro {0} por {0}".format(
                  self.emision.strftime('%d/%m/%Y'),
                  self.motivo)}

        DeduccionBancaria(**kw)

    def revertir(self):
        """Revierte el pago del :class:`Reintegro`"""

        self.pagado = False


class Sobrevivencia(SQLObject):
    afiliado = ForeignKey("Affiliate")
    fecha = DateCol(default=date.today)
    monto = CurrencyCol(default=0)
    cheque = UnicodeCol(length=20, default=None)
    banco = UnicodeCol(length=50)


class Devolucion(SQLObject):
    afiliado = ForeignKey("Affiliate")
    """:class:`Afiliado` a quien se entrega"""
    concepto = UnicodeCol(length=200)
    """razon por la que se entrega la devolucion"""
    fecha = DateCol(default=date.today)
    """Día en cual se entrego el cheque"""
    monto = CurrencyCol()
    """Monto entregado"""
    cheque = UnicodeCol(length=20)
    """Referencia al cheque emitido"""
    banco = UnicodeCol(length=50)


class Funebre(SQLObject):
    """Ayuda funebre en caso de fallecimiento de un familiar"""

    class sqlmeta:
        table = 'ayuda_funebre'

    afiliado = ForeignKey("Affiliate")
    """:class:`Afiliado` a quien se entrega"""
    fecha = DateCol(default=date.today)
    """Día en cual se entrego el cheque"""
    monto = CurrencyCol()
    """Cantidad que se entrego"""
    cheque = UnicodeCol(length=20)
    """Referencia al cheque emitido"""
    pariente = UnicodeCol(length=100)
    """Familiar que fallecio"""
    banco = UnicodeCol(length=50)


class Indemnizacion(SQLObject):
    nombre = UnicodeCol(length=50)
    seguros = MultipleJoin("Seguro")


class Seguro(SQLObject):
    afiliado = MultipleJoin("Affiliate")
    indemnizacion = ForeignKey("Indemnizacion")
    fecha = DateCol(default=datetime.now)
    fallecimiento = DateCol(default=datetime.now)
    beneficiarios = MultipleJoin("Beneficiario")

    def monto(self):
        return sum(beneficiario.monto for beneficiario in self.beneficiarios)


class Beneficiario(SQLObject):
    seguro = ForeignKey("Seguro")
    nombre = UnicodeCol(length=50)
    monto = CurrencyCol()
    cheque = UnicodeCol(length=20)
    banco = UnicodeCol(length=50)
    fecha = DateCol(default=datetime.now)


class Asamblea(SQLObject):
    """Representación de asambleas efectuadas por la organización"""

    numero = IntCol()
    nombre = UnicodeCol(length=100)
    departamento = ForeignKey('Departamento')
    habilitado = BoolCol(default=False)
    fecha = DateCol(default=date.today)
    inscripciones = MultipleJoin('Inscripcion')


class Banco(SQLObject):
    """Instituciones bancarías a través de las cuales se efectuan los pagos de
    :class:`Viaticos`"""

    nombre = UnicodeCol(length=100)
    depositable = BoolCol(default=False)
    asambleista = BoolCol(default=False)
    parser = UnicodeCol(length=100, default=None)
    generator = UnicodeCol(length=100, default=None)
    cuenta = UnicodeCol(length=100, default=None)
    codigo = UnicodeCol(length=100, default=None)
    cuota = BoolCol(default=True)
    depositos = MultipleJoin("Deposito")
    depositosAnonimos = MultipleJoin("DepositoAnonimo")


class Viatico(SQLObject):
    """Describe las cantidades a pagar por departamento para cada
    :class:`Asamblea`"""

    asamblea = ForeignKey('Asamblea')
    municipio = ForeignKey('Municipio')
    monto = CurrencyCol()
    transporte = CurrencyCol()
    previo = CurrencyCol()
    posterior = CurrencyCol()
    inscripciones = MultipleJoin('Inscripcion')


class Inscripcion(SQLObject):
    """Pagos a efectuar por concepto de :class:`Viaticos` a un
    :class:`Affiliate`"""

    afiliado = ForeignKey('Affiliate')
    """:class:`Afiliado` que se inscribio"""
    asamblea = ForeignKey('Asamblea')
    viatico = ForeignKey('Viatico')
    enviado = BoolCol(default=False)
    envio = DateCol(default=date.today)
    ingresado = DateTimeCol(default=datetime.now)

    def reenviable(self):

        """Indica si la inscripcion puede ser enviada de nuevo"""

        return self.asamblea.habilitado

    def monto(self):

        """Obtiene el monto a pagar por concepto de viaticos"""

        if self.asamblea.fecha is None or self.ingresado is None:
            return self.viatico.monto

        if self.ingresado < self.asamblea.fecha:
            return self.viatico.transporte + self.viatico.previo

        return self.viatico.transporte + self.viatico.posterior


class Deposito(SQLObject):
    """Pagos efectuados mediante un deposito bancario

    @DynamicAttrs
    """

    afiliado = ForeignKey("Affiliate")
    """:class:`Afiliado` que realizó el :class:`Deposito`"""
    banco = ForeignKey("Banco")
    concepto = UnicodeCol(length=50)
    fecha = DateCol(default=date.today)
    posteo = DateCol(default=date.today)
    monto = CurrencyCol()
    descripcion = UnicodeCol(length=100)


class DepositoAnonimo(SQLObject):
    """Depositos efectuados en el :class:`Banco` que no pueden ser rastreados
    a su depositante

    @DynamicAttrs"""

    referencia = UnicodeCol(length=100)
    banco = ForeignKey("Banco")
    concepto = UnicodeCol(length=50)
    fecha = DateCol(default=date.today)
    monto = CurrencyCol()


class DeduccionBancaria(SQLObject):
    afiliado = ForeignKey("Affiliate")
    banco = ForeignKey("Banco")
    account = ForeignKey("Account")
    amount = CurrencyCol()
    detail = UnicodeCol(default="")
    day = DateCol(default=date.today)
    month = IntCol(default=date.today().month)
    year = IntCol(default=date.today().year)

    def consolidar(self):
        deducciones = DeduccionBancaria.selectBy(afiliado=self.afiliado,
                                                 month=self.month,
                                                 year=self.year,
                                                 banco=self.banco)

        return sum(d.amount for d in deducciones)


class ReporteBancario(SQLObject):
    banco = ForeignKey("Banco")
    day = DateCol(default=date.today)
    month = IntCol(default=date.today().month)
    year = IntCol(default=date.today().year)


class DetalleBancario(SQLObject):
    reporte = ForeignKey("ReporteBancario")
    account = ForeignKey("Account")
    amount = CurrencyCol()


class CobroBancarioBanhcafe(SQLObject):
    identidad = UnicodeCol(length=13)
    cantidad = CurrencyCol()
    consumido = BoolCol(default=False)


class PagoBancarioBanhcafe(SQLObject):
    identidad = UnicodeCol(length=13)
    cantidad = CurrencyCol()
    aplicado = DateTimeCol(default=datetime.now)
    fecha = DateTimeCol(default=datetime.now)
    referencia = IntCol()
    agencia = IntCol()
    cajero = UnicodeCol(length=10)
    terminal = UnicodeCol(length=1)
    aplicado = BoolCol(default=False)


class ReversionBancariaBanhcafe():
    fecha = DateTimeCol(default=datetime.now)
    referencia = IntCol()
    agencia = IntCol()
    cajero = UnicodeCol(length=10)
    terminal = UnicodeCol(length=10)
    cajero = UnicodeCol(length=10)


class Recibo(SQLObject):
    casa = ForeignKey("Casa")
    afiliado = IntCol()
    cliente = UnicodeCol()
    dia = DateTimeCol()
    # Marca si el recibo ya ha sido impreso
    impreso = BoolCol()
    ventas = MultipleJoin("Venta")

    def total(self):
        """Retorna el total de las ventas de un recibo"""

        return sum(venta.valor() for venta in self.ventas)


class Venta(SQLObject):
    """Descripción de Venta

    Contiene los datos sobre la venta de determinado producto en un recibo."""

    recibo = ForeignKey("Recibo")
    producto = ForeignKey("Producto")
    descripcion = UnicodeCol()
    cantidad = IntCol()
    # No siempre el precio unitario esta determinado por el precio nominal de un
    # producto, este puede cambiar como en el caso de los préstamos
    unitario = CurrencyCol()

    def valor(self):
        """Retorna el total de una venta"""

        return self.cantidad * self.unitario


class Producto(SQLObject):
    """Servicios u Objetos a la venta

    Guarda los datos de productos que se tienen a la disposición de los
    afiliados."""

    nombre = UnicodeCol()
    descripcion = UnicodeCol()


class ReciboSPS(SQLObject):
    class sqlmeta:
        table = "recibo_sps"

    casa = ForeignKey("Casa")
    afiliado = IntCol()
    cliente = UnicodeCol()
    dia = DateTimeCol()
    # Marca si el recibo ya ha sido impreso
    impreso = BoolCol()
    ventas = MultipleJoin("VentaSPS", joinColumn="recibo_id")

    def total(self):
        """Retorna el total de las ventas de un recibo"""

        return sum(venta.valor() for venta in self.ventas)


class VentaSPS(SQLObject):
    """Descripción de Venta

    Contiene los datos sobre la venta de determinado producto en un recibo."""

    class sqlmeta:
        table = "venta_sps"

    recibo = ForeignKey("ReciboSPS")
    producto = ForeignKey("Producto")
    descripcion = UnicodeCol()
    cantidad = IntCol()
    # No siempre el precio unitario esta determinado por el precio nominal de un
    # producto, este puede cambiar como en el caso de los préstamos
    unitario = CurrencyCol()

    def valor(self):
        """Retorna el total de una venta"""

        return self.cantidad * self.unitario


class ReciboCeiba(SQLObject):
    class sqlmeta:
        table = "recibo_ceiba"

    casa = ForeignKey("Casa")
    afiliado = IntCol()
    cliente = UnicodeCol()
    dia = DateTimeCol()
    # Marca si el recibo ya ha sido impreso
    impreso = BoolCol()
    ventas = MultipleJoin("VentaCeiba", joinColumn="recibo_id")

    def total(self):
        """Retorna el total de las ventas de un recibo"""

        return sum(venta.valor() for venta in self.ventas)


class VentaCeiba(SQLObject):
    """Descripción de Venta

    Contiene los datos sobre la venta de determinado producto en un recibo."""

    class sqlmeta:
        table = "venta_ceiba"

    recibo = ForeignKey("ReciboCeiba")
    producto = ForeignKey("Producto")
    descripcion = UnicodeCol()
    cantidad = IntCol()
    # No siempre el precio unitario esta determinado por el precio nominal de un
    # producto, este puede cambiar como en el caso de los préstamos
    unitario = CurrencyCol()

    def valor(self):
        """Retorna el total de una venta"""

        return self.cantidad * self.unitario


class Rechazo(SQLObject):
    """Permite registrar la razón de un rechazo de débito automático"""
    affiliate = ForeignKey("Affiliate")
    reason = UnicodeCol()
    day = DateCol(default=date.today)
