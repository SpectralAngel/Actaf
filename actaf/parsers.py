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

from datetime import date
from decimal import Decimal

class Parser(object):
    
    def __init__(self, fecha, archivo):
        
        self.archivo = archivo
        self.fecha = fecha
    
    def output(self):
        
        return list()

class Occidente(Parser):
    
    def __init__(self, archivo):
        
        super(Occidente).__init__(self, archivo)
        self.file = open(archivo)
    
    def output(self):
        
        charges = list()
        
        for line in self.archivo:
            
            identidad = line[119:149]
            valor = Decimal(line[169:181])
            fecha = date(int(line[29:33]), int(line[33:34]), int(line[35:36]))
            
            charges.append((identidad, valor, fecha))
        
        return charges
