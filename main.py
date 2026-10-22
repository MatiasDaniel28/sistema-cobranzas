import json
import os
from datetime import datetime

def cargar_clientes():
    try:
        with open("clientes.json", "r") as archivo:
            datos = json.load(archivo)

    except FileNotFoundError:
        datos = {
            "ultimo_id": 0,
            "clientes": []
    }

    except json.JSONDecodeError:
        print("ERROR: El archivo clientes.json está dañado.")
        print("No se cargarán datos vacíos para evitar perder información.")
        raise
        

    # Migrar formato viejo al nuevo
    if isinstance(datos, list):
        clientes = datos
        ultimo_id = 0

        for cliente in clientes:
            if 'id' in cliente and cliente['id'] > ultimo_id:
                ultimo_id = cliente['id']

        datos = {
            "ultimo_id": ultimo_id,
            "clientes": clientes
        }

    if not isinstance(datos, dict):
        raise ValueError("El archivo JSON tiene una estructura incorrecta.")

    if "clientes" not in datos or "ultimo_id" not in datos:
        raise ValueError("Faltan datos obligatorios en el archivo JSON.")

    if not isinstance(datos["clientes"], list):
        raise ValueError("La lista de clientes tiene un formato incorrecto.")

    
    if not isinstance(datos["ultimo_id"], int) or isinstance(datos["ultimo_id"], bool):
        raise ValueError("El último ID tiene un formato incorrecto.")


    clientes = datos["clientes"]
    hubo_cambios = False
    ids_vistos = set()

    # Completar y validar los datos de cada cliente
    for cliente in clientes:

        if not isinstance(cliente, dict):
            raise ValueError("Hay un cliente con una estructura incorrecta.")

        if 'id' not in cliente:
            datos["ultimo_id"] += 1
            cliente['id'] = datos["ultimo_id"]
            hubo_cambios = True

        if not isinstance(cliente['id'], int) or isinstance(cliente['id'], bool) or cliente['id'] <= 0:
            raise ValueError("Hay un cliente con un ID inválido.")

        if cliente['id'] in ids_vistos:
            raise ValueError("Hay clientes con IDs duplicados.")

        ids_vistos.add(cliente['id'])

        if cliente['id'] > datos["ultimo_id"]:
            datos["ultimo_id"] = cliente['id']
            hubo_cambios = True

        if 'nombre' not in cliente or not isinstance(cliente['nombre'], str) or not cliente['nombre'].strip():
            raise ValueError("Hay un cliente con un nombre inválido.")

        if 'deuda' not in cliente:
            raise ValueError("Hay un cliente sin deuda registrada.")

        if (
            not isinstance(cliente['deuda'], (int, float))
            or isinstance(cliente['deuda'], bool)
            or cliente['deuda'] < 0
        ):
            raise ValueError("Hay un cliente con una deuda inválida.")

        if 'estado' not in cliente:
            raise ValueError("Hay un cliente sin estado registrado.")

        if cliente['estado'] not in ('SIN DEUDA', 'CON DEUDA'):
            raise ValueError("Hay un cliente con un estado inválido.")

        if (cliente['deuda'] == 0 and cliente['estado'] != 'SIN DEUDA') or (
            cliente['deuda'] > 0 and cliente['estado'] != 'CON DEUDA'
        ):
            raise ValueError("El estado de un cliente no coincide con su deuda.")

        if 'pagos' not in cliente:
            cliente['pagos'] = []
            hubo_cambios = True

        if not isinstance(cliente['pagos'], list):
            raise ValueError("El historial de pagos tiene un formato incorrecto.")

        if 'modificaciones' not in cliente:
            cliente['modificaciones'] = []
            hubo_cambios = True

        if not isinstance(cliente['modificaciones'], list):
            raise ValueError("El historial de modificaciones tiene un formato incorrecto.")

    if hubo_cambios:
        guardar_datos(datos)

    return datos




def guardar_datos(datos):
    archivo_temporal = "clientes.json.tmp"

    try:
        with open(archivo_temporal, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)

        os.replace(archivo_temporal, "clientes.json")

    except OSError:
        if os.path.exists(archivo_temporal):
            try:
                os.remove(archivo_temporal)
            except OSError:
                pass

        raise




def mostrar_menu():
    print("==== SISTEMA DE COBRANZA ====")
    print("1. Agregar cliente")
    print("2. Mostrar clientes")
    print("3. Buscar cliente")
    print("4. Registrar pago")
    print("5. Eliminar cliente")
    print("6. Editar cliente")
    print("7. Ver historial de pagos")
    print("8. Ver historial de modificaciones")
    print("9. Resumen de cobranzas")
    print("10. Reporte de pagos por fecha")
    print("11. Salir")


def mostrar_clientes(clientes):
    if not clientes:
        print("No hay clientes registrados.")
    else:
        print("==== LISTA DE CLIENTES ====")
        for cliente in clientes:
            print(f"ID: {cliente['id']}")
            print(f"Nombre: {cliente['nombre']}")
            print(f"Deuda: {cliente['deuda']}")
            print(f"Estado: {cliente['estado']}")



def agregar_cliente(datos):
    clientes = datos["clientes"]
    cliente = {
        'pagos': [],
        'modificaciones': []
    }

    while True:
        cliente['nombre'] = input("Escriba el nombre del cliente: ").strip().lower()

        if cliente['nombre'] == "":
            print("ERROR: El nombre no puede estar vacío.")
        else:
            break

    while True:
        try:
            deuda = float(input("Escriba la deuda: "))

            if deuda < 0:
                print("ERROR: La deuda no puede ser negativa.")
                continue

            cliente['deuda'] = deuda

            if deuda == 0:
                cliente['estado'] = 'SIN DEUDA'
            else:
                cliente['estado'] = 'CON DEUDA'

            datos["ultimo_id"] += 1
            cliente['id'] = datos["ultimo_id"]

            clientes.append(cliente)
            guardar_datos(datos)

            print("Cliente agregado exitosamente.")
            break

        except ValueError:
            print("ERROR: Por favor, ingrese un número válido para la deuda.")




def registrar_pago(datos):
    clientes = datos["clientes"]

    try:
        id_cliente = int(input("Ingrese el ID del cliente para registrar el pago: "))
    except ValueError:
        print("ERROR: Ingrese un ID válido.")
        return

    for cliente in clientes:
        if cliente['id'] == id_cliente:
            if cliente['deuda'] == 0:
                print("El cliente no tiene deuda pendiente.")
                return

            while True:
                try:
                    pago = float(input("Ingrese el monto del pago: "))

                    if pago <= 0:
                        print("El pago debe ser mayor a cero.")

                    elif pago > cliente['deuda']:
                        print("El pago no puede superar la deuda.")

                    else:
                        cliente['deuda'] -= pago

                        if cliente['deuda'] == 0:
                            cliente['estado'] = 'SIN DEUDA'
                            print("Pago registrado. El cliente ya no tiene deuda.")
                        else:
                            cliente['estado'] = 'CON DEUDA'
                            print(f"Pago registrado. Deuda restante: {cliente['deuda']}")

                        print(f"Estado del cliente: {cliente['estado']}")

                        cliente['pagos'].append({
                            'monto': pago,
                            'fecha': datetime.now().strftime("%Y-%m-%d")
                        })

                        guardar_datos(datos)
                        return

                except ValueError:
                    print("ERROR: Por favor, ingrese un número válido para el pago.")

    print("Cliente no encontrado.")


def buscar_cliente(clientes):
    try:
        id_cliente = int(input("Ingrese el ID del cliente a buscar: "))
    except ValueError:
        print("ERROR: Ingrese un id válido.")
        return

    for cliente in clientes:
        if cliente['id'] == id_cliente:
            print(f"ID: {cliente['id']}")
            print(f"Nombre: {cliente['nombre']}")
            print(f"Deuda: {cliente['deuda']}")
            print(f"Estado: {cliente['estado']}")
            return
    print("Cliente no encontrado.")


def eliminar_cliente(datos):
    clientes = datos["clientes"]

    try:
        id_cliente = int(input("Ingrese el ID del cliente a eliminar: "))
    except ValueError:
        print("ERROR: Ingrese un ID válido.")
        return

    for cliente in clientes:
        if cliente['id'] == id_cliente:
            print(f"Cliente encontrado: {cliente['nombre']}")
            confirmacion = input(
                "¿Está seguro de eliminarlo? Escriba SI para confirmar: "
            ).strip().upper()

            if confirmacion != "SI":
                print("Eliminación cancelada.")
                return

            clientes.remove(cliente)
            guardar_datos(datos)
            print("Cliente eliminado exitosamente.")
            return

    print("Cliente no encontrado.")


def editar_cliente(datos):
    clientes = datos["clientes"]
    try:
        id_cliente = int(input("Ingrese el ID del cliente a editar: "))
    except ValueError:
        print("ERROR: Ingrese un ID válido.")
        return

    for cliente in clientes:
        if cliente['id'] == id_cliente:
            print("Cliente encontrado.")
            print("¿Que desea editar?")
            print("1. Nombre")
            print("2. Deuda")
            print("3. Salir")
            opcion_editar = input("Seleccione una opción: ")
            
            if opcion_editar == "1":
                while True:
                    nuevo_nombre = input(
                        "Ingrese el nuevo nombre del cliente: "
                    ).strip().lower()

                    if nuevo_nombre == "":
                        print("ERROR: El nombre no puede estar vacío.")
                    else:
                        break

                nombre_anterior = cliente["nombre"]

                if nuevo_nombre == nombre_anterior:
                    print(
                        "El nombre ingresado es igual al actual. "
                        "No se realizaron cambios."
                    )
                    return

                cliente["modificaciones"].append({
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "tipo": "nombre",
                    "nombre_anterior": nombre_anterior,
                    "nombre_nuevo": nuevo_nombre
                })

                cliente["nombre"] = nuevo_nombre
                guardar_datos(datos)

                print("Cliente editado exitosamente.")
                return

            elif opcion_editar == "2":
                while True:
                    try:
                        nueva_deuda = float(input("Ingrese la nueva deuda del cliente: "))
                        if nueva_deuda < 0:
                            print("ERROR: La deuda no puede ser negativa.")
                        else:

                            if nueva_deuda == cliente['deuda']:
                                print("La deuda ingresada es igual a la actual. No se realizaron cambios.")
                                return
                            deuda_anterior = cliente['deuda']

                            cliente['modificaciones'].append({
                                "fecha": datetime.now().strftime("%Y-%m-%d"),
                                "tipo": "deuda",
                                "deuda_anterior": deuda_anterior,
                                "deuda_nueva": nueva_deuda
                            })

                            cliente['deuda'] = nueva_deuda
                            if nueva_deuda == 0:
                                cliente['estado'] = 'SIN DEUDA'
                            else:
                                cliente['estado'] = 'CON DEUDA'
                            guardar_datos(datos)
                            print("Cliente editado exitosamente.")
                            return
    
                    except ValueError:
                        print("ERROR: Por favor, ingrese un número válido para la deuda.")
            elif opcion_editar == "3":
                print("Saliendo de la edición.")
                return
            else:
                print("Opción no válida.")
                return
    print("Cliente no encontrado.")


def mostrar_historial(clientes):
    try:
        id_cliente = int(input("Ingrese el ID del cliente para ver el historial de pagos: "))
    except ValueError:
        print("ERROR: Ingrese un id válido.")
        return

    for cliente in clientes:
        if cliente['id'] == id_cliente:
            if not cliente['pagos']:
                print("El cliente no tiene pagos registrados.")
            else:
                print(f"Historial de pagos del cliente {cliente['nombre']}:")
                for pago in cliente['pagos']:
                    print(f"Monto: {pago['monto']}, Fecha: {pago['fecha']}")
            return
    print("Cliente no encontrado.")


def mostrar_modificaciones(clientes):
    try:
        id_cliente = int(input("Ingrese el ID del cliente para ver el historial de modificaciones: "))
    except ValueError:
        print("ERROR: Ingrese un ID válido.")
        return

    for cliente in clientes:
        if cliente['id'] == id_cliente:
            if not cliente['modificaciones']:
                print("El cliente no tiene modificaciones registradas.")
            else:
                print(f"Historial de modificaciones del cliente {cliente['nombre']}:")

                for modificacion in cliente['modificaciones']:
                    if modificacion.get('tipo') == 'nombre':
                        print(
                            f"Fecha: {modificacion['fecha']}, "
                            f"Nombre anterior: {modificacion['nombre_anterior']}, "
                            f"Nombre nuevo: {modificacion['nombre_nuevo']}"
                        )
                    else:
                        print(
                            f"Fecha: {modificacion['fecha']}, "
                            f"Deuda anterior: {modificacion['deuda_anterior']}, "
                            f"Deuda nueva: {modificacion['deuda_nueva']}"
                        )
            return

    print("Cliente no encontrado.")


def mostrar_resumen(clientes):
    total_clientes = len(clientes)
    clientes_con_deuda = 0
    clientes_sin_deuda = 0
    total_pendiente = 0

    for cliente in clientes:
        if cliente['deuda'] > 0:
            clientes_con_deuda +=1
        else:
            clientes_sin_deuda +=1

        total_pendiente += cliente['deuda']

    print("\n=== RESUMEN DE COBRANZAS ===")
    print(f"Total de clientes: {total_clientes}")
    print(f"Clientes con deuda: {clientes_con_deuda}")
    print(f"Clientes sin deudas: {clientes_sin_deuda}")
    total_formateado = f"{total_pendiente:,.2f}"
    total_formateado = total_formateado.replace(",", "X").replace(".", ",").replace("X", ".")
    print(f"total pendiente de cobrar: ${total_formateado}")


def reporte_pagos(clientes):
    fecha_consultada = input("Ingrese la fecha a consultar (AAA-MM-DD): ").strip()
    try:
        datetime.strptime(fecha_consultada, "%Y-%m-%d")
    except ValueError:
        print("ERROR: La fecha debe tener el formato AAAA-MM-DD.")
        return

    cantidad_pagos = 0
    total_recaudado = 0

    for cliente in clientes:
        for pago in cliente['pagos']:
            if pago['fecha'] == fecha_consultada:
                cantidad_pagos += 1
                total_recaudado += pago['monto']

    total_formateado = f"{total_recaudado:,.2f}"
    total_formateado = total_formateado.replace(",", "X").replace(".", ",").replace("X", ".")

    print("\n=== REPORTE DE PAGOS ===")
    print(f"Fecha consultada: {fecha_consultada}")
    print(f"Cantidad de pagos: {cantidad_pagos}")
    print(f"Total recaudado: ${total_formateado}")



def main():
    datos = cargar_clientes()
    clientes = datos["clientes"]

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            agregar_cliente(datos)
        elif opcion == "2":
            mostrar_clientes(clientes)
        elif opcion == "3":
            buscar_cliente(clientes)
        elif opcion == "4":
            registrar_pago(datos)
        elif opcion == "5":
            eliminar_cliente(datos)
        elif opcion == "6":
            editar_cliente(datos)
        elif opcion == "7":
            mostrar_historial(clientes)
        elif opcion == "8":
            mostrar_modificaciones(clientes)
        elif opcion == "9":
            mostrar_resumen(clientes)
        elif opcion == "10":
            reporte_pagos(clientes)
        elif opcion == "11":
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Por favor, seleccione una opción válida.")


if __name__ == "__main__":
    main()
