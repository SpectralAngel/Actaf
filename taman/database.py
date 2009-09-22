#!/usr/bin/env python
# -*- coding: utf8 -*-
# database.py
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

from model import *

def get_affiliates_by_payment(payment):
	
	return Affiliate.select(Affiliate.q.payment==payment)

def get_loans_by_period(start, end):
	
	query = "loan.start_date >= '%s' and loan.start_date <= '%s'" % (start, end)

	return Loans.q.select(query)

def get_obligation(year, month, inprema=False):
	
	query = "obligation.year = %s and obligation.month = %s" % (year, month)
	obligations = Obligation.select(query)
	if inprema: return sum(o.inprema for o in obligations)
	return sum(o.amount for o in obligations)

def get_accounts():
	
	return Account.select()

def get_loan_account():
	
	return Account.get(659)

def get_cuota_account():
	
	return Account.get(1)

def get_exceding_account():
	
	return Account.get(674)

def get_incomplete_account():
	
	return Account.get(659)

def get_income_report(year, month):
	
	return PostReport.select("post_report.year = %s and post_report.month = %s "
							 % (year, month))

def create_deduction(affiliate, amount, account):
	
	return Deduced(affiliate=affiliate, account=account, amount=amount)

def create_report(accounts, year, month):
	
	report = PostReport(year=year, month=month)
	for key in accounts:
		if accounts[key]['amount'] != 0:
			ReportAccount(name=key.name, amount=accounts[key]['amount'],
					quantity=accounts[key]['number'], postReport=report)
		
	
	return report

def create_other_report(accounts, year, month, other):
	
	report = OtherReport(year=year, month=month, payment=other)
	for key in accounts:
		if accounts[key]['amount'] != 0:
			OtherAccount(amount=accounts[key]['amount'],
					quantity=accounts[key]['number'], otherReport=report, account=key)
	
	return report

def create_delayed(affiliate, delayed):
	
	kw = {}
	kw['affiliate'] = affiliate
	kw['month'] = delayed.delayed()

