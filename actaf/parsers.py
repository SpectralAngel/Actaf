# -*- coding: utf8 -*-
#
# parsers.py
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

import database
import core


class Actualizador(object):
    """Actualiza estados de cuenta de acuerdo a los datos entregados por
    :class:`Ingreso` registrando los motivos por los cuales se efectuó un
    determinado cobro"""

    def __init__(self, obligacion, accounts, day, banco, cobro,
                 jubilados, alternativos):

        self.obligacion = obligacion
        self.cuentas = accounts
        self.day = day
        self.banco = banco
        self.cobro = cobro
        self.jubilados = jubilados
        self.alternativos = alternativos
        self.registro = dict()

    def registrar_cuenta(self, account, name):

        """Registra una cuenta para usarla como destino especifico"""

        self.registro[name] = account

    def aditional(self, ingreso):
        self.extra(ingreso)
        map((lambda r: self.reintegros(r, ingreso)),
            ingreso.afiliado.reintegros)
        map((lambda p: self.prestamo(p, ingreso)), ingreso.afiliado.loans)
        if ingreso.cantidad > 0:
            self.excedente(ingreso)

    def update(self, ingreso, cuota=True):

        """Actualiza el estado de cuenta de acuerdo a un :class:`Ingreso`"""
        if cuota:
            if ingreso.afiliado.cotizacion.jubilados or \
                    ingreso.afiliado.cotizacion.alternate:
                self.complemento(ingreso)
            else:
                self.cuota(ingreso)
        self.aditional(ingreso)

    def cuota(self, ingreso):

        """Acredita la cuota de aportacion en el estado de cuenta"""

        if ingreso.cantidad >= self.obligacion:
            self.cuentas[self.registro['cuota']]['amount'] += self.obligacion
            self.cuentas[self.registro['cuota']]['number'] += 1
            # afiliado = database.get_affiliate(ingreso.afiliado.id)
            ingreso.afiliado.pay_cuota(self.day.year, self.day.month)
            ingreso.cantidad -= self.obligacion
            database.create_bank_deduction(ingreso.afiliado, self.obligacion,
                                           self.registro['cuota'], self.banco,
                                           self.day, self.cobro)

    def reintegros(self, reintegro, ingreso):

        """Acredita los reintegros en el estado de cuenta"""

        if ingreso >= reintegro.monto and not reintegro.pagado:
            ingreso.cantidad -= reintegro.monto
            self.cuentas[reintegro.cuenta]['amount'] += reintegro.monto
            self.cuentas[reintegro.cuenta]['number'] += 1
            reintegro.deduccion_bancaria(self.day, self.cobro)

    def procesar_extra(self, extra, ingreso, disminuir=False):

        """Ingresa los pagos de una deducción extra"""

        if disminuir:
            if ingreso.cantidad >= extra.amount:
                ingreso.cantidad -= extra.amount
            else:
                return

        self.cuentas[extra.account]['amount'] += extra.amount
        self.cuentas[extra.account]['number'] += 1
        extra.act(True, self.day, True, self.cobro)

    def extra(self, ingreso):

        """Acredita las deducciones extra en el estado de cuenta"""
        map((lambda e: self.procesar_extra(e, ingreso, True)),
            ingreso.afiliado.extras)

    def excedente(self, ingreso):

        """Guarda registro acerca de las cantidades extra que han sido deducidas
        por el sistema, estas serán las devoluciones a efectuar en el mes."""

        self.cuentas[self.registro['excedente']]['amount'] += ingreso.cantidad
        self.cuentas[self.registro['excedente']]['number'] += 1
        database.create_bank_deduction(ingreso.afiliado, ingreso.cantidad,
                                       self.registro['excedente'], self.banco,
                                       self.day, self.cobro)

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
            database.create_bank_deduction(ingreso.afiliado, payment,
                                           self.registro['prestamo'],
                                           self.banco, self.day)
        # Cobrar lo que queda en las deducciones y marcalo como cuota incompleta
        # de prestamo
        else:
            database.efectuar_pago(prestamo, ingreso.cantidad, self.day)
            self.cuentas[self.registro['incomplete']][
                'amount'] += ingreso.cantidad
            self.cuentas[self.registro['incomplete']]['number'] += 1
            database.create_bank_deduction(ingreso.afiliado, ingreso.cantidad,
                                           self.registro['incomplete'],
                                           self.banco, self.day, self.cobro)
            ingreso.cantidad = 0

    def complemento(self, ingreso):

        if ingreso.afiliado.cotizacion.alternate:
            complemento = self.alternativos
        if ingreso.afiliado.cotizacion.jubilados:
            complemento = self.jubilados

        if ingreso.cantidad >= complemento:
            self.cuentas[self.registro['complemento']]['amount'] += complemento
            self.cuentas[self.registro['complemento']]['number'] += 1
            ingreso.afiliado.pay_compliment(self.day.year, self.day.month)
            ingreso.cantidad -= complemento
            database.create_bank_deduction(ingreso.afiliado, complemento,
                                           self.registro['complemento'],
                                           self.banco,
                                           self.day)


class Parser(object):
    def __init__(self, fecha, archivo, banco):
        self.archivo = archivo
        self.fecha = fecha
        self.banco = banco
        self.afiliados = database.get_affiliates_by_banco(self.banco)

    def output(self):
        self.analizador = core.AnalizadorCSV(self.archivo, self.afiliados)
        return self.analizador.parse()


class Occidente(Parser):
    def __init__(self, fecha, archivo, banco):
        super(Occidente, self).__init__(fecha, archivo, banco)

    def output(self):
        self.analizador = core.AnalizadorCSV(self.archivo, self.afiliados, True)
        return self.analizador.parse()


class Atlantida(Parser):
    def __init__(self, fecha, archivo, banco):
        super(Atlantida, self).__init__(fecha, archivo, banco)

    def output(self):
        self.analizador = core.AnalizadorCSV(self.archivo, self.afiliados, True)
        return self.analizador.parse()


class DaVivienda(Parser):
    def __init__(self, fecha, archivo, banco):
        super(DaVivienda, self).__init__(fecha, archivo, banco)

    def output(self):
        self.analizador = core.AnalizadorCSV(self.archivo, self.afiliados)
        return self.analizador.parse()


class Ficensa(Parser):
    def __init__(self, fecha, archivo, banco):
        super(Ficensa, self).__init__(fecha, archivo, banco)

    def output(self):
        self.analizador = core.AnalizadorCSV(self.archivo, self.afiliados, True)
        return self.analizador.parse()
