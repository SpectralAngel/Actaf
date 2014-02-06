import model

if __name__ == "__main__":
    cuenta = model.Account.get(674)

    print("Procesando Deducciones Bancarias")
    deducciones = model.DeduccionBancaria.selectBy(
        account=cuenta, month=11, year=2013)

    print(deducciones.count())

    for deduccion in deducciones:

        for extra in deduccion.afiliado.extras:

            if extra.amount == deduccion.amount:
                deduccion.account = extra.account
                print(deduccion.amount)
    print("Procesando Deducciones Planilla")

    deducciones = model.Deduced.selectBy(
        account=cuenta, month=11, year=2013)
    print(deducciones.count())

    for deduccion in deducciones:

        for extra in deduccion.affiliate.extras:

            if extra.amount <= deduccion.amount:
                deduccion.account = extra.account
                print(deduccion.amount)
