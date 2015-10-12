import database
import csv


def obtener_afiliado(afiliado):
    return database.get_affiliate(int(afiliado[0]))


if __name__ == '__main__':
    banco = database.Banco.get(1001060)

    cuentas = csv.reader(open('cuentas.csv'))
    correctas = csv.reader(open('correctas.csv'))
    archivo = csv.writer(open('final.txt', 'wb'))
    li = database.get_affiliates_by_banco(banco)
    afiliados = dict()
    for a in li:
        afiliados[a.cuenta] = a

    montos = dict()
    identidades = dict()
    incorrectas = list()
    for cuenta in cuentas:
        if not cuenta[0] in afiliados:
            print(cuenta[0])
            continue
        afiliado = afiliados[cuenta[0]]
        identidad = afiliado.cardID.replace('-', '')
        montos[identidad] = cuenta[1]
        identidades[identidad] = afiliado
        incorrectas.append(cuenta)
    print(len(montos))
    for row in correctas:

        identidad = '{0:013d}'.format(int(row[0].replace('-', '')))
        if not identidad in montos:
            continue
        afiliado = identidades[identidad]
        archivo.writerow([
            "1001060",
            "A",
            str(row[1]),
            "2",
            "2",
            str(montos[identidad]),
            "{0} {1} {2}".format(afiliado.id, afiliado.firstName,
                                 afiliado.lastName)
        ])
