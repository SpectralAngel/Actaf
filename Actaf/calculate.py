__author__ = 'Carlos'


import database

loans = database.get_all_loans()

for loan in loans:
    loan.vencidas = loan.calcular_vencidas()
    loan.acumulado = loan.interes_acumulado(loan.vencidas)
    loan.vence = loan.vencimiento()
