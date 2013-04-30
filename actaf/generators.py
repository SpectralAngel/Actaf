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

import unicodecsv
from decimal import Decimal
import io

class Generator(object):
    
    def __init__(self, banco, afiliados, fecha):
        
        self.afiliados = afiliados
        self.fecha = fecha
        self.banco = banco
    
    def output(self):
        
        line = ([str(a.id),
                 u"{0} {1}".format(a.firstName,a.lastName),
                 a.cardID,
                 str(a.get_monthly()),
                 str(a.cuenta)] for a in self.afiliados)
        line = filter((lambda l: l[0]!=None and l[1]!=None and l[2]!=None and l[3]!=None),
                      line)
        planilla = unicodecsv.UnicodeWriter(open(u'{0}.csv'.format(self.banco.nombre+str(self.fecha)), 'wb'))
        map((lambda l: planilla.writerow(l)), line)

class Occidente(Generator):
    
    def __init__(self, banco, afiliados, fecha):
        
        super(Occidente, self).__init__(banco, afiliados, fecha)
        self.format = u"{0:012d}{1:<18}{2:12d}{3:30}{4:20}{5:04d}{6:02d}"
        self.format += u"{7:02d}{8:013d}1\n"
    
    def output(self):
        
        charges = list()
        
        for afiliado in self.afiliados:
            
            charges.append(self.format.format(
                            0,#int(self.banco.cuenta),
                            0,#int(self.banco.codigo),
                            int(afiliado.cuenta),
                            afiliado.cardID,
                            afiliado.id,
                            self.fecha.year,
                            self.fecha.month,
                            self.fecha.day,
                            int(afiliado.get_monthly() * Decimal("100"))
                            )
                          )
        
        out = io.open(self.banco.nombre + str(self.fecha)+".txt", 'w')
        out.writelines(charges)

class Atlantida(Generator):
    
    def __init__(self, banco, afiliados, fecha):
        
        super(Atlantida, self).__init__(banco, afiliados, fecha)
        self.cformat = u"{0:16}{1:2}{2:1}{3:5d}{4:8}{5:15}{6:40}"
        self.cformat += u"{7:3}{8:40}{9:19}{10:8}{11:2}{12:03d}{13:16}\n"
        
        self.format = u"{0:05d}{1:16}{2:16}{3:03d}{4:016d}{5:3}{6:40}"
        self.format += u"{7:9}{8:9}\n"
    
    def output(self):
        
        clients = list()
        charges = list()
        
        for afiliado in self.afiliados:
            
            clients.append(self.cformat.format(
                afiliado.id,
                u"01",
                u"A",
                5,
                self.fecha.strftime("%Y%m%d"),
                afiliado.cardID,
                afiliado.email,
                "LPS",
                u"{0} {1}".format(afiliado.firstName, afiliado.lastName),
                afiliado.cuenta,
                afiliado.phone,
                u"TJ",
                3,
                u""
            ))
            charges.append(self.format.format(
                5,
                afiliado.id,
                u"",
                1,
                int(afiliado.get_monthly() * Decimal("100")),
                self.fecha.strftime("%Y%m%d"),
                afiliado.cardID,
                afiliado.email,
                u"LPS",
                u"{0} {1}".format(afiliado.firstName, afiliado.lastName),
                afiliado.cuenta,
                afiliado.phone,
                u"TJ",
                3,
                u""
            ))
        
        out = io.open(self.banco.nombre + "c" + str(self.fecha)+".txt", 'w')
        out.writelines(clients)
        out.close()
        out = io.open(self.banco.nombre + str(self.fecha)+".txt", 'w')
        out.writelines(charges)

class INPREMA(Generator):
    
    def __init__(self, afiliados, fecha):
        
        super(INPREMA, self).__init__(None, afiliados, fecha)
        self.format = u"{0:4d}{1:02d}{2:13}00011{3:013}\n"
    
    def output(self):
        
        charges = list()
        identidad = 0
        
        for afiliado in self.afiliados:
            if afiliado.cardID == None or afiliado.cardID == '0':
                identidad += 1
                continue
            salida = self.format.format(
                            self.fecha.year,
                            self.fecha.month,
                            afiliado.cardID.strip('-'),
                            afiliado.get_monthly()
                            )
            charges.append(salida)
        print(identidad)    
        out = io.open("inprema.txt", 'w')
        out.writelines(charges)
