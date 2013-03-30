#!/usr/bin/python
# -*- coding: utf8 -*-
#
# gui.py
# This file is part of TaMan
#
# Copyright (C) 2009, 2010 Carlos Flores <cafg10@gmail.com>
#
# TaMan is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# TaMan is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TaMan; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, 
# Boston, MA  02110-1301  USA

import pygtk
pygtk.require("2.0")
import gtk

from datetime import date
import locale

import core
import database
import process
import inprema

class MainWindow(object):
    
    """GUI class for Affiliate management"""
    
    def __init__(self):
        
        self.builder = gtk.Builder()
        self.builder.add_from_file("actaf.glade")
        
        self.window = self.builder.get_object("main")
        
        self.connect_signals()
        self.estado = self.builder.get_object('estado')
        contexto = self.estado.get_context_id('Conexion')
        self.estado.push(contexto, database.obtener_conexion())
        
        self.window.show()
    
    def connect_signals(self):
        
        self.builder.connect_signals(
            {
                "on_update_clicked":self.on_update_clicked,
                "on_correct_clicked":self.on_correct_clicked,
                "on_report_clicked":self.on_report_clicked,
                "on_about_activate":self.on_about_activate,
                "on_window_destroy":gtk.main_quit,
                "on_acerca_close":self.on_acerca_close,
                "on_generate_clicked":self.on_generate_clicked,
                "on_posteo_inprema_clicked":self.on_posteo_inprema_clicked,
                "on_generar_inprema_clicked":self.on_generar_inprema_clicked
            }
        )
    
    #################################
    # Callbacks
    def on_acerca_close(self, window, response=None):
    
        """Hides the about window"""
        
        window.hide()
    
    def on_about_activate(self, obj):
        
        """Shows the about window"""
        
        acerca = self.builder.get_object("acerca")
        
        acerca.set_version("0.2")
        acerca.show()
    
    def on_update_clicked(self, button):
        
        posteo = self.builder.get_object("posteo")
        archivo = self.builder.get_object("deducciones")
        fecha = self.builder.get_object("diaposteo")
        
        # Cambiando la fecha a mostrar en la ventana de posteo
        hoy = date.today()
        fecha.select_month(hoy.month - 1, hoy.year)
        fecha.select_day(hoy.day)
        
        respuesta = posteo.run()
        posteo.hide()
        
        if respuesta == gtk.RESPONSE_OK:
            
            afiliados = database.get_affiliates_by_payment(1, False)
            #afiliados = database.get_all_affiliates()
            
            parser = core.AnalizadorEscalafon(archivo.get_filename(), afiliados)
            #parser = core.AnalizadorCSV(archivo.get_filename(), afiliados)
            dia = fecha.get_date()
            report = process.start(parser, date(dia[0], dia[1] + 1, dia[2]), False)
            
            self.create_report_window(report)
    
    def on_correct_clicked(self, button):
        
        corrector = core.Corrector()
        corrector.corregir_prestamos()
    
    def on_report_clicked(self, button):
        
        periodo = self.builder.get_object("dialogoReporte")
        anio = self.builder.get_object("anio")
        mes = self.builder.get_object("mes")
        
        respuesta = periodo.run()
        periodo.hide()
        if respuesta == gtk.RESPONSE_OK:
            
            report = database.get_income_report(int(anio.get_value()),
                                                int(mes.get_value()))
            self.create_report_window(report)
    
    def on_generate_clicked(self, button):
        
        anio = self.builder.get_object("gen_anio")
        mes = self.builder.get_object("gen_mes")
        generador = self.builder.get_object("generator")
        respuesta = generador.run()
        generador.hide()
        if respuesta == gtk.RESPONSE_OK:
            
            reporter = core.Generador(int(anio.get_value()), int(mes.get_value()))
            reporter.procesar_afiliados()
            reporter.escribir_archivo()
    
    def on_posteo_inprema_clicked(self, button):
        
        posteo = self.builder.get_object("posteo")
        archivo = self.builder.get_object("deducciones")
        fecha = self.builder.get_object("diaposteo")
        
        # Cambiando la fecha a mostrar en la ventana de posteo
        hoy = date.today()
        fecha.select_month(hoy.month - 1, hoy.year)
        fecha.select_day(hoy.day)
        
        respuesta = posteo.run()
        posteo.hide()
        
        if respuesta == gtk.RESPONSE_OK:
            print("Procesando")
            dia = fecha.get_date()
            self.create_report_window(process.inprema(archivo.get_filename(),
                                                      date(dia[0], dia[1] + 1,
                                                      dia[2])), True)
    
    def on_generar_inprema_clicked(self, button):
        
        inprema.extraer_cambios()
    
    ###################
    # Utility Functions
    def create_report_window(self, report, other=False):
        
        reporte = self.builder.get_object("reporte")
        
        vistaCuentas = self.builder.get_object("vistaReporte")
        column = gtk.TreeViewColumn("Cuenta", gtk.CellRendererText(), text=0)
        vistaCuentas.append_column(column)
        column.set_sort_column_id(0)
        
        column = gtk.TreeViewColumn("Aportantes", gtk.CellRendererText(), text=1)
        vistaCuentas.append_column(column)
        column.set_sort_column_id(1)
        
        column = gtk.TreeViewColumn("Cantidad", gtk.CellRendererText(), text=2)
        vistaCuentas.append_column(column)
        column.set_sort_column_id(2)
        
        cuentas = gtk.ListStore(str, int, str)
        vistaCuentas.set_model(cuentas)
        
        if not other:
            for ra in report.reportAccounts:
                cuentas.append([ra.name, ra.quantity, locale.currency(ra.amount, True, True)])
        else:
            for ra in report.otherAccounts:
                cuentas.append([ra.account.name, ra.quantity, locale.currency(ra.amount, True, True)])
        
        reporte.show_all()
