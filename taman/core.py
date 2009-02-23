#!/usr/bin/env python
# -*- coding: utf8 -*-
from decimal import Decimal

class Income(object):

	def __init__(self, affiliate, amount):

		(self.affiliate, self.amount) = (affiliate, amount)

class Parser(object):

	def __init__(self, filename, affiliates):

		self.file = open(filename)
		self.affiliates = affiliates
		self.parsed = []

	def parse(self):

		for line in self.file:

			amount = Decimal(str(line[94:111])) / hundred
			card = str(line[6:10] + '-' + line[10:14] + '-' + line[14:19])
			try:
				self.parsed.append(Income(affiliates[card], amount))

			except:
				print("Error de parseo no se encontro la identidad %s" % card)

		return self.parsed

class Updater(object):

	def __init__(self, obligation, accounts, day):

		self.obligation = obligation
		self.accounts = accounts
		self.day = day
		self.registered = {}

	def register_account(self, account, name):

		self.registered[name] = account

	def update(self, income):

		self.cuota(income.affiliate, income.amount)
		self.extra(income.affiliate, income.amount)
		(self.loan(loan, income.amount) for loan in affiliate.loans)
		if income.amount > 0:
			
			self.exceding(income.affiliate, income.amount)

	def cuota(self, affiliate, amount):

		if amount >= self.obligation:

			self.accounts[self.registered['cuota']]['amount'] += self.obligation
			self.accounts[self.registered['cuota']]['number'] += 1
			affiliate.pay_cuota(day.year, day.month)
			amount -= obligation
			database.create_deduction(affiliate, obligation, self.accounts[self.registered['cuota']])

	def extra(self, affiliate, amount):

		extras = sum(e.amount for e in affiliate.extras)
		if amount >= extras:
			amount -= extras
			for extra in affiliate.extras:
				self.acdict[extra.account]['amount'] += extra.amount
				self.acdict[extra.account]['number'] += 1
				extra.act()
		else:
			for extra in affiliate.extras:
				if converted.amount >= extra.amount:
					converted.amount -= extra.amount
					self.acdict[extra.account]['amount'] += extra.amount
					self.acdict[extra.account]['number'] += 1
					extra.act()

	def exceding(self, affiliate, amount):

		self.accounts[self.registered['exceding']]['amount'] += amount
		self.accounts[self.registered['exceding']]['number'] += 1
		database.create_deduction(affiliate, amount, self.accounts[self.registered['exceding']])

	def loan(self, loan, amount):

		if amount == 0:
			return

		payment = loan.get_payment()
		if amount >= payment:

			loan.pay(payment, "Planilla", self.day)
			self.accounts[self.registered['loan']]['amount'] += payment
			self.accounts[self.registered['loan']]['number'] += 1
			amount -= payment
			database.create_deduction(affiliate, payment, self.accounts[self.registered['loan']])

		else:
			loan.pay(amount, "Planilla", self.day)
			self.accounts[self.registered['incomplete']]['amount'] += amount
			self.accounts[self.registered['incomplete']]['number'] += 1
			database.create_deduction(affiliate, payment, self.accounts[self.registered['incomplete']])

class Corrector(object):
	
	def __init__(self, loans):
		
		self.affiliates = (l.affiliate for l in loans if len(l.affiliate.loans) == 2 and l.affiliate.payment == "Escalafon")
	
	def correct(self):
		
		for a in self.affiliates:
			
			if len(a.loans) == 2:
			
				loan.affiliate.loans[1].pays[0].revert()
				loan.affiliate.loans[0].remove()
