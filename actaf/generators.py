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
from __future__ import unicode_literals

import csv
import errno
import io
import os
from datetime import date
from decimal import Decimal, ROUND_DOWN

import unicodecsv

import model

directory = 'generated'

if not os.path.exists(directory):
    try:
        os.makedirs(directory)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


class Generator(object):
    def __init__(self, banco, afiliados, fecha):
        self.afiliados = [
            a for a in afiliados
            if a.cardID is not None and a.firstName is not None
            and a.lastName is not None
            ]
        self.fecha = fecha
        self.banco = banco

    def output(self):
        print(self.banco.nombre)
        line = ([str(a.id),
                 "{0} {1}".format(a.firstName, a.lastName),
                 a.cardID,
                 str(a.get_monthly(self.fecha, True)),
                 str(a.cuenta)] for a in self.afiliados)
        line = filter((lambda l: l[0] is not None and l[1] is not None and
                                 l[2] is not None and l[3] is not None), line)
        planilla = unicodecsv.writer(
                io.open(os.path.join(directory, '{0}.csv'.format(
                        self.banco.nombre + str(self.fecha))),
                        'wb'))
        [planilla.writerow(l) for l in line]

    def davivienda(self):
        line = ([str(a.id),
                 a.cardID.replace('-', ''),
                 "{0} {1}".format(a.firstName, a.lastName),
                 str(a.get_monthly(self.fecha, True)),
                 str(0),
                 str(0),
                 str(a.get_monthly(self.fecha, True)),
                 ]
                for a in self.afiliados)
        line = filter((lambda l: l[0] is not None and l[1] is not None and
                                 l[2] is not None and l[3] is not None), line)
        planilla = unicodecsv.writer(
                io.open(os.path.join(directory, 'general.csv'), 'wb'))
        [planilla.writerow(l) for l in line]

    def cobros(self):
        line = ([str(a.id),
                 a.cardID.replace('-', ''),
                 "{0} {1}".format(a.firstName, a.lastName),
                 str(a.get_monthly(self.fecha)),
                 a.get_phone(),
                 a.get_email(),
                 a.get_monthly(),
                 ]
                for a in self.afiliados)
        line = filter((lambda l: l[0] is not None and l[1] is not None and
                                 l[2] is not None and l[3] is not None), line)
        planilla = unicodecsv.writer(
                io.open(os.path.join(directory, 'general-cobros.csv'), 'wb'))
        [planilla.writerow(l) for l in line]


class Occidente(Generator):
    def __init__(self, banco, afiliados, fecha):

        super(Occidente, self).__init__(banco, afiliados, fecha)
        self.format = "{0:012d}{1:18}{2:12d}{3:<30}{4:<20}{5:04d}{6:02d}"
        self.format += "{7:02d}{8:013d} \n"
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
                    int(afiliado.get_monthly(self.fecha_cuota, True) * Decimal(
                            "100"))
            )
            )

        out = io.open(os.path.join(directory, self.banco.nombre + str(
                self.fecha) + ".txt"), 'w')
        out.writelines(charges)


class Atlantida(Generator):
    def __init__(self, banco, afiliados, fecha):

        super(Atlantida, self).__init__(banco, afiliados, fecha)
        self.cformat = "{0:<16}{1:2}{2:1}{3:05d}{4:8}{5:15}{6:40}"
        self.cformat += "{7:3}{8:40}{9:19}{10:12}{11:2}{12:03d}{13:16}\n"

        self.format = "{0:05d}{1:<16}{2:<16}{3:03d}{4:016d}{5:3}{6:<40}"
        self.format += "{7:<9}{8:<9}\n"

    def output(self):

        print(self.banco.nombre)
        clients = []
        charges = []

        for afiliado in self.afiliados:
            if not afiliado.autorizacion:
                continue

            nombre_afiliado = "{0} {1}".format(afiliado.firstName,
                                               afiliado.lastName)
            if len(nombre_afiliado) > 40:
                nombre_afiliado = nombre_afiliado[:39]
            clients.append(self.cformat.format(
                    afiliado.id,
                    "01",
                    "A",
                    int(self.banco.codigo),
                    0,
                    afiliado.cardID,
                    afiliado.get_email(),
                    "LPS",
                    nombre_afiliado,
                    afiliado.cuenta,
                    afiliado.get_phone(),
                    "AH",
                    1,
                    ""
            ))
            charges.append(self.format.format(
                    int(self.banco.codigo),
                    afiliado.id,
                    "",
                    1,
                    int(afiliado.get_monthly(self.fecha, True) * Decimal(
                            "100")),
                    "LPS",
                    "Cuota de Aportaciones COPEMH",
                    '',
                    '',
            ))

        out = io.open(os.path.join(directory,
                                   self.banco.nombre + "clientes" + str(
                                           self.fecha) + ".txt"),
                      'w')
        out.writelines(clients)
        out.close()
        out = io.open(os.path.join(directory, self.banco.nombre + str(
                self.fecha) + "-debito.txt"), 'w')
        out.writelines(charges)


class INPREMA(Generator):
    def __init__(self, afiliados, fecha, append=False):

        super(INPREMA, self).__init__(None, afiliados, fecha)
        self.format = "{0:4d}{1:02d}{2:13}00011{3:013}\n"
        self.append = append

    def output(self):
        identidad = 0
        line = []
        loan = []

        for afiliado in self.afiliados:
            if afiliado.cardID is None or afiliado.cardID == '0':
                identidad += 1
                continue

            line.append(
                    (
                        self.fecha.year,
                        self.fecha.month,
                        afiliado.cardID.replace('-', ''),
                        11,
                        afiliado.get_monthly(self.fecha)
                    )
            )
            loan.append(
                    (
                        self.fecha.year,
                        self.fecha.month,
                        afiliado.cardID.replace('-', ''),
                        11,
                        afiliado.get_prestamo()
                    )
            )

        mode = 'wb'
        if self.append:
            mode = 'ab+'
        planilla = unicodecsv.writer(
                io.open(os.path.join(directory,
                                     'INPREMA{0}.csv'.format(str(self.fecha))),
                        mode),
                quoting=csv.QUOTE_ALL, encoding='utf-8')
        prestamos = unicodecsv.writer(
                io.open(os.path.join(directory,
                                     'INPREMA{0}-prestamo.csv'.format(
                                             str(self.fecha))), mode),
                quoting=csv.QUOTE_ALL)

        print("Generando Colegiación")

        [planilla.writerow(l) for l in line]

        print("Generando Prestamos")
        [prestamos.writerow(l) for l in loan]


class Banhcafe(Generator):
    def __init__(self, banco, afiliados, fecha):
        super(Banhcafe, self).__init__(banco, afiliados, fecha)

    def output(self):
        model.CobroBancarioBanhcafe.clearTable()
        for afiliado in self.afiliados:
            model.CobroBancarioBanhcafe(
                    cantidad=afiliado.get_monthly(),
                    identidad=afiliado.cardID.replace('-', '')
            )

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
                 "{0} {1}".format(a.firstName, a.lastName),
                 str(a.cuenta),
                 str(a.bancario),
                 str(a.get_monthly(self.fecha, True)),
                 str(a.last)] for a in self.afiliados
                if a.autorizacion)

        line = [l for l in line if l[0] is not None and l[1] is not None and
                l[2] is not None and l[3] is not None]
        planilla = unicodecsv.writer(
                io.open(os.path.join(directory, '{0}.csv'.format(
                        self.banco.nombre + str(self.fecha))),
                        'wb'))
        [planilla.writerow(l) for l in line]


class Ficensa(Generator):
    def __init__(self, banco, afiliados, fecha):

        super(Ficensa, self).__init__(banco, afiliados, fecha)
        self.format = "{0}{1:13}APO{02:8d}{3:<40}{4:<20}{5:08d} {6:015d}\n"

    def output(self):

        print(self.banco.nombre)
        charges = list()

        for afiliado in self.afiliados:
            nombre_afiliado = "{0} {1}".format(afiliado.firstName,
                                               afiliado.lastName)
            if len(nombre_afiliado) > 40:
                nombre_afiliado = nombre_afiliado[:39]

            charges.append(self.format.format(
                    self.fecha.strftime("%Y%m"),
                    afiliado.cardID.replace('-', ''),
                    int(afiliado.get_monthly(self.fecha, True) * Decimal(
                            "100")),
                    nombre_afiliado,
                    'Aportaciones',
                    afiliado.id,
                    int(afiliado.cuenta),
            )
            )

        out = io.open(os.path.join(directory, self.banco.nombre + str(
                self.fecha) + ".txt"), 'w')
        out.writelines(charges)


class Continental(Generator):
    def __init__(self, banco, afiliados, fecha):

        super(Continental, self).__init__(banco, afiliados, fecha)
        self.format = "{0:02d}{1:04d}{2:016d}{3:50}{4:08d}.{5:02d}\n"

    def output(self):

        charges = list()

        for afiliado in self.afiliados:
            nombre_afiliado = "{0} {1}".format(afiliado.firstName,
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

        out = io.open(os.path.join(directory, self.banco.nombre + str(
                self.fecha) + ".txt"), 'w')
        out.writelines(charges)


class UPN(Generator):
    def __init__(self, afiliados, fecha):
        super(UPN, self).__init__(None, afiliados, fecha)
        self.afiliados = afiliados

    def output(self):
        line = ([a.cardID,
                 "{0} {1}".format(a.firstName, a.lastName),
                 str(a.escalafon),
                 str(a.get_monthly(self.fecha, True))] for a in self.afiliados)

        planilla = unicodecsv.writer(
                io.open(os.path.join(directory,
                                     'UPN{0}.csv'.format(str(self.fecha))),
                        'wb'))
        [planilla.writerow(l) for l in line]


class Trabajadores(Generator):
    def output(self):
        print(self.banco.nombre)
        line = ([str(a.id),
                 "{0} {1}".format(a.firstName, a.lastName),
                 a.cardID,
                 str(a.get_monthly(self.fecha, True, True)),
                 '50',
                 str(a.cuenta)] for a in self.afiliados)

        line = [l for l in line if l[0] is not None and l[1] is not None and
                l[2] is not None and l[3] is not None]

        planilla = unicodecsv.writer(
                io.open(os.path.join(directory, '{0}.csv'.format(
                        self.banco.nombre + str(self.fecha))),
                        'wb'))

        [planilla.writerow(l) for l in line]
