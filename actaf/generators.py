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

class Generator(object):
    
    def __init__(self, banco, afiliados, fecha):
        
        self.afiliados = afiliados
        self.fecha = fecha
        self.banco = banco
    
    def output(self):
        
        return list()

class Occidente(Generator):
    
    def __init__(self, banco, afiliados, fecha):
        
        super(Occidente).__init__(banco, afiliados, fecha)
        self.format = "{0:012d}{1:<018}{2:12d}{3:30}{4:20}{5:04d}{6:02d}"
        self.format += "{7:02d}{8:013d}1"
    
    def output(self):
        
        charges = list()
        
        for afiliado in self.afiliados:
            
            charges.append(self.format.format(
                            self.banco.cuenta,
                            self.banco.codigo,
                            afiliado.cuenta,
                            afiliado.cardID,
                            afiliado.id,
                            self.fecha.year,
                            self.fecha.month,
                            self.fecha.day,
                            afiliado.get_monthly
                            )
                          )
        return charges
