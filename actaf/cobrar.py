#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# cobrar.py
#
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
from multiprocessing import Pool
import generators
import argparse
from datetime import datetime


def escribir_banco(parametro):
    
    afiliados = database.get_affiliates_by_banco(parametro[0], 1, True)
    Generator = getattr(generators, parametro[0].generator)
    generator = Generator(parametro[0], afiliados, parametro[1])
    generator.output()


class BancoProxy(object):
    
    nombre = "General"
    
    def __init__(self):
        
        self.nombre = "General"

if __name__ == "__main__":
    
    pool = Pool()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("fecha",
                        help=u"Fecha en que se efectuarán los cobros")
    
    args = parser.parse_args()
    
    fecha = datetime.strptime(args.fecha, "%Y%m%d").date()
    bancos = database.get_bancos()
    bancos = ((banco, fecha) for banco in bancos)
    
    pool.map(escribir_banco, bancos)
    
    afiliados = database.get_affiliates_by_payment(1, True)
    generator = generators.Generator(BancoProxy, afiliados, fecha)
    generator.output()
    generator.davivienda()
