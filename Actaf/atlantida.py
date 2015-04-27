from datetime import date
import database
import csv
from generators import Atlantida


if __name__ == '__main__':
    faltantes = csv.reader(open('atlantida.csv'))
    afiliados = []

    for line in faltantes:
        afiliados.append(database.get_affiliate(int(line[0])))

    print afiliados

    generator = Atlantida(database.Banco.get(1001020), afiliados, date.today())
    generator.output()
