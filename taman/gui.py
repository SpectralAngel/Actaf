#!/usr/bin/python
# -*- coding: utf8 -*-
#
# gui.py
# This file is part of TaMan
#
# Copyright (C) 2009 - Carlos Flores
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

from decimal import Decimal
from datetime import date
import locale

import core
import database

class TaMan(object):
	
	"""GUI class for Afiliate management"""
	
	def __init__(self):
		
		self.builder = gtk.Builder()
		self.builder.add_from_file("taman.glade")
		
		self.window = self.builder.get_object("main")
		
		self.connect_signals()
		
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
		
		acerca.set_version("0.1")
		acerca.show()
	
	def on_update_clicked(self, button):
		
		posteo = self.builder.get_object("posteo")
		archivo = self.builder.get_object("deductions")
		fecha = self.builder.get_object("diaposteo")
		
		# Cambiando la fecha a mostrar en la ventana de posteo
		hoy = date.today()
		fecha.select_month(hoy.month-1, hoy.year)
		fecha.select_day(hoy.day)
		
		respuesta = posteo.run()
		posteo.hide()
		
		if respuesta == gtk.RESPONSE_OK:
			
			afiliados = dict()
			for a in database.get_affiliates_by_payment("Escalafon"):
				
				afiliados[a.cardID] = a
			
			parser = core.Parser(archivo.get_filename(), afiliados)
			
			report = process.start(parser, afiliados, fecha.get_date())
			
			self.create_report_window(report)
	
	def on_correct_clicked(self, button):
		
		inicio = self.builder.get_object("inicio")
		fin = self.builder.get_object("fin")
		
		# Cambiar las fechas a mostrar en el selector de periodo
		hoy = date.today()
		
		inicio.select_month(hoy.month-1, hoy.year)
		inicio.select_day(1)
		
		fin.select_month(hoy.month-1, hoy.year)
		fin.select_day(hoy.day)
		
		ventana = self.builder.get_object("correccion")
		
		respuesta = ventana.run()
		ventana.hide()
		
		if respuesta == gtk.RESPONSE_OK:
		
			corrector = core.Corrector(get_loans_by_period(inicio.get_date(),
										fin.get_date()))
			corrector.correct()
	
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
			
			reporter = core.Reporter(int(anio.get_value()), int(mes.get_value()))
			reporter.process_affiliates()
	
	def on_posteo_inprema_clicked(self, button):
		
		posteo = self.builder.get_object("posteo")
		archivo = self.builder.get_object("deductions")
		fecha = self.builder.get_object("diaposteo")
		
		# Cambiando la fecha a mostrar en la ventana de posteo
		hoy = date.today()
		fecha.select_month(hoy.month-1, hoy.year)
		fecha.select_day(hoy.day)
		
		respuesta = posteo.run()
		posteo.hide()
		
		if respuesta != gtk.RESPONSE_OK: return
		
		affiliates = database.get_affiliates_by_payment("INPREMA")
		afiliados = dict()
	
		for a in affiliates:
		
			inprema = None
			try: inprema = int(a.escalafon)
			except Exception, e: print e.message
		
			afiliados[inprema] = a
	
		parser = core.ParserINPREMA(archivo.get_filename(), afiliados)
	
		reporte = process.start(parser, fecha.get_date(), True, 'INPREMA')
		
		self.create_report_window(reporte)
	
	def on_generar_inprema(self, button):
		
		pass
	
	###################
	# Utility Functions
	def create_report_window(self, report):
		
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
		vistaCuentas.set_view(cuentas)
		
		for ra in report.reportAccounts:
			cuentas.append([ra.name, ra.quantity, locale.currency(ra.amount, True, True)])
		
		reporte.show_all()

