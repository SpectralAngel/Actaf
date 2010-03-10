#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# database.py
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

from model import *

def obtener_conexion():
    
    return scheme

def get_affiliate(afiliacion):
    
    """Obtiene un afiliado por número de afiliación""" 
    
    return Affiliate.get(afiliacion)

def get_loan(prestamo):
    
    return Loan.get(prestamo)

def get_affiliates_by_payment(payment, active_only=False):
    
    if active_only:
        return Affiliate.selectBy(payment=payment, active=True)
    
    return Affiliate.select(Affiliate.q.payment==payment)

def get_all_affiliates():
    
    return Affiliate.select()

def get_loans_by_period(start, end):
    
    query = "loan.start_date >= '%s' and loan.start_date <= '%s'" % (start, end)

    return Loan.select(query)

def get_all_loans():
    
    return Loan.select()

def get_obligation(year, month, inprema=False):
    
    obligations = Obligation.selectBy(year=year, month=month)
    if inprema:
        return sum(o.inprema for o in obligations)
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

def get_help_account():
    
    return Account.get(495)

def get_income_report(year, month):
    
    return PostReport.selectBy(year=year, month=month)[0]

def efectuar_pago(loan, amount, day, method='Planilla'):
    
    loan.pay(amount, method, day)

def create_deduction(affiliate, amount, account):
    
    return Deduced(affiliate=affiliate, account=account, amount=amount)

def create_report(accounts, year, month):
    
    report = PostReport(year=year, month=month)
    for account in accounts:
        if accounts[account]['amount'] != 0:
            ReportAccount(name=account.name, amount=accounts[account]['amount'],
                    quantity=accounts[account]['number'], postReport=report)
    
    return report

def create_other_report(accounts, year, month, other):
    
    report = OtherReport(year=year, month=month, payment=other)
    for account in accounts:
        if accounts[account]['amount'] != 0:
            OtherAccount(amount=accounts[account]['amount'],
                    quantity=accounts[account]['number'], otherReport=report, account=account)
    
    return report

