#!/usr/bin/env python
# -*- coding: utf8 -*-
# core.py
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

from decimal import Decimal
import csv
import database

class Income(object):

	def __init__(self, affiliate, amount):

		(self.affiliate, self.amount) = (affiliate, amount)

class Parser(object):

	def __init__(self, filename, affiliates):

		self.file = open(filename)
		self.affiliates = affiliates
		self.parsed = list()

	def parse(self):

		for line in self.file:

			amount = Decimal(str(line[94:111])) / hundred
			card = str(line[6:10] + '-' + line[10:14] + '-' + line[14:19])
			try:
				self.parsed.append(Income(self.affiliates[card], amount))

			except:
				print("Error de parseo no se encontro la identidad %s" % card)

		return self.parsed

class ParserINPREMA(object):

	def __init__(self, filename, affiliates):

		self.reader = csv.reader(filename)
		self.affiliates = affiliates
		self.parsed = list()

	def parse(self):
		
		perdidos = 0
		for row in self.reader:

			amount = Decimal(row[2])
			cobro = int(row[0])
			try:
				self.parsed.append(Income(self.affiliates[cobro], amount))

			except:
				perdidos += 1
				print("Error de parseo no se encontro la identidad %s" % cobro)
				
		print perdidos
		return self.parsed

class Updater(object):

	def __init__(self, obligation, accounts, day):

		self.obligation = obligation
		self.accounts = accounts
		self.day = day
		self.registered = dict()

	def register_account(self, account, name):

		self.registered[name] = account

	def update(self, income):

		self.cuota(income)
		for loan in income.affiliate.loans: self.loan(loan, income)
		self.extra(income)
		if income.amount > 0:
			
			self.exceding(income)

	def cuota(self, income):

		if income.amount >= self.obligation:

			self.accounts[self.registered['cuota']]['amount'] += self.obligation
			self.accounts[self.registered['cuota']]['number'] += 1
			income.affiliate.pay_cuota(self.day.year, self.day.month)
			income.amount -= self.obligation
			database.create_deduction(income.affiliate, self.obligation, self.accounts[self.registered['cuota']])

	def extra(self, income):

		extras = sum(e.amount for e in income.affiliate.extras)
		if income.amount >= extras:
			income.amount -= extras
			for extra in income.affiliate.extras:
				self.accounts[extra.account]['amount'] += extra.amount
				self.accounts[extra.account]['number'] += 1
				extra.act()
		else:
			for extra in income.affiliate.extras:
				if income.amount >= extra.amount:
					amount -= extra.amount
					self.accounts[extra.account]['amount'] += extra.amount
					self.accounts[extra.account]['number'] += 1
					extra.act()

	def exceding(self, income):

		self.accounts[self.registered['exceding']]['amount'] += income.amount
		self.accounts[self.registered['exceding']]['number'] += 1
		database.create_deduction(income.affiliate, income.amount, self.accounts[self.registered['exceding']])
	
	def delayed(income):
		
		for delayed in income.affiliate.delayed:
			self.accounts[self.registered['delayed']]['amount'] += income.amount
			self.accounts[self.registered['delayed']]['number'] += 1
			delayed.act()

	def loan(self, loan, income):

		if income.amount == 0:
			return
		
		payment = loan.get_payment()
		if income.amount >= payment:

			loan.pay(payment, "Planilla", self.day)
			self.accounts[self.registered['loan']]['amount'] += payment
			self.accounts[self.registered['loan']]['number'] += 1
			income.amount -= payment
			database.create_deduction(loan.affiliate, payment, self.accounts[self.registered['loan']])

		else:
			loan.pay(income.amount, "Planilla", self.day)
			self.accounts[self.registered['incomplete']]['amount'] += income.amount
			self.accounts[self.registered['incomplete']]['number'] += 1
			income.amount = 0
			database.create_deduction(loan.affiliate, payment, self.accounts[self.registered['incomplete']])

class Corrector(object):
	
	def __init__(self, loans):
		
		self.affiliates = (l.affiliate for l in loans if len(l.affiliate.loans) == 2 and l.affiliate.payment == "Escalafon")
	
	def correct(self):
		
		for a in self.affiliates:
			
			if len(a.loans) == 2:
			
				loan.affiliate.loans[1].pays[0].revert()
				loan.affiliate.loans[0].remove()

class ReporteLine(object):
	
	def __init__(self, affiliate, amount):
		
		self.amount = amount
		self.affiliate = affiliate
	
	def __str__(self):
	
		total = self.amount * Decimal(100)
		zeros = '%(#)018d' % {"#":total}
		if self.affiliate.cardID == None:
			return ""
		return self.affiliate.cardID.replace('-', '') + '0011' + zeros

class Reporter(object):
	
	def __init__(self, year, month):
		
		self.year = year
		self.month = month
		self.lines = []
		self.filename = "./%(year)s%(month)02dCOPEMH.txt" % {'year':self.year, 'month':self.month}
	
	def create_delayed(self):
		
		affiliates = database.get_affiliates_by_payment("Escalafon")
		for affiliate in affiliates:
			
			delayed = affiliate.get_delayed()
			
			if delayed != None: database.create_delayed(affiliate, delayed)
	
	def process_affiliates(self):
		
		affiliates = database.get_affiliates_by_payment("Escalafon")
		obligation = database.get_obligation(self.year, self.month)
		
		for affiliate in affiliates:
			
			if not affiliate.active: continue
			
			amount = 0
			
			for e in affiliate.extras: amount += e.amount
			
			for loan in affiliate.loans: amount += loan.get_payment()
			
			amount += obligation
			line = ReportLine(affiliate, amount)
			self.lines.append(line)
	
	def write_file(self):
		
		f = open(self.filename, 'w')
		start = "%(year)s%(month)02d" % {'year':int(year), 'month':int(month)}
		
		for line in self.lines:
			str_line = str(line)
			if str_line == "":
				continue
			l = start + str_line + "\n"
			f.write(l)

