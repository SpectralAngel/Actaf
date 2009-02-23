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
import core
import database
from decimal import Decimal
import locale
import datetime

class TaMan(object):
	
	"""GUI class for Afiliate management"""
	
	def __init__(self):
		
		self.builder = gtk.Builder()
		self.builder.add_from_file("taman.xml")
		
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
				"on_acerca_close":self.on_acerca_close
			}
		)
	
	#################################
	# Callbacks
	def on_acerca_close(self, obj, response=None):
	
		"""Hides the about window"""
		
		obj.hide()
	
	def on_about_activate(self, obj):
		
		"""Shows the about window"""
		
		acerca = self.builder.get_object("acerca")
		
		acerca.set_version("0.1")
		acerca.show()
	
	def on_update_clicked(self, obj):
		
		posteo = self.builder.get_object("posteo")
		archivo = self.builder.get_object("deductions")
		fecha = self.builder.get_object("post_day")
		
		# Cambiando la fecha a mostrar en la ventana de posteo
		hoy = datetime.date.today()
		fecha.select_month(hoy.month-1, hoy.year)
		fecha.select_day(hoy.day)
		
		respuesta = posteo.run()
		posteo.hide()
		return
		if respuesta == gtk.RESPONSE_OK:
			
			afiliados = {}
			for a in database.get_affiliates_by_payment("Escalafon"):
				
				afiliados[a.cardID] = a
			
			parser = core.Parser(archivo.get_filename(), afiliados)
			
			dia = fecha.get_date()
			
			accounts = {}
			for account in database.get_accounts():
				
				accounts[account] = {}
				accounts[account]['number'] = 0
				accounts[account]['amount'] = Decimal(0)
			
			updater = core.Updater(database.get_obligation(dia.year, dia.month),
									accounts, dia)
			
			updater.register_account(get_loan_account(), 'loan')
			updater.register_account(get_cuota_account(), 'cuota')
			updater.register_account(get_incomplete_account(), 'incomplete')
			updater.register_account(get_exceding_account(), 'exceding')
			
			# Cambiar por un par de acciones que muestren progreso
			(updater.update(income) for income in parser.parse())
			
			reporte = database.create_report(accounts, dia.year, dia.month)
			self.create_report_window(report)
	
	def on_correct_clicked(self, obj):
		
		inicio = self.builder.get_object("inicio")
		fin = self.builder.get_object("fin")
		
		# Cambiar las fechas a mostrar en el selector de periodo
		hoy = datetime.date.today()
		
		inicio.select_month(hoy.month-1, hoy.year)
		inicio.select_day(1)
		
		fin.select_month(hoy.month-1, hoy.year)
		fin.select_day(hoy.day)
		
		ventana = self.builder.get_object("correccion")
		
		respuesta = ventana.run()
		ventana.hide()
		return
		if respuesta == gtk.RESPONSE_OK:
		
			corrector = core.Corrector(get_loans_by_period(inicio.get_date(),
										fin.get_date()))
			corrector.correct()
	
	def on_report_clicked(self, obj):
		
		periodo = self.builder.get_object("dialogoReporte")
		anio = self.builder.get_object("anio")
		mes = self.builder.get_object("mes")
		
		respuesta = periodo.run()
		periodo.hide()
		return
		if respuesta == gtk.response_OK:
			
			report = database.get_income_report(int(anio.get_value()),
												int(mes.get_value()))
			self.create_report_window(report)
	
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
		
		(cuentas.append([ra.name, ra.quantity, locale.currency(ra.amount, True,
																True)])
			for ra in report.reportAccounts)
		
		reporte.show_all()
