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
from decimal import Decimal
from sqlobject import sqlhub

import database
import core


class ActualizadorBancario(core.Actualizador):
    """Actualiza estados de cuenta de acuerdo a los datos entregados por
    :class:`Ingreso` registrando los motivos por los cuales se efectuó un
    determinado cobro"""

    def __init__(self, obligacion, accounts, day, banco, cobro,
                 jubilados, alternativos):

        super(ActualizadorBancario, self).__init__(obligacion, accounts, day)

        self.banco = banco
        self.cobro = cobro
        self.jubilados = jubilados
        self.alternativos = alternativos

    def update(self, ingreso, cuota=True):

        """Actualiza el estado de cuenta de acuerdo a un :class:`Ingreso`"""
        ingreso.afiliado.last = ingreso.cantidad
        if cuota:
            if ingreso.afiliado.cotizacion.jubilados or \
                    ingreso.afiliado.cotizacion.alternate:
                self.complemento(ingreso, Decimal())
            else:
                self.cuota(ingreso)
        self.aditional(ingreso)

    def complemento(self, ingreso, monto):

        if ingreso.afiliado.cotizacion.alternate:
            monto = self.alternativos
        if ingreso.afiliado.cotizacion.jubilados:
            monto = self.jubilados

        super(ActualizadorBancario, self).complemento(ingreso, monto)

    def extra_act(self, extra):
        extra.act(True, self.day, True, self.cobro)

    def register_deduction(self, cantidad, afiliado, cuenta):
        database.create_bank_deduction(
            afiliado, cantidad, cuenta, self.banco, self.day, self.cobro
        )


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
