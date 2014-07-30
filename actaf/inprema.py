# !/usr/bin/python
# -*- coding: utf8 -*-
#
# inprema.py
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

from datetime import datetime
import argparse

import database
from generators import INPREMA


def extraer_cambios(fecha):
    affiliates = database.get_affiliates_by_payment(2, True)

    generator = INPREMA(affiliates, fecha)
    generator.output()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fecha",
                        help=u"Fecha en que se efectuarán los cobros")

    args = parser.parse_args()

    fecha = datetime.strptime(args.fecha, "%Y%m%d").date()
    extraer_cambios(fecha)
