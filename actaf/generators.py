# -*- coding: utf8 -*-
#
# generators.py
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

import csv
from decimal import Decimal, ROUND_DOWN
import io
from datetime import date

import unicodecsv
import model


class Generator(object):
    def __init__(self, banco, afiliados, fecha):
        self.afiliados = filter((lambda
                                         a: a.cardID != None and a.firstName != None and a.lastName != None),
                                afiliados)
        self.fecha = fecha
        self.banco = banco

    def output(self):
        print(self.banco.nombre)
        line = ([unicode(a.id),
                 u"{0} {1}".format(a.firstName, a.lastName),
                 a.cardID,
                 unicode(a.get_monthly(self.fecha, True)),
                 unicode(a.cuenta)] for a in self.afiliados)
        line = filter((lambda l: l[0] != None and l[1] != None and l[
            2] is not None and l[3] is not None),
                      line)
        planilla = unicodecsv.UnicodeWriter(
            open(u'{0}.csv'.format(self.banco.nombre + str(self.fecha)), 'wb'))
        map((lambda l: planilla.writerow(l)), line)

    def davivienda(self):
        line = ([unicode(a.id),
                 a.cardID.replace('-', ''),
                 u"{0} {1}".format(a.firstName, a.lastName),
                 unicode(a.get_monthly(self.fecha, True)),
                 unicode(0),
                 unicode(0),
                 unicode(a.get_monthly(self.fecha, True)),
                ]
                for a in self.afiliados)
        line = filter((lambda l: l[0] != None and l[1] != None and l[2] != None and l[3] != None), line)
        planilla = unicodecsv.UnicodeWriter(open(u'COPEMH.csv', 'wb'))
        map((lambda l: planilla.writerow(l)), line)

    def cobros(self):
        line = ([unicode(a.id),
                 a.cardID.replace('-', ''),
                 u"{0} {1}".format(a.firstName, a.lastName),
                 unicode(a.get_monthly(self.fecha)),
                 unicode(a.get_phone()),
                 unicode(a.get_email()),
                 unicode(a.get_monthly()),
                 ]
                for a in self.afiliados)
        line = filter((lambda l: l[0] != None and l[1] != None and l[2] != None and l[3] != None), line)
        planilla = unicodecsv.UnicodeWriter(open(u'COPEMH-cobros.csv', 'wb'))
        map((lambda l: planilla.writerow(l)), line)


class Occidente(Generator):
    def __init__(self, banco, afiliados, fecha):

        super(Occidente, self).__init__(banco, afiliados, fecha)
        self.format = u"{0:012d}{1:18}{2:12d}{3:<30}{4:<20}{5:04d}{6:02d}"
        self.format += u"{7:02d}{8:013d} \n"
        month = self.fecha.month + 3
        year = self.fecha.year
        if month > 12:
            month -= 12
            year += 1
        self.fecha_cuota = self.fecha
        self.fecha = date(year, month, self.fecha.day)

    def output(self):

        charges = list()

        for afiliado in self.afiliados:
            charges.append(self.format.format(
                int(self.banco.cuenta),
                int(self.banco.codigo),
                int(afiliado.cuenta),
                afiliado.cardID,
                afiliado.id,
                self.fecha.year,
                self.fecha.month,
                self.fecha.day,
                int(afiliado.get_monthly(self.fecha_cuota, True) * Decimal("100"))
            )
            )

        out = io.open(self.banco.nombre + str(self.fecha) + ".txt", 'w')
        out.writelines(charges)


class Atlantida(Generator):
    def __init__(self, banco, afiliados, fecha):

        super(Atlantida, self).__init__(banco, afiliados, fecha)
        self.cformat = u"{0:<16}{1:2}{2:1}{3:05d}{4:8}{5:15}{6:40}"
        self.cformat += u"{7:3}{8:40}{9:19}{10:12}{11:2}{12:03d}{13:16}\n"

        self.format = u"{0:05d}{1:<16}{2:<16}{3:03d}{4:016d}{5:3}{6:<40}"
        self.format += u"{7:<9}{8:<9}\n"

    def output(self):

        print(self.banco.nombre)
        clients = []
        charges = []

        for afiliado in self.afiliados:
            if not afiliado.autorizacion:
                continue

            nombre_afiliado = u"{0} {1}".format(afiliado.firstName,
                                                afiliado.lastName)
            if len(nombre_afiliado) > 40:
                nombre_afiliado = nombre_afiliado[:39]
            clients.append(self.cformat.format(
                afiliado.id,
                u"01",
                u"A",
                int(self.banco.codigo),
                0,
                afiliado.cardID,
                afiliado.get_email(),
                u"LPS",
                nombre_afiliado,
                afiliado.cuenta,
                afiliado.get_phone(),
                u"AH",
                1,
                u""
            ))
            charges.append(self.format.format(
                int(self.banco.codigo),
                afiliado.id,
                u"",
                1,
                int(afiliado.get_monthly(self.fecha, True) * Decimal("100")),
                u"LPS",
                u"Cuota de Aportaciones COPEMH",
                u'',
                u'',
            ))

        out = io.open(self.banco.nombre + "clientes" + str(self.fecha) + ".txt",
                      'w')
        out.writelines(clients)
        out.close()
        out = io.open(self.banco.nombre + str(self.fecha) + "-debito.txt", 'w')
        out.writelines(charges)


class INPREMA(Generator):
    def __init__(self, afiliados, fecha):

        super(INPREMA, self).__init__(None, afiliados, fecha)
        self.format = u"{0:4d}{1:02d}{2:13}00011{3:013}\n"

    def output(self):

        charges = list()
        identidad = 0
        line = []
        loan = []

        for afiliado in self.afiliados:
            if afiliado.cardID is None or afiliado.cardID == '0':
                identidad += 1
                continue
            salida = self.format.format(
                self.fecha.year,
                self.fecha.month,
                afiliado.cardID.replace('-', ''),
                afiliado.get_monthly(self.fecha, True))
            line.append((
                str(self.fecha.year),
                str(self.fecha.month),
                afiliado.cardID.replace('-', ''),
                '11',
                str(afiliado.get_monthly(self.fecha))))
            loan.append((
                str(self.fecha.year),
                str(self.fecha.month),
                afiliado.cardID.replace('-', ''),
                '11',
                str(afiliado.get_prestamo())))
            charges.append(salida)

        planilla = unicodecsv.UnicodeWriter(
            open(u'INPREMA{0}.csv'.format(str(self.fecha)), 'wb'),
            quoting=csv.QUOTE_ALL)
        prestamos = unicodecsv.UnicodeWriter(
            open(u'INPREMA{0}-prestamo.csv'.format(str(self.fecha)), 'wb'),
            quoting=csv.QUOTE_ALL)
        map((lambda l: planilla.writerow(l)), line)
        map((lambda l: prestamos.writerow(l)), loan)


class Banhcafe(Generator):
    def __init__(self, banco, afiliados, fecha):
        super(Banhcafe, self).__init__(banco, afiliados, fecha)

    def output(self):
        model.CobroBancarioBanhcafe.clearTable()
        for afiliado in self.afiliados:
            model.CobroBancarioBanhcafe(cantidad=afiliado.get_monthly(),
                                        identidad=afiliado.cardID.replace('-',
                                                                          ''))

        super(Banhcafe, self).output()


class DaVivienda(Generator):
    def __init__(self, banco, afiliados, fecha):
        super(DaVivienda, self).__init__(banco, afiliados, fecha)


class Pais(Generator):
    def __init__(self, banco, afiliados, fecha):
        super(Pais, self).__init__(banco, afiliados, fecha)

    def output(self):
        print(self.banco.nombre)
        line = ([str(a.id),
                 a.cardID.replace('-', ''),
                 u"{0} {1}".format(a.firstName, a.lastName),
                 str(a.cuenta),
                 str(a.bancario),
                 str(a.get_monthly(self.fecha, True)),
                 str(a.last)] for a in self.afiliados
                if a.autorizacion)

        line = filter((lambda l: l[0] != None and l[1] != None and l[
            2] is not None and l[3] is not None),
                      line)
        planilla = unicodecsv.UnicodeWriter(
            open(u'{0}.csv'.format(self.banco.nombre + str(self.fecha)), 'wb'))
        map((lambda l: planilla.writerow(l)), line)


class Ficensa(Generator):
    def __init__(self, banco, afiliados, fecha):

        super(Ficensa, self).__init__(banco, afiliados, fecha)
        self.format = u"{0}{1:13}APO{02:8d}{3:<40}{4:<20}{5:08d} {6:015d}\n"

    def output(self):

        print(self.banco.nombre)
        charges = list()

        for afiliado in self.afiliados:
            if not afiliado.autorizacion:
                continue
            nombre_afiliado = u"{0} {1}".format(afiliado.firstName,
                                                afiliado.lastName)
            if len(nombre_afiliado) > 40:
                nombre_afiliado = nombre_afiliado[:39]

            charges.append(self.format.format(
                self.fecha.strftime("%Y%m"),
                afiliado.cardID.replace('-', ''),
                int(afiliado.get_monthly(self.fecha, True) * Decimal("100")),
                nombre_afiliado,
                'Aportaciones',
                afiliado.id,
                int(afiliado.cuenta),
            )
            )

        out = io.open(self.banco.nombre + str(self.fecha) + ".txt", 'w')
        out.writelines(charges)


class Continental(Generator):
    def __init__(self, banco, afiliados, fecha):

        super(Continental, self).__init__(banco, afiliados, fecha)
        self.format = u"{0:02d}{1:04d}{2:016d}{3:50}{4:08d}.{5:02d}\n"

    def output(self):

        charges = list()

        for afiliado in self.afiliados:
            nombre_afiliado = u"{0} {1}".format(afiliado.firstName,
                                                afiliado.lastName)
            if len(nombre_afiliado) > 50:
                nombre_afiliado = nombre_afiliado[:49]

            mensual = afiliado.get_monthly(self.fecha, True)
            charges.append(self.format.format(
                self.fecha.month,
                self.fecha.year,
                int(afiliado.cuenta),
                nombre_afiliado,
                int(mensual.quantize(Decimal("1"), rounding=ROUND_DOWN)),
                int(mensual % 1)
            )
            )

        out = io.open(self.banco.nombre + str(self.fecha) + ".txt", 'w')
        out.writelines(charges)


class UPN(Generator):
    def __init__(self, afiliados, fecha):
        super(UPN, self).__init__(None, afiliados, fecha)
        self.afiliados = afiliados

    def output(self):
        line = ([a.cardID,
                 u"{0} {1}".format(a.firstName, a.lastName),
                 str(a.escalafon),
                 str(a.get_monthly(self.fecha, True))] for a in self.afiliados)

        planilla = unicodecsv.UnicodeWriter(
            open(u'UPN{0}.csv'.format(str(self.fecha)), 'wb'))
        map((lambda l: planilla.writerow(l)), line)
