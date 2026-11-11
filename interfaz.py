
import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from tkinter import simpledialog
import os
import tempfile
import shutil
from datetime import datetime
import sys

# Colores de la aplicación
FONDO = "#F4F6F9"
AZUL_OSCURO = "#172554"
AZUL = "#2563EB"
BLANCO = "#FFFFFF"
GRIS = "#64748B"

# Archivo de datos, ubicado junto a interfaz.py

# Carpeta donde se guardan los datos del programa
if getattr(sys, "frozen", False):
    CARPETA_APP = Path(sys.executable).resolve().parent
else:
    CARPETA_APP = Path(__file__).resolve().parent

ARCHIVO_DATOS = CARPETA_APP / "clientes.json"



def cargar_clientes():
    """Lee los clientes guardados en el archivo JSON."""
    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        # Admite el formato actual y el formato antiguo en forma de lista
        if isinstance(datos, list):
            clientes = datos
        elif isinstance(datos, dict):
            clientes = datos.get("clientes", [])
        else:
            raise ValueError("El formato del archivo no es válido.")

        if not isinstance(clientes, list):
            raise ValueError("La lista de clientes no es válida.")

        return clientes


    except FileNotFoundError:
        # Crear automáticamente el archivo la primera vez
        datos_iniciales = {
            "ultimo_id": 0,
            "clientes": []
        }

        try:
            with open(ARCHIVO_DATOS, "x", encoding="utf-8") as archivo:
                json.dump(
                    datos_iniciales,
                    archivo,
                    indent=4,
                    ensure_ascii=False
                )
                archivo.write("\n")

        except OSError as error:
            messagebox.showerror(
                "Error al crear los datos",
                f"No se pudo crear clientes.json:\n{error}"
            )
            return []

        return []


    except (json.JSONDecodeError, ValueError) as error:
        messagebox.showerror(
            "Error en los datos",
            f"No se pudieron leer los clientes:\n{error}"
        )
        return []


def formatear_pesos(monto):
    """Muestra importes con formato argentino."""
    texto = f"{monto:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {texto}"



def guardar_nuevo_cliente(nombre, deuda):
    """Agrega un cliente al JSON compartido de forma segura."""
    nombre = nombre.strip().lower()

    if not nombre:
        raise ValueError("El nombre no puede estar vacío.")

    if deuda < 0:
        raise ValueError("La deuda no puede ser negativa.")

    if not deuda < float("inf"):
        raise ValueError("La deuda debe ser un número válido.")

    # Leer los datos actuales para no sobrescribir cambios recientes
    with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    if isinstance(datos, list):
        raise ValueError(
            "El archivo usa el formato antiguo. "
            "Abrilo y guardalo primero desde main.py."
        )

    clientes = datos["clientes"]

    # Evitar IDs duplicados y mantener el consecutivo
    ultimo_id = max(
        int(datos.get("ultimo_id", 0)),
        max((int(c["id"]) for c in clientes), default=0)
    )
    nuevo_id = ultimo_id + 1

    cliente = {
        "id": nuevo_id,
        "nombre": nombre,
        "deuda": deuda,
        "estado": "SIN DEUDA" if deuda == 0 else "CON DEUDA",
        "pagos": [],
        "modificaciones": []
    }

    datos["ultimo_id"] = nuevo_id
    clientes.append(cliente)

    # Guardar primero en un archivo temporal y luego reemplazar el JSON
    ruta_temporal = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=ARCHIVO_DATOS.parent,
            suffix=".tmp",
            delete=False
        ) as archivo:
            ruta_temporal = archivo.name
            json.dump(datos, archivo, indent=4, ensure_ascii=False)
            archivo.write("\n")
            archivo.flush()
            os.fsync(archivo.fileno())


        # Guardar una copia de los datos anteriores
        crear_copia_seguridad()

        # Reemplazar el archivo original con los datos nuevos
        os.replace(ruta_temporal, ARCHIVO_DATOS)

    finally:

        if ruta_temporal and os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

    return cliente



def editar_cliente(identificador, nuevo_nombre, nueva_deuda):
    """Actualiza un cliente y registra los cambios en su historial."""
    nuevo_nombre = nuevo_nombre.strip().lower()

    if not nuevo_nombre:
        raise ValueError("El nombre no puede estar vacío.")

    if nueva_deuda < 0 or nueva_deuda == float("inf"):
        raise ValueError("La deuda debe ser un número válido y no negativo.")

    with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    if not isinstance(datos, dict) or not isinstance(datos.get("clientes"), list):
        raise ValueError("El archivo de clientes tiene un formato inválido.")

    cliente = next(
        (c for c in datos["clientes"] if str(c.get("id")) == str(identificador)),
        None
    )

    if cliente is None:
        raise ValueError("No se encontró el cliente seleccionado.")

    cambios = []
    nombre_anterior = cliente.get("nombre", "")
    deuda_anterior = float(cliente.get("deuda", 0))

    if nombre_anterior != nuevo_nombre:
        cambios.append({
            "campo": "nombre",
            "anterior": nombre_anterior,
            "nuevo": nuevo_nombre
        })

    if deuda_anterior != nueva_deuda:
        cambios.append({
            "campo": "deuda",
            "anterior": deuda_anterior,
            "nuevo": nueva_deuda
        })

    if not cambios:
        return cliente

    cliente["nombre"] = nuevo_nombre
    cliente["deuda"] = nueva_deuda
    cliente["estado"] = "SIN DEUDA" if nueva_deuda == 0 else "CON DEUDA"

    if not isinstance(cliente.get("modificaciones"), list):
        cliente["modificaciones"] = []

    from datetime import datetime

    for cambio in cambios:
        cliente["modificaciones"].append({
            **cambio,
            "fecha": datetime.now().strftime("%Y-%m-%d")
        })

    # Escritura temporal para reducir el riesgo de dañar el JSON
    ruta_temporal = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=ARCHIVO_DATOS.parent,
            suffix=".tmp",
            delete=False
        ) as archivo:
            ruta_temporal = archivo.name
            json.dump(datos, archivo, indent=4, ensure_ascii=False)
            archivo.write("\n")
            archivo.flush()
            os.fsync(archivo.fileno())


        # Crear una copia antes de guardar la edición
        crear_copia_seguridad()

        # Reemplazar el archivo original con los datos actualizados
        os.replace(ruta_temporal, ARCHIVO_DATOS)

    finally:

        if ruta_temporal and os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

    return cliente




def mostrar_clientes(ventana):
    # Crear una nueva ventana
    pantalla = tk.Toplevel(ventana)
    pantalla.title("Gestión de clientes")
    pantalla.geometry("850x500")
    pantalla.configure(bg=FONDO)

    # Encabezado
    encabezado = tk.Frame(pantalla, bg=FONDO)
    encabezado.pack(fill="x", padx=25, pady=(20, 10))

    tk.Label(
        encabezado,
        text="Gestión de clientes",
        font=("Segoe UI", 22, "bold"),
        bg=FONDO,
        fg=AZUL_OSCURO
    ).pack(anchor="w")

    tk.Label(
        encabezado,
        text="Consultá y buscá los clientes registrados",
        font=("Segoe UI", 10),
        bg=FONDO,
        fg=GRIS
    ).pack(anchor="w", pady=(5, 0))

    # Buscador

    buscador_frame = tk.Frame(pantalla, bg=FONDO)
    buscador_frame.pack(fill="x", padx=25, pady=10)

    barra_acciones = tk.Frame(pantalla, bg=FONDO)
    barra_acciones.pack(fill="x", padx=25, pady=(0, 10))

    def nuevo_cliente():
        formulario = tk.Toplevel(pantalla)
        formulario.title("Nuevo cliente")
        formulario.geometry("380x260")
        formulario.resizable(False, False)
        formulario.configure(bg=FONDO)
        formulario.transient(pantalla)
        formulario.grab_set()

        tk.Label(
            formulario,
            text="Registrar cliente",
            font=("Segoe UI", 18, "bold"),
            bg=FONDO,
            fg=AZUL_OSCURO
        ).pack(anchor="w", padx=25, pady=(20, 15))

        tk.Label(
            formulario,
            text="Nombre",
            bg=FONDO,
            fg=AZUL_OSCURO
        ).pack(anchor="w", padx=25)

        entrada_nombre = ttk.Entry(formulario, font=("Segoe UI", 11))
        entrada_nombre.pack(fill="x", padx=25, pady=(4, 12))

        tk.Label(
            formulario,
            text="Deuda inicial",
            bg=FONDO,
            fg=AZUL_OSCURO
        ).pack(anchor="w", padx=25)

        entrada_deuda = ttk.Entry(formulario, font=("Segoe UI", 11))
        entrada_deuda.pack(fill="x", padx=25, pady=(4, 15))

        def guardar():
            nombre = entrada_nombre.get()
            texto_deuda = entrada_deuda.get().strip().replace(",", ".")

            if not nombre.strip():
                messagebox.showerror(
                    "Dato obligatorio",
                    "Ingresá el nombre del cliente.",
                    parent=formulario
                )
                return

            try:
                deuda = float(texto_deuda)

                if deuda < 0 or not __import__("math").isfinite(deuda):
                    raise ValueError

                cliente = guardar_nuevo_cliente(nombre, deuda)

            except ValueError:
                messagebox.showerror(
                    "Deuda inválida",
                    "Ingresá un número válido, mayor o igual a cero.",
                    parent=formulario
                )
                return

            except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
                messagebox.showerror(
                    "Error al guardar",
                    f"No se pudo guardar el cliente:\n{error}",
                    parent=formulario
                )
                return

            messagebox.showinfo(
                "Cliente registrado",
                f"Se agregó a {cliente['nombre']} con ID {cliente['id']}.",
                parent=formulario
            )

            formulario.destroy()
            actualizar_tabla()
            entrada.delete(0, tk.END)

        tk.Button(
            formulario,
            text="Guardar cliente",
            command=guardar,
            bg=AZUL,
            fg=BLANCO,
            activebackground=AZUL_OSCURO,
            activeforeground=BLANCO,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8
        ).pack(anchor="e", padx=25, pady=(0, 15))

        entrada_nombre.focus_set()

    tk.Button(
        barra_acciones,
        text="+ Nuevo cliente",
        command=nuevo_cliente,
        bg=AZUL,
        fg=BLANCO,
        activebackground=AZUL_OSCURO,
        activeforeground=BLANCO,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        padx=15,
        pady=8
    ).pack(side="right")



    def editar_seleccionado():
        seleccion = tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Seleccioná un cliente",
                "Primero seleccioná un cliente de la tabla.",
                parent=pantalla
            )
            return

        valores = tabla.item(seleccion[0], "values")
        identificador = valores[0]

        # Leer los datos actuales del archivo
        clientes = cargar_clientes()
        cliente = next(
            (c for c in clientes if str(c.get("id")) == str(identificador)),
            None
        )

        if cliente is None:
            messagebox.showerror(
                "Cliente no encontrado",
                "No se encontró el cliente en el archivo.",
                parent=pantalla
            )
            actualizar_tabla()
            return

        formulario = tk.Toplevel(pantalla)
        formulario.title("Editar cliente")
        formulario.geometry("380x280")
        formulario.resizable(False, False)
        formulario.configure(bg=FONDO)
        formulario.transient(pantalla)
        formulario.grab_set()

        tk.Label(
            formulario,
            text=f"Editar cliente #{identificador}",
            font=("Segoe UI", 17, "bold"),
            bg=FONDO,
            fg=AZUL_OSCURO
        ).pack(anchor="w", padx=25, pady=(20, 15))

        tk.Label(
            formulario,
            text="Nombre",
            bg=FONDO,
            fg=AZUL_OSCURO
        ).pack(anchor="w", padx=25)

        entrada_nombre = ttk.Entry(formulario, font=("Segoe UI", 11))
        entrada_nombre.pack(fill="x", padx=25, pady=(4, 12))
        entrada_nombre.insert(0, cliente.get("nombre", ""))

        tk.Label(
            formulario,
            text="Deuda",
            bg=FONDO,
            fg=AZUL_OSCURO
        ).pack(anchor="w", padx=25)

        entrada_deuda = ttk.Entry(formulario, font=("Segoe UI", 11))
        entrada_deuda.pack(fill="x", padx=25, pady=(4, 15))
        entrada_deuda.insert(0, str(cliente.get("deuda", 0)))

        def guardar_edicion():
            nombre = entrada_nombre.get()
            texto_deuda = entrada_deuda.get().strip().replace(",", ".")

            if not nombre.strip():
                messagebox.showerror(
                    "Dato obligatorio",
                    "El nombre no puede estar vacío.",
                    parent=formulario
                )
                return

            try:
                deuda = float(texto_deuda)

                if deuda < 0 or not __import__("math").isfinite(deuda):
                    raise ValueError

                editar_cliente(identificador, nombre, deuda)

            except ValueError as error:
                messagebox.showerror(
                    "Dato inválido",
                    str(error) or "Ingresá una deuda válida, mayor o igual a cero.",
                    parent=formulario
                )
                return

            except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
                messagebox.showerror(
                    "Error al guardar",
                    f"No se pudieron guardar los cambios:\n{error}",
                    parent=formulario
                )
                return

            formulario.destroy()
            actualizar_tabla()

            messagebox.showinfo(
                "Cliente actualizado",
                "Los cambios se guardaron correctamente.",
                parent=pantalla
            )

        tk.Button(
            formulario,
            text="Guardar cambios",
            command=guardar_edicion,
            bg=AZUL,
            fg=BLANCO,
            activebackground=AZUL_OSCURO,
            activeforeground=BLANCO,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8
        ).pack(anchor="e", padx=25, pady=(0, 15))

        entrada_nombre.focus_set()



    def eliminar_seleccionado():
        seleccion = tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Seleccioná un cliente",
                "Primero seleccioná un cliente de la tabla.",
                parent=pantalla
            )
            return

        valores = tabla.item(seleccion[0], "values")
        identificador = str(valores[0])
        nombre = str(valores[1])

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar a {nombre} (ID {identificador})?\n\n"
            "Se eliminarán también sus datos e historiales guardados.",
            parent=pantalla
        )

        if not confirmar:
            return

        archivo_temporal = None

        try:
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            if isinstance(datos, dict):
                clientes = datos.get("clientes", [])

                clientes_actualizados = [
                    cliente for cliente in clientes
                    if str(cliente.get("id")) != identificador
                ]

                if len(clientes_actualizados) == len(clientes):
                    messagebox.showerror(
                        "Cliente no encontrado",
                        "No se encontró el cliente en el archivo.",
                        parent=pantalla
                    )
                    actualizar_tabla()
                    return

                datos["clientes"] = clientes_actualizados

            elif isinstance(datos, list):
                clientes_actualizados = [
                    cliente for cliente in datos
                    if str(cliente.get("id")) != identificador
                ]

                if len(clientes_actualizados) == len(datos):
                    messagebox.showerror(
                        "Cliente no encontrado",
                        "No se encontró el cliente en el archivo.",
                        parent=pantalla
                    )
                    actualizar_tabla()
                    return

                datos = clientes_actualizados

            else:
                raise ValueError("La estructura del archivo no es válida.")

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(ARCHIVO_DATOS.parent),
                delete=False
            ) as archivo:
                archivo_temporal = archivo.name
                json.dump(datos, archivo, indent=4, ensure_ascii=False)


            # Crear respaldo antes de eliminar al cliente
            crear_copia_seguridad()

            # Guardar los datos actualizados
            os.replace(archivo_temporal, ARCHIVO_DATOS)
            archivo_temporal = None


        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "Error al eliminar",
                f"No se pudo eliminar el cliente:\n{error}",
                parent=pantalla
            )
            return

        finally:
            if archivo_temporal and os.path.exists(archivo_temporal):
                try:
                    os.remove(archivo_temporal)
                except OSError:
                    pass

        actualizar_tabla()

        messagebox.showinfo(
            "Cliente eliminado",
            f"El cliente {nombre} se eliminó correctamente.",
            parent=pantalla
        )

    tk.Button(
        barra_acciones,
        text="Eliminar cliente",
        command=eliminar_seleccionado,
        bg="#B42318",
        fg=BLANCO,
        activebackground="#8E1B12",
        activeforeground=BLANCO,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        padx=15,
        pady=8
    ).pack(side="right", padx=(0, 10))


    tk.Button(
        barra_acciones,
        text="Editar cliente",
        command=editar_seleccionado,
        bg=AZUL_OSCURO,
        fg=BLANCO,
        activebackground=AZUL,
        activeforeground=BLANCO,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        padx=15,
        pady=8
    ).pack(side="right", padx=(0, 10))



    tk.Label(
        buscador_frame,
        text="Buscar por nombre o ID:",
        font=("Segoe UI", 10),
        bg=FONDO,
        fg=AZUL_OSCURO
    ).pack(anchor="w", pady=(0, 5))

    busqueda = tk.StringVar()

    entrada = ttk.Entry(
        buscador_frame,
        textvariable=busqueda,
        font=("Segoe UI", 11)
    )
    entrada.pack(fill="x")

    # Tabla de clientes
    tabla_frame = tk.Frame(pantalla, bg=BLANCO)
    tabla_frame.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=(5, 20)
    )

    columnas = ("id", "nombre", "deuda", "estado")
    tabla = ttk.Treeview(
        tabla_frame,
        columns=columnas,
        show="headings"
    )

    tabla.heading("id", text="ID")
    tabla.heading("nombre", text="Nombre")
    tabla.heading("deuda", text="Deuda")
    tabla.heading("estado", text="Estado")

    tabla.column("id", width=60, anchor="center")
    tabla.column("nombre", width=250)
    tabla.column("deuda", width=150, anchor="e")
    tabla.column("estado", width=150, anchor="center")

    tabla.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    scroll = ttk.Scrollbar(
        tabla_frame,
        orient="vertical",
        command=tabla.yview
    )
    scroll.pack(side="right", fill="y", pady=10)
    tabla.configure(yscrollcommand=scroll.set)

    # Cargar y mostrar los clientes
    def actualizar_tabla(*args):
        for elemento in tabla.get_children():
            tabla.delete(elemento)

        clientes = cargar_clientes()
        texto = busqueda.get().strip().lower()

        for cliente in clientes:
            identificador = str(cliente.get("id", ""))
            nombre = str(cliente.get("nombre", ""))
            deuda = float(cliente.get("deuda", 0))
            estado = cliente.get(
                "estado",
                "CON DEUDA" if deuda > 0 else "SIN DEUDA"
            )

            # Filtrar por ID o nombre
            if (
                texto
                and texto not in identificador.lower()
                and texto not in nombre.lower()
            ):
                continue

            tabla.insert(
                "",
                "end",
                values=(
                    identificador,
                    nombre,
                    formatear_pesos(deuda),
                    estado
                )
            )

    busqueda.trace_add("write", actualizar_tabla)
    actualizar_tabla()
    entrada.focus_set()



def mostrar_registrar_pago(ventana):
    pantalla = tk.Toplevel(ventana)
    pantalla.title("Registrar pago")
    pantalla.geometry("480x430")
    pantalla.resizable(False, False)
    pantalla.configure(bg=FONDO)

    tk.Label(
        pantalla,
        text="Registrar pago",
        font=("Segoe UI", 22, "bold"),
        bg=FONDO,
        fg=AZUL_OSCURO
    ).pack(anchor="w", padx=25, pady=(25, 5))

    tk.Label(
        pantalla,
        text="Seleccioná un cliente e ingresá el importe recibido.",
        font=("Segoe UI", 10),
        bg=FONDO,
        fg=GRIS
    ).pack(anchor="w", padx=25, pady=(0, 20))

    tk.Label(
        pantalla,
        text="Cliente",
        bg=FONDO,
        fg=AZUL_OSCURO
    ).pack(anchor="w", padx=25)

    clientes = cargar_clientes()
    clientes_con_deuda = [
        cliente for cliente in clientes
        if float(cliente.get("deuda", 0)) > 0
    ]

    opciones = {
        f"ID {cliente['id']} - {cliente['nombre']} "
        f"(Deuda: {formatear_pesos(float(cliente['deuda']))})": cliente
        for cliente in clientes_con_deuda
    }

    seleccion_cliente = tk.StringVar()
    combo_clientes = ttk.Combobox(
        pantalla,
        textvariable=seleccion_cliente,
        values=list(opciones.keys()),
        state="readonly",
        font=("Segoe UI", 10)
    )
    combo_clientes.pack(fill="x", padx=25, pady=(5, 15))

    etiqueta_deuda = tk.Label(
        pantalla,
        text="Deuda actual: —",
        font=("Segoe UI", 12, "bold"),
        bg=FONDO,
        fg=AZUL_OSCURO
    )
    etiqueta_deuda.pack(anchor="w", padx=25, pady=(0, 15))

    tk.Label(
        pantalla,
        text="Importe del pago",
        bg=FONDO,
        fg=AZUL_OSCURO
    ).pack(anchor="w", padx=25)

    entrada_importe = ttk.Entry(pantalla, font=("Segoe UI", 12))
    entrada_importe.pack(fill="x", padx=25, pady=(5, 20))

    def actualizar_deuda(event=None):
        cliente = opciones.get(seleccion_cliente.get())

        if cliente:
            etiqueta_deuda.config(
                text=f"Deuda actual: {formatear_pesos(float(cliente['deuda']))}"
            )
        else:
            etiqueta_deuda.config(text="Deuda actual: —")

    combo_clientes.bind("<<ComboboxSelected>>", actualizar_deuda)

    def guardar_pago():
        cliente = opciones.get(seleccion_cliente.get())

        if not cliente:
            messagebox.showwarning(
                "Seleccioná un cliente",
                "Elegí un cliente con deuda pendiente.",
                parent=pantalla
            )
            return

        texto_importe = entrada_importe.get().strip().replace(",", ".")

        try:
            importe = float(texto_importe)

            if importe <= 0 or not __import__("math").isfinite(importe):
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Importe inválido",
                "Ingresá un importe numérico mayor que cero.",
                parent=pantalla
            )
            return

        identificador = cliente["id"]

        try:
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            lista_clientes = (
                datos.get("clientes", [])
                if isinstance(datos, dict)
                else datos
            )

            cliente_actual = next(
                (
                    c for c in lista_clientes
                    if str(c.get("id")) == str(identificador)
                ),
                None
            )

            if cliente_actual is None:
                raise ValueError("El cliente ya no existe.")

            deuda_actual = float(cliente_actual.get("deuda", 0))

            if deuda_actual <= 0:
                raise ValueError("El cliente ya no tiene deuda pendiente.")

            if importe > deuda_actual:
                raise ValueError(
                    f"El pago supera la deuda actual de "
                    f"{formatear_pesos(deuda_actual)}."
                )

            nueva_deuda = round(deuda_actual - importe, 2)

            cliente_actual["deuda"] = nueva_deuda
            cliente_actual["estado"] = (
                "SIN DEUDA" if nueva_deuda == 0 else "CON DEUDA"
            )

            cliente_actual.setdefault("pagos", []).append({
                "monto": importe,
                "fecha": __import__("datetime").datetime.now().strftime("%Y-%m-%d")
            })

            archivo_temporal = None


            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=str(ARCHIVO_DATOS.parent),
                    delete=False
                ) as archivo:
                    archivo_temporal = archivo.name
                    json.dump(datos, archivo, indent=4, ensure_ascii=False)

                # Crear respaldo antes de modificar los datos
                crear_copia_seguridad()

                # Guardar los datos actualizados
                os.replace(archivo_temporal, ARCHIVO_DATOS)
                archivo_temporal = None


            finally:
                if archivo_temporal and os.path.exists(archivo_temporal):
                    os.remove(archivo_temporal)

        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            messagebox.showerror(
                "No se pudo registrar el pago",
                str(error),
                parent=pantalla
            )
            return

        messagebox.showinfo(
            "Pago registrado",
            f"Cliente: {cliente_actual['nombre']}\n"
            f"Pago: {formatear_pesos(importe)}\n"
            f"Deuda restante: {formatear_pesos(nueva_deuda)}",
            parent=pantalla
        )

        pantalla.destroy()

    tk.Button(
        pantalla,
        text="Guardar pago",
        command=guardar_pago,
        bg=AZUL,
        fg=BLANCO,
        activebackground=AZUL_OSCURO,
        activeforeground=BLANCO,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 11, "bold"),
        padx=18,
        pady=9
    ).pack(anchor="e", padx=25, pady=(0, 20))

    if combo_clientes["values"]:
        combo_clientes.current(0)
        actualizar_deuda()
    else:
        combo_clientes.configure(state="disabled")
        entrada_importe.configure(state="disabled")
        messagebox.showinfo(
            "Sin deudas pendientes",
            "No hay clientes con deuda pendiente para registrar pagos.",
            parent=pantalla
        )

    entrada_importe.focus_set()



def mostrar_historial_pagos(ventana):
    pantalla = tk.Toplevel(ventana)
    pantalla.title("Historial de pagos")
    pantalla.geometry("750x480")
    pantalla.minsize(650, 400)
    pantalla.configure(bg=FONDO)

    tk.Label(
        pantalla,
        text="Historial de pagos",
        font=("Segoe UI", 18, "bold"),
        bg=FONDO,
        fg="#263238"
    ).pack(anchor="w", padx=20, pady=(20, 10))

    clientes = cargar_clientes()
    print("CLIENTES CARGADOS:", clientes)

    if not clientes:
        messagebox.showinfo(
            "Sin clientes",
            "Todavía no hay clientes registrados.",
            parent=pantalla
        )
        pantalla.destroy()
        return

    marco = tk.Frame(pantalla, bg=FONDO)
    marco.pack(fill="both", expand=True, padx=20, pady=10)

    tk.Label(
        marco,
        text="Seleccioná un cliente:",
        bg=FONDO,
        fg="#263238",
        font=("Segoe UI", 10)
    ).pack(anchor="w", pady=(0, 5))

    opciones = {
        f"ID {cliente['id']} - {cliente['nombre']}": cliente
        for cliente in clientes
    }

    seleccion = tk.StringVar()

    combo = ttk.Combobox(
        marco,
        textvariable=seleccion,
        values=list(opciones.keys()),
        state="readonly",
        font=("Segoe UI", 10)
    )
    combo.pack(fill="x", pady=(0, 15))


    resumen = tk.Label(
        marco,
        text="",
        bg=FONDO,
        fg="#263238",
        font=("Segoe UI", 10, "bold")
    )
    resumen.pack(anchor="w", pady=(0, 10))

    columnas = ("fecha", "monto")

    tabla = ttk.Treeview(
        marco,
        columns=columnas,
        show="headings",
        height=12
    )

    tabla.heading("fecha", text="Fecha")
    tabla.heading("monto", text="Monto del pago")

    tabla.column("fecha", width=180, anchor="center")
    tabla.column("monto", width=220, anchor="e")

    tabla.pack(fill="both", expand=True)



    def actualizar_historial(_event=None):
        for elemento in tabla.get_children():
            tabla.delete(elemento)

        cliente = opciones.get(seleccion.get())

        if not cliente:
            resumen.config(text="")
            return

        pagos = cliente.get("pagos", [])
        total_pagado = 0

        for pago in pagos:
            monto = float(pago.get("monto", 0))
            fecha = pago.get("fecha", "Sin fecha")
            total_pagado += monto

            tabla.insert(
                "",
                "end",
                values=(fecha, formatear_pesos(monto))
            )

        deuda_actual = float(cliente.get("deuda", 0) or 0)

        resumen.config(
            text=(
                f"Cantidad de pagos: {len(pagos)}   |   "
                f"Total pagado: {formatear_pesos(total_pagado)}   |   "
                f"Deuda actual: {formatear_pesos(deuda_actual)}"
            )
        )


    combo.bind("<<ComboboxSelected>>", actualizar_historial)

    if combo["values"]:
        combo.current(0)
        actualizar_historial()



def crear_copia_seguridad():
    # Verificar que exista el archivo original
    if not ARCHIVO_DATOS.exists():
        return None

    # Crear carpeta de respaldos
    carpeta_backups = ARCHIVO_DATOS.parent / "backups"
    carpeta_backups.mkdir(exist_ok=True)

    # Nombre único para cada copia
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    nombre_backup = f"clientes_{fecha}.json"
    ruta_backup = carpeta_backups / nombre_backup

    # Copiar el archivo sin modificar el original
    shutil.copy2(ARCHIVO_DATOS, ruta_backup)

    return ruta_backup


def restaurar_copia_seguridad(ventana):
    from tkinter import filedialog

    carpeta = ARCHIVO_DATOS.parent / "backups"

    if not carpeta.exists():
        messagebox.showwarning(
            "Sin respaldos",
            "Todavía no existen copias de seguridad.",
            parent=ventana
        )
        return

    ruta = filedialog.askopenfilename(
        parent=ventana,
        title="Seleccionar copia de seguridad",
        initialdir=str(carpeta),
        filetypes=[("Archivos JSON", "*.json")]
    )

    if not ruta:
        return

    # Comprobar que el respaldo sea válido
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if (
            not isinstance(datos, dict)
            or not isinstance(datos.get("clientes"), list)
            or not isinstance(datos.get("ultimo_id"), int)
        ):
            raise ValueError(
                "La copia no tiene el formato esperado."
            )

        for cliente in datos["clientes"]:
            if (
                not isinstance(cliente, dict)
                or "id" not in cliente
                or "nombre" not in cliente
                or "deuda" not in cliente
            ):
                raise ValueError(
                    "La copia contiene clientes inválidos."
                )

    except (OSError, ValueError, TypeError) as error:
        messagebox.showerror(
            "Respaldo inválido",
            f"No se pudo leer el respaldo:\n{error}",
            parent=ventana
        )
        return

    confirmar = messagebox.askyesno(
        "Confirmar restauración",
        "¿Querés restaurar esta copia de seguridad?\n\n"
        "Los datos actuales serán reemplazados.\n"
        "Antes se creará un respaldo de seguridad.",
        parent=ventana
    )

    if not confirmar:
        return

    ruta_temporal = None

    try:
        # Preparar los datos restaurados
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(ARCHIVO_DATOS.parent),
            suffix=".tmp",
            delete=False
        ) as archivo:
            ruta_temporal = archivo.name
            json.dump(
                datos,
                archivo,
                indent=4,
                ensure_ascii=False
            )
            archivo.flush()
            os.fsync(archivo.fileno())

        # Respaldar la información actual
        crear_copia_seguridad()

        # Restaurar la información seleccionada
        os.replace(ruta_temporal, ARCHIVO_DATOS)
        ruta_temporal = None

    except (OSError, ValueError, TypeError) as error:
        messagebox.showerror(
            "Error al restaurar",
            str(error),
            parent=ventana
        )
        return

    finally:
        if ruta_temporal and os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

    messagebox.showinfo(
        "Restauración completada",
        "Los datos se restauraron correctamente.",
        parent=ventana
    )




def mostrar_reportes(ventana):
    pantalla = tk.Toplevel(ventana)
    pantalla.title("Reportes de cobranzas")
    pantalla.geometry("800x550")
    pantalla.minsize(700, 450)
    pantalla.configure(bg=FONDO)

    tk.Label(
        pantalla,
        text="Reportes de cobranzas",
        font=("Segoe UI", 18, "bold"),
        bg=FONDO,
        fg="#263238"
    ).pack(anchor="w", padx=25, pady=(20, 10))

    clientes = cargar_clientes()

    total_recaudado = 0
    cantidad_pagos = 0
    clientes_con_pagos = 0
    deuda_pendiente = 0

    datos_tabla = []

    for cliente in clientes:
        pagos = cliente.get("pagos", [])
        total_cliente = 0

        for pago in pagos:
            monto = float(pago.get("monto", 0))
            total_cliente += monto
            total_recaudado += monto
            cantidad_pagos += 1

        if pagos:
            clientes_con_pagos += 1

        deuda_pendiente += float(cliente.get("deuda", 0) or 0)

        datos_tabla.append((
            cliente.get("nombre", "Sin nombre"),
            len(pagos),
            total_cliente,
            float(cliente.get("deuda", 0) or 0)
        ))

    marco_resumen = tk.Frame(pantalla, bg=FONDO)
    marco_resumen.pack(fill="x", padx=25, pady=15)

    def crear_indicador(titulo, valor):
        cuadro = tk.Frame(
            marco_resumen,
            bg="white",
            padx=12,
            pady=14
        )
        cuadro.pack(
            side="left",
            fill="both",
            expand=True,
            padx=4
        )

        tk.Label(
            cuadro,
            text=titulo,
            bg="white",
            fg="#555555",
            font=("Segoe UI", 9)
        ).pack()


        etiqueta_valor = tk.Label(
            cuadro,
            text=valor,
            bg="white",
            fg="#263238",
            font=("Segoe UI", 12, "bold")
        )
        etiqueta_valor.pack(pady=(6, 0))

        return etiqueta_valor



    indicador_recaudado = crear_indicador(
        "Total recaudado",
        formatear_pesos(total_recaudado)
    )

    indicador_pagos = crear_indicador(
        "Pagos registrados",
        str(cantidad_pagos)
    )

    indicador_clientes = crear_indicador(
        "Clientes que pagaron",
        str(clientes_con_pagos)
    )

    crear_indicador(
        "Deuda pendiente",
        formatear_pesos(deuda_pendiente)
    )



    # Filtro de cobranzas por fechas
    marco_fechas = tk.Frame(pantalla, bg=FONDO)
    marco_fechas.pack(fill="x", padx=25, pady=(5, 10))

    tk.Label(
        marco_fechas,
        text="Desde:",
        bg=FONDO,
        fg="#263238",
        font=("Segoe UI", 10)
    ).pack(side="left", padx=(0, 5))

    entrada_desde = tk.Entry(
        marco_fechas,
        font=("Segoe UI", 10),
        width=12
    )
    entrada_desde.pack(side="left", padx=(0, 15))
    entrada_desde.insert(0, "2026-10-01")

    tk.Label(
        marco_fechas,
        text="Hasta:",
        bg=FONDO,
        fg="#263238",
        font=("Segoe UI", 10)
    ).pack(side="left", padx=(0, 5))

    entrada_hasta = tk.Entry(
        marco_fechas,
        font=("Segoe UI", 10),
        width=12
    )
    entrada_hasta.pack(side="left", padx=(0, 15))
    entrada_hasta.insert(0, "2026-10-31")


    tk.Label(
        pantalla,
        text="Resumen por cliente",
        font=("Segoe UI", 13, "bold"),
        bg=FONDO,
        fg="#263238"
    ).pack(anchor="w", padx=25, pady=(15, 10))

    marco_tabla = tk.Frame(pantalla)
    marco_tabla.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=(0, 20)
    )

    columnas = (
        "cliente",
        "pagos",
        "recaudado",
        "deuda"
    )

    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas,
        show="headings"
    )

    tabla.heading("cliente", text="Cliente")
    tabla.heading("pagos", text="Pagos")
    tabla.heading("recaudado", text="Total pagado")
    tabla.heading("deuda", text="Deuda actual")

    tabla.column("cliente", width=200)
    tabla.column("pagos", width=80, anchor="center")
    tabla.column("recaudado", width=150, anchor="e")
    tabla.column("deuda", width=150, anchor="e")

    barra = ttk.Scrollbar(
        marco_tabla,
        orient="vertical",
        command=tabla.yview
    )

    tabla.configure(yscrollcommand=barra.set)

    tabla.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")

    for nombre, pagos, recaudado, deuda in datos_tabla:
        tabla.insert(
            "",
            "end",
            values=(
                nombre,
                pagos,
                formatear_pesos(recaudado),
                formatear_pesos(deuda)
            )
        )


    # Resumen del período seleccionado
    resumen_periodo = tk.Label(
        marco_resumen,
        text="",
        bg=FONDO,
        fg="#263238",
        font=("Segoe UI", 10, "bold")
    )
    resumen_periodo.pack(fill="x", pady=(12, 0))

    def filtrar_reportes():
        from datetime import datetime

        desde = entrada_desde.get().strip()
        hasta = entrada_hasta.get().strip()

        try:
            fecha_desde = datetime.strptime(
                desde, "%Y-%m-%d"
            ).date()

            fecha_hasta = datetime.strptime(
                hasta, "%Y-%m-%d"
            ).date()

        except ValueError:
            messagebox.showerror(
                "Fechas incorrectas",
                "Ingresá las fechas con el formato AAAA-MM-DD.",
                parent=pantalla
            )
            return

        if fecha_desde > fecha_hasta:
            messagebox.showwarning(
                "Fechas incorrectas",
                "La fecha Desde no puede ser posterior a Hasta.",
                parent=pantalla
            )
            return

        for elemento in tabla.get_children():
            tabla.delete(elemento)

        total_periodo = 0
        cantidad_pagos_periodo = 0
        clientes_periodo = 0

        for cliente in cargar_clientes():
            pagos_filtrados = []

            for pago in cliente.get("pagos", []):
                try:
                    fecha_pago = datetime.strptime(
                        pago.get("fecha", ""),
                        "%Y-%m-%d"
                    ).date()

                    if fecha_desde <= fecha_pago <= fecha_hasta:
                        monto = float(pago.get("monto", 0))
                        pagos_filtrados.append(monto)

                except (ValueError, TypeError):
                    continue

            if pagos_filtrados:
                total_cliente = sum(pagos_filtrados)

                total_periodo += total_cliente
                cantidad_pagos_periodo += len(pagos_filtrados)
                clientes_periodo += 1

                tabla.insert(
                    "",
                    "end",
                    values=(
                        cliente.get("nombre", "Sin nombre"),
                        len(pagos_filtrados),
                        formatear_pesos(total_cliente),
                        formatear_pesos(
                            float(cliente.get("deuda", 0) or 0)
                        )
                    )
                )



        indicador_recaudado.config(
            text=formatear_pesos(total_periodo)
        )

        indicador_pagos.config(
            text=str(cantidad_pagos_periodo)
        )

        indicador_clientes.config(
            text=str(clientes_periodo)
        )


        resumen_periodo.config(
            text=(
                f"Período: {desde} al {hasta}  |  "
                f"Recaudado: {formatear_pesos(total_periodo)}  |  "
                f"Pagos: {cantidad_pagos_periodo}  |  "
                f"Clientes: {clientes_periodo}"
            )
        )

    tk.Button(
        marco_fechas,
        text="Filtrar",
        command=filtrar_reportes,
        bg=AZUL,
        fg=BLANCO,
        activebackground=AZUL_OSCURO,
        activeforeground=BLANCO,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        padx=15,
        pady=5
    ).pack(side="left")

    def limpiar_filtros():
        # Vaciar los campos de fechas
        entrada_desde.delete(0, tk.END)
        entrada_hasta.delete(0, tk.END)

        # Restaurar indicadores generales
        indicador_recaudado.config(
            text=formatear_pesos(total_recaudado)
        )

        indicador_pagos.config(
            text=str(cantidad_pagos)
        )

        indicador_clientes.config(
            text=str(clientes_con_pagos)
        )

        # Limpiar la tabla
        for elemento in tabla.get_children():
            tabla.delete(elemento)

        # Restaurar todos los clientes
        for nombre, pagos, recaudado, deuda in datos_tabla:
            tabla.insert(
                "",
                "end",
                values=(
                    nombre,
                    pagos,
                    formatear_pesos(recaudado),
                    formatear_pesos(deuda)
                )
            )

        # Quitar el resumen del filtro
        resumen_periodo.config(text="")

    # Botón para limpiar filtros
    tk.Button(
        marco_fechas,
        text="Limpiar filtros",
        command=limpiar_filtros,
        bg="#607D8B",
        fg=BLANCO,
        activebackground="#455A64",
        activeforeground=BLANCO,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        padx=15,
        pady=5
    ).pack(side="left", padx=(10, 0))


    def exportar_excel():
        from tkinter import filedialog
        from datetime import datetime
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        # Obtener los datos visibles de la tabla
        filas = [
            tabla.item(item, "values")
            for item in tabla.get_children()
        ]

        if not filas:
            messagebox.showwarning(
                "Sin datos",
                "No hay resultados para exportar.",
                parent=pantalla
            )
            return

        # Convertir montos formateados a números
        def convertir_monto(valor):
            texto = str(valor)
            texto = texto.replace("$", "").replace("ARS", "")
            texto = texto.replace(" ", "").replace("\xa0", "")

            if "," in texto:
                texto = texto.replace(".", "").replace(",", ".")
            elif "." in texto and len(texto.split(".")[-1]) == 3:
                texto = texto.replace(".", "")

            return float(texto)

        # Seleccionar dónde guardar el archivo
        nombre_archivo = (
            "reporte_cobranzas_"
            + datetime.now().strftime("%Y%m%d_%H%M")
            + ".xlsx"
        )

        ruta = filedialog.asksaveasfilename(
            parent=pantalla,
            title="Guardar reporte de cobranzas",
            defaultextension=".xlsx",
            initialfile=nombre_archivo,
            filetypes=[("Archivos Excel", "*.xlsx")]
        )

        if not ruta:
            return

        try:
            libro = Workbook()
            hoja = libro.active
            hoja.title = "Cobranzas"

            # Título
            hoja.merge_cells("A1:D1")
            hoja["A1"] = "REPORTE DE COBRANZAS"
            hoja["A1"].font = Font(
                size=16,
                bold=True,
                color="FFFFFF"
            )
            hoja["A1"].fill = PatternFill(
                "solid",
                fgColor="1565C0"
            )
            hoja["A1"].alignment = Alignment(
                horizontal="center"
            )
            hoja.row_dimensions[1].height = 32

            # Período del reporte
            hoja.merge_cells("A2:D2")
            hoja["A2"] = (
                resumen_periodo.cget("text")
                or "Reporte general - Sin filtro"
            )

            # Encabezados
            encabezados = [
                "Cliente",
                "Pagos",
                "Total pagado",
                "Deuda actual"
            ]

            hoja.append(encabezados)

            for celda in hoja[3]:
                celda.font = Font(
                    bold=True,
                    color="FFFFFF"
                )
                celda.fill = PatternFill(
                    "solid",
                    fgColor="263238"
                )
                celda.alignment = Alignment(
                    horizontal="center"
                )

            # Datos
            for nombre, pagos, recaudado, deuda in filas:
                nombre = str(nombre)

                if nombre.startswith(("=", "+", "-", "@")):
                    nombre = "'" + nombre

                hoja.append([
                    nombre,
                    int(pagos),
                    convertir_monto(recaudado),
                    convertir_monto(deuda)
                ])


            # Fila de totales automáticos
            fila_total = hoja.max_row + 1

            hoja.cell(
                row=fila_total,
                column=1,
                value="TOTALES"
            )

            for columna in (2, 3, 4):
                letra = hoja.cell(
                    row=3, column=columna
                ).column_letter

                hoja.cell(
                    row=fila_total,
                    column=columna,
                    value=f"=SUM({letra}4:{letra}{fila_total - 1})"
                )

            for celda in hoja[fila_total]:
                celda.font = Font(
                    bold=True,
                    color="FFFFFF"
                )
                celda.fill = PatternFill(
                    "solid",
                    fgColor="1565C0"
                )


            # Formato de importes
            for fila in hoja.iter_rows(
                min_row=4,
                min_col=3,
                max_col=4
            ):
                for celda in fila:
                    celda.number_format = '"$" #,##0.00'

            # Ancho de las columnas
            hoja.column_dimensions["A"].width = 28
            hoja.column_dimensions["B"].width = 15
            hoja.column_dimensions["C"].width = 22
            hoja.column_dimensions["D"].width = 22

            # Filtros y encabezados fijos
            hoja.freeze_panes = "A4"
            hoja.auto_filter.ref = f"A3:D{fila_total - 1}"

            libro.save(ruta)

        except (OSError, ValueError, TypeError) as error:
            messagebox.showerror(
                "Error al exportar",
                f"No se pudo crear el archivo:\n{error}",
                parent=pantalla
            )
            return

        messagebox.showinfo(
            "Exportación completada",
            "El reporte de Excel se guardó correctamente.",
            parent=pantalla
        )

    # Botón Exportar a Excel
    tk.Button(
        marco_fechas,
        text="Exportar Excel",
        command=exportar_excel,
        bg="#2E7D32",
        fg=BLANCO,
        activebackground="#1B5E20",
        activeforeground=BLANCO,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 10, "bold"),
        padx=12,
        pady=5
    ).pack(side="left", padx=(10, 0))







def crear_aplicacion():
    ventana = tk.Tk()
    ventana.title("Sistema de Cobranzas")
    ventana.geometry("1100x680")
    ventana.minsize(900, 550)
    ventana.configure(bg=FONDO)

    # Cargar los datos
    clientes = cargar_clientes()

    # Calcular el resumen
    total_clientes = len(clientes)
    clientes_con_deuda = sum(
        1 for cliente in clientes
        if float(cliente.get("deuda", 0)) > 0
    )
    deuda_pendiente = sum(
        float(cliente.get("deuda", 0))
        for cliente in clientes
    )

    # Menú lateral
    menu = tk.Frame(ventana, bg=AZUL_OSCURO, width=220)
    menu.pack(side="left", fill="y")
    menu.pack_propagate(False)

    tk.Label(
        menu,
        text="SISTEMA\nDE COBRANZAS",
        font=("Segoe UI", 17, "bold"),
        bg=AZUL_OSCURO,
        fg=BLANCO,
        justify="left"
    ).pack(anchor="w", padx=22, pady=(30, 40))



    def abrir_opcion(opcion):
        if opcion == "Clientes":
            mostrar_clientes(ventana)
        elif opcion == "Registrar pago":
            mostrar_registrar_pago(ventana)
        elif opcion == "Historial":
            mostrar_historial_pagos(ventana)
        elif opcion == "Reportes":
            mostrar_reportes(ventana)
        elif opcion == "Restaurar respaldo":
            restaurar_copia_seguridad(ventana)
        else:
            messagebox.showinfo(
                "En desarrollo",
                f"La opción '{opcion}' todavía está en desarrollo."
            )






    for opcion in [
        "Inicio",
        "Clientes",
        "Registrar pago",
        "Historial",
        "Reportes",
        "Restaurar respaldo"
    ]:

        boton = tk.Button(
            menu,
            text=opcion,
            font=("Segoe UI", 11),
            bg=AZUL_OSCURO,
            fg=BLANCO,
            activebackground=AZUL,
            activeforeground=BLANCO,
            relief="flat",
            anchor="w",
            padx=20,
            pady=12,
            cursor="hand2",
            bd=0,
            command=lambda op=opcion: abrir_opcion(op)
        )

        boton.pack(fill="x", padx=10, pady=3)

        boton.bind(
            "<Enter>",
            lambda _evento, b=boton: b.config(bg=AZUL)
        )

        boton.bind(
            "<Leave>",
            lambda _evento, b=boton: b.config(bg=AZUL_OSCURO)
        )



    # Área principal
    contenido = tk.Frame(ventana, bg=FONDO)
    contenido.pack(
        side="left",
        fill="both",
        expand=True,
        padx=30,
        pady=25
    )

    tk.Label(
        contenido,
        text="Panel de control",
        font=("Segoe UI", 24, "bold"),
        bg=FONDO,
        fg=AZUL_OSCURO
    ).pack(anchor="w")

    tk.Label(
        contenido,
        text="Resumen general de cobranzas",
        font=("Segoe UI", 11),
        bg=FONDO,
        fg=GRIS
    ).pack(anchor="w", pady=(4, 22))

    # Tarjetas con datos reales
    tarjetas = tk.Frame(contenido, bg=FONDO)
    tarjetas.pack(fill="x", pady=(0, 25))

    resumen = [
        ("Total de clientes", str(total_clientes)),
        ("Clientes con deuda", str(clientes_con_deuda)),
        ("Deuda pendiente", formatear_pesos(deuda_pendiente))
    ]


    etiquetas_resumen = {}

    # Colores para cada indicador
    colores_tarjetas = {
        "Total de clientes": "#2563EB",
        "Clientes con deuda": "#D97706",
        "Deuda pendiente": "#DC2626"
    }

    for titulo, valor in resumen:
        color = colores_tarjetas.get(
            titulo, AZUL_OSCURO
        )

        # Tarjeta principal
        tarjeta = tk.Frame(
            tarjetas,
            bg=BLANCO,
            highlightbackground="#E2E8F0",
            highlightthickness=1,
            padx=14,
            pady=16
        )

        tarjeta.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 12)
        )

        # Barra de color lateral
        barra_color = tk.Frame(
            tarjeta,
            bg=color,
            width=5
        )

        barra_color.pack(
            side="left",
            fill="y",
            padx=(0, 14)
        )

        # Contenido de la tarjeta
        contenido_tarjeta = tk.Frame(
            tarjeta,
            bg=BLANCO
        )

        contenido_tarjeta.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Nombre del indicador
        tk.Label(
            contenido_tarjeta,
            text=titulo,
            font=("Segoe UI", 10),
            bg=BLANCO,
            fg=GRIS
        ).pack(anchor="w")

        # Valor del indicador
        etiqueta_valor = tk.Label(
            contenido_tarjeta,
            text=valor,
            font=("Segoe UI", 20, "bold"),
            bg=BLANCO,
            fg=color
        )

        etiqueta_valor.pack(
            anchor="w",
            pady=(10, 0)
        )

        # Mantener actualización automática
        etiquetas_resumen[titulo] = etiqueta_valor


    # Tabla de clientes
    tk.Label(
        contenido,
        text="Clientes recientes",
        font=("Segoe UI", 15, "bold"),
        bg=FONDO,
        fg=AZUL_OSCURO
    ).pack(anchor="w", pady=(0, 12))

    tabla_frame = tk.Frame(contenido, bg=BLANCO)
    tabla_frame.pack(fill="both", expand=True)

    columnas = ("id", "nombre", "deuda", "estado")

    tabla = ttk.Treeview(
        tabla_frame,
        columns=columnas,
        show="headings"
    )

    tabla.heading("id", text="ID")
    tabla.heading("nombre", text="Nombre")
    tabla.heading("deuda", text="Deuda")
    tabla.heading("estado", text="Estado")

    tabla.column("id", width=60, anchor="center")
    tabla.column("nombre", width=250)
    tabla.column("deuda", width=150, anchor="e")
    tabla.column("estado", width=150, anchor="center")


    # Mostrar los clientes guardados
    for indice, cliente in enumerate(clientes):
        deuda = float(cliente.get("deuda", 0))

        estado = (
            "CON DEUDA" if deuda > 0 else "SIN DEUDA"
        )

        tipo = "con_deuda" if deuda > 0 else "sin_deuda"
        alternancia = "par" if indice % 2 == 0 else "impar"
        etiqueta = f"{tipo}_{alternancia}"

        tabla.insert(
            "",
            "end",
            values=(
                cliente.get("id", ""),
                cliente.get("nombre", ""),
                formatear_pesos(deuda),
                estado
            ),
            tags=(etiqueta,)
        )


    tabla.pack(fill="both", expand=True, padx=12, pady=12)

    estilo = ttk.Style()
    estilo.configure(
        "Treeview",
        font=("Segoe UI", 10),
        rowheight=32
    )
    estilo.configure(
        "Treeview.Heading",
        font=("Segoe UI", 10, "bold")
    )
    # Colores de las filas según el estado del cliente
    tabla.tag_configure(
        "con_deuda_par",
        background="#FFF1F2",
        foreground="#9F1239"
    )

    tabla.tag_configure(
        "con_deuda_impar",
        background="#FFE4E6",
        foreground="#9F1239"
    )

    tabla.tag_configure(
        "sin_deuda_par",
        background="#F0FDF4",
        foreground="#166534"
    )

    tabla.tag_configure(
        "sin_deuda_impar",
        background="#DCFCE7",
        foreground="#166534"
    )


    def actualizar_panel():
        clientes_actualizados = cargar_clientes()

        total = len(clientes_actualizados)

        con_deuda = sum(
            1 for cliente in clientes_actualizados
            if float(cliente.get("deuda", 0)) > 0
        )

        deuda_total = sum(
            float(cliente.get("deuda", 0))
            for cliente in clientes_actualizados
        )

        etiquetas_resumen["Total de clientes"].config(
            text=str(total)
        )

        etiquetas_resumen["Clientes con deuda"].config(
            text=str(con_deuda)
        )
        etiquetas_resumen["Deuda pendiente"].config(
            text=formatear_pesos(deuda_total)
        )
        for elemento in tabla.get_children():
            tabla.delete(elemento)
        for indice, cliente in enumerate(clientes_actualizados):
            deuda = float(cliente.get("deuda", 0))

            estado = (
                "CON DEUDA" if deuda > 0 else "SIN DEUDA"
            )

            tipo = "con_deuda" if deuda > 0 else "sin_deuda"
            alternancia = "par" if indice % 2 == 0 else "impar"
            etiqueta = f"{tipo}_{alternancia}"

            tabla.insert(
                "",
                "end",
                values=(
                    cliente.get("id", ""),
                    cliente.get("nombre", ""),
                    formatear_pesos(deuda),
                    estado
                ),
                tags=(etiqueta,)
            )


    # Actualizar automáticamente cada 2 segundos
    def revisar_cambios():
        actualizar_panel()
        ventana.after(2000, revisar_cambios)

    ventana.after(2000, revisar_cambios)


    ventana.mainloop()

if __name__ == "__main__":
    crear_aplicacion()