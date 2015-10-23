# -*- coding: utf8 -*-
#
# core.py
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

from decimal import Decimal
import csv
from collections import defaultdict
from sqlobject import sqlhub

import database
import retrasadas

hundred = Decimal("100")
complemento = Decimal("178.68")


class Ingreso(object):
    """Almacena el afiliado y la deduccion realizada para registrar los cobros
    en el sistema"""

    def __init__(self, afiliado, cantidad):
        self.afiliado, self.cantidad = (afiliado, cantidad)


class AnalizadorEscalafon(object):
    """Extrae los datos de la planilla de Escalafon y los convierte en
    una representación interna de los cobros"""

    def __init__(self, filename, affiliates):

        self.file = open(filename)
        self.affiliates = dict()
        for a in affiliates:
            self.affiliates[a.cardID] = a

        self.parsed = list()

    def parse(self):

        """Se encarga de tomar linea por linea cada uno de los codigos de
        Identidad y asignarle la cantidad deducida, entregandola en una lista
        de :class:`Ingreso`"""

        lines = filter((lambda l: l[89:93] == "0011"), self.file)
        matches = map(distribuir, lines)

        map((lambda l: self.match(l)), matches)
        return self.parsed

    def match(self, line):

        if line[0] in self.affiliates:
            self.parsed.append(Ingreso(self.affiliates[line[0]], line[1]))
        else:
            print(
                "Error de parseo no se encontro la identidad {0}".format(
                    line[0]))


def distribuir(line):
    return str(line[6:10] + '-' + line[10:14] + '-' + line[14:19]), Decimal(
        str(line[94:111])) / hundred


class AnalizadorCSV(object):
    def __init__(self, filename, affiliates, byID=False):

        self.reader = csv.reader(open(filename))
        self.affiliates = {}
        self.parsed = []
        self.perdidos = 0
        self.byID = byID
        if not byID:
            affiliates = filter((lambda a: a.cardID is not None), affiliates)
            for a in affiliates:
                self.affiliates[a.cardID.replace('-', '')] = a
        self.preparse = defaultdict(Decimal)

    def parse(self):

        """Se encarga de tomar linea por linea cada uno de los códigos de
        cobro y asignarle la cantidad deducida, entregandola en una lista
        de :class:`Ingreso`"""

        map((lambda r: self.single(r)), self.reader)

        for afiliado in self.preparse:
            self.parsed.append(Ingreso(afiliado, self.preparse[afiliado]))

        return self.parsed

    def single(self, row):

        amount = Decimal(row[2].replace(',', ''))
        afiliado = None
        if self.byID:
            afiliado = database.get_affiliate(int(row[0]))
            if not afiliado:
                self.perdidos += 1
                print("Error de parseo no se encontro la identidad {0}".format(
                    row[0]))
        else:
            identidad = '{0:013d}'.format(int(row[0].replace('-', '')))
            if identidad not in self.affiliates:
                self.perdidos += 1
                print("Error de parseo no se encontro la identidad {0}".format(
                    identidad))
            else:
                afiliado = self.affiliates[identidad]
        if afiliado:
            self.preparse[afiliado] += amount


class AnalizadorCSVSingle(AnalizadorCSV):
    def __init__(self, filename, byID=False):

        self.reader = csv.reader(open(filename))
        self.affiliates = dict()
        self.parsed = list()
        self.byID = byID

    def parse(self):

        return [self.single(row) for row in self.reader]

    def single(self, row):

        amount = Decimal(row[2].replace(',', ''))
        if self.byID:
            afiliado = database.get_affiliate(int(row[0]))
        else:
            cardID = '{0:013d}'.format(int(row[0].replace('-', '')))
            afiliado = database.get_affiliate_by_card_id(cardID)

        return Ingreso(afiliado, amount)


class AnalizadorINPREMA(object):
    """Extrae los datos de la planilla de INPREMA y los convierte en
    una representación interna de los cobros"""

    def __init__(self, filename, affiliates):

        self.reader = csv.reader(open(filename))
        self.affiliates = affiliates
        self.parsed = list()
        self.perdidos = 0

    def parse(self):

        """Se encarga de tomar linea por linea cada uno de los códigos de
        cobro y asignarle la cantidad deducida, entregandola en una lista
        de :class:`Ingreso`"""

        map((lambda r: self.single(r)), self.reader)

        print self.perdidos
        return self.parsed

    def single(self, row):

        amount = Decimal(row[2])
        cobro = int(row[0])
        try:
            self.parsed.append(Ingreso(self.affiliates[cobro], amount))

        except:
            self.perdidos += 1
            # print("Error de parseo no se encontro la identidad {0}".format(
            # cobro))


class Actualizador(object):
    """Actualiza estados de cuenta de acuerdo a los datos entregados por
    :class:`Ingreso` registrando los motivos por los cuales se efectuó un
    determinado cobro"""

    def __init__(self, obligacion, accounts, day):

        self.obligacion = obligacion
        self.cuentas = accounts
        self.day = day
        self.registro = {}

    def registrar_cuenta(self, account, name):

        """Registra una cuenta para usarla como destino especifico"""

        self.registro[name] = account

    def aditional(self, ingreso):

        """Efectua los pagos de un afiliado en el siguiente orden:

        1. Primero paga los préstamos
        2. Luego los cobros extra.
        3. Posteriormente las cuotas retrasdas
        4. Reintegros.
        """

        [self.prestamo(p, ingreso) for p in ingreso.afiliado.loans]
        self.extra(ingreso)
        [self.reintegros(r, ingreso) for r in ingreso.afiliado.reintegros]

        if ingreso.cantidad > 0:
            self.excedente(ingreso)

    def update(self, ingreso, cuota=True):

        """Actualiza el estado de cuenta de acuerdo a un :class:`Ingreso`"""
        conn = sqlhub.getConnection()
        transaction = conn.transaction()
        sqlhub.processConnection = transaction
        try:
            ingreso.afiliado.last = ingreso.cantidad

            if ingreso.cantidad == complemento:
                self.complemento(ingreso, complemento)
            else:
                self.cuota(ingreso)
            self.aditional(ingreso)
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise

    def cuota(self, ingreso):

        """Acredita la cuota de aportacion en el estado de cuenta"""

        if ingreso.cantidad >= self.obligacion:
            self.cuentas[self.registro['cuota']]['amount'] += self.obligacion
            self.cuentas[self.registro['cuota']]['number'] += 1
            # afiliado = database.get_affiliate(ingreso.afiliado.id)
            ingreso.afiliado.pay_cuota(self.day.year, self.day.month)
            ingreso.cantidad -= self.obligacion
            self.register_deduction(
                ingreso.afiliado, self.obligacion, self.registro['cuota']
            )

    def reintegros(self, reintegro, ingreso):

        """Acredita los reintegros en el estado de cuenta"""

        if ingreso >= reintegro.monto and not reintegro.pagado:
            ingreso.cantidad -= reintegro.monto
            self.cuentas[reintegro.cuenta]['amount'] += reintegro.monto
            self.cuentas[reintegro.cuenta]['number'] += 1

            self.register_deduction(
                reintegro.monto, ingreso.afiliado, reintegro.cuenta
            )

    def procesar_extra(self, extra, ingreso, disminuir=False):

        """Ingresa los pagos de una deducción extra"""

        if disminuir:
            if ingreso.cantidad >= extra.amount:
                ingreso.cantidad -= extra.amount
            else:
                return

        self.cuentas[extra.account]['amount'] += extra.amount
        self.cuentas[extra.account]['number'] += 1
        self.extra_act(extra)

    def extra_act(self, extra):
        extra.act(True, self.day)

    def extra(self, ingreso):

        """Acredita las deducciones extra en el estado de cuenta"""
        [self.procesar_extra(e, ingreso, True) for e in ingreso.afiliado.extras]

    def excedente(self, ingreso):

        """Guarda registro acerca de las cantidades extra que han sido deducidas
        por el sistema, estas serán las devoluciones a efectuar en el mes."""

        self.cuentas[self.registro['excedente']]['amount'] += ingreso.cantidad
        self.cuentas[self.registro['excedente']]['number'] += 1
        self.register_deduction(
            ingreso.afiliado, ingreso.cantidad, self.registro['excedente']
        )

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
            self.register_deduction(
                ingreso.afiliado, payment, self.registro['prestamo']
            )
        # Cobrar lo que queda en las deducciones y marcalo como cuota incompleta
        # de prestamo
        else:
            database.efectuar_pago(prestamo, ingreso.cantidad, self.day)
            self.cuentas[self.registro['incomplete']][
                'amount'] += ingreso.cantidad
            self.cuentas[self.registro['incomplete']]['number'] += 1
            self.register_deduction(ingreso.afiliado, ingreso.cantidad,
                                    self.registro['incomplete'])

    def complemento(self, ingreso, monto):

        if ingreso.cantidad >= monto:
            self.cuentas[self.registro['complemento']]['amount'] += monto
            self.cuentas[self.registro['complemento']]['number'] += 1
            ingreso.afiliado.pay_compliment(self.day.year, self.day.month)
            ingreso.cantidad -= monto
            self.register_deduction(monto, ingreso.afiliado,
                                    self.registro['completo'])
            ingreso.cantidad = 0

    def register_deduction(self, cantidad, afiliado, cuenta):
        database.create_deduction(afiliado, cantidad, cuenta, self.day)


class Corrector(object):
    def __init__(self, loans):

        self.corregir = open('correcciones.txt', 'w')
        self.prestamos = database.get_all_loans()

    def iniciar(self):

        map((lambda p: self.corregir_prestamo(p)), self.prestamos)

    def corregir_prestamo(self, prestamo):

        futuro = prestamo.future()
        if futuro == list():
            self.corregir.write(str(prestamo.id))
            self.corregir.write('\n')
            return

        ultimo_pago = futuro[-1]['payment']
        ultimo_mes = futuro[-1]['enum']
        if ultimo_pago < prestamo.payment and ultimo_mes == prestamo.months:
            prestamo.debt += (
                (prestamo.payment - ultimo_pago) * 2 / 3).quantize(
                Decimal("0.01"))
            print("Corregido prestamo {0}".format(prestamo.id))


class ReportLine(object):
    """Representacion interna de los valores a deducir en la planilla de
    Escalafon"""

    def __init__(self, affiliate, amount):
        self.amount = amount
        self.afiliado = affiliate

    def __str__(self):
        total = self.amount * Decimal(100)
        if self.afiliado.cardID is None:
            return str()
        return "{0}0011{1:018d}".format(self.afiliado.cardID.replace('-', ''),
                                        total)


class Generador(object):
    """Permite generar la planilla de Escalafon a partir de los estados de
    cuenta de los afiliados"""

    def __init__(self, year, month):

        self.year = year
        self.month = month
        self.lines = list()
        self.filename = "./%(year)s%(month)02dCOPEMH.txt" % {'year': self.year,
                                                             'month':
                                                                 self.month}

    def crear_retrasadas(self):

        """Crea las cuotas retrasadas para los afiliados"""

        for retrasada in retrasadas.procesar_retrasadas('Escalafon'):
            retrasada.crear_extra()

    def procesar_afiliados(self):

        """Calcula las cantidades a pagar por los afiliados"""

        afiliados = database.get_affiliates_by_payment(1, True)

        for afiliado in afiliados:
            line = ReportLine(afiliado, afiliado.get_monthly())
            self.lines.append(line)

    def escribir_archivo(self):

        """Escribe el archivo de cobros que se enviará"""

        f = open(self.filename, 'w')
        start = "%(year)s%(month)02d" % {'year': int(self.year),
                                         'month': int(self.month)}
        vacio = str()

        identidades = list()
        for line in self.lines:

            if line.afiliado.cardID == None:
                print("Identidad Invalida: {0}".format(line.afiliado.id))
                continue

            identidad = line.afiliado.cardID.replace('-', '')
            if len(identidad) < 13 or len(identidad) > 13:
                print("Identidad muy corta {0} {1}".format(line.afiliado.cardID,
                                                           line.afiliado.id))
                continue

            if identidad in identidades:
                print("Identidad Repetida {0} {1}".format(line.afiliado.cardID,
                                                          line.afiliado.id))
                continue

            identidades.append(identidad)
            str_line = str(line)
            if str_line == vacio:
                continue
            l = start + str_line + "\n"
            f.write(l)

    def escribir_csv(self):

        archivo = csv.writer(open('banco.csv', 'w'))
        identidades = list()
        for line in self.lines:
            if line.afiliado.cardID == None:
                print("Identidad Invalida: {0}".format(line.afiliado.id))
                continue

            identidad = line.afiliado.cardID.replace('-', '')
            if len(identidad) < 13 or len(identidad) > 13:
                print("Identidad muy corta {0} {1}".format(line.afiliado.cardID,
                                                           line.afiliado.id))
                continue

            if identidad in identidades:
                print("Identidad Repetida {0} {1}".format(line.afiliado.cardID,
                                                          line.afiliado.id))
            identidades.append(identidad)
            archivo.writerow([identidad, line.amount])

    def agregar_ayuda_medica(self):

        """Agrega una Ayuda Médica aprobada a todos los afiliados de
        Escalafón"""

        afiliados = database.get_affiliates_by_payment("Escalafon", True)
        kw = dict()
        kw['account'] = database.get_help_account()
        kw['amount'] = 50
        kw['months'] = 1

        for afiliado in afiliados:
            kw['affiliate'] = afiliado
            database.Extra(**kw)


class Extraccion(object):
    def __init__(self, afiliado, cantidad, fecha):
        self.afiliado = afiliado
        self.cantidad = cantidad
        self.marca = 'N'
        self.fecha = fecha

    def list(self):
        return [self.afiliado.escalafon,
                0,
                11,
                self.fecha.day,
                self.fecha.month,
                self.fecha.year,
                self.cantidad,
                self.marca]

    def __str__(self):
        return "{0} {1} {1}".format(self.afiliado.escalafon, str(self.cantidad),
                                    self.marca)
