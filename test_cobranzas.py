
import unittest
from unittest import mock
from io import StringIO
from contextlib import redirect_stdout
import json

from main import (mostrar_resumen, registrar_pago, editar_cliente, guardar_datos, cargar_clientes)



class TestSistemaCobranzas(unittest.TestCase):

    def test_resumen_de_cobranzas(self):
        clientes_falsos = [
            {"nombre": "Ana", "deuda": 100.0},
            {"nombre": "Luis", "deuda": 0.0},
            {"nombre": "Pedro", "deuda": 50.0}
        ]

        salida = StringIO()

        with redirect_stdout(salida):
            mostrar_resumen(clientes_falsos)

        resultado = salida.getvalue()

        self.assertIn("Total de clientes: 3", resultado)
        self.assertIn("Clientes con deuda: 2", resultado)
        self.assertIn("Clientes sin deudas: 1", resultado)
        self.assertIn("150,00", resultado)


    def test_resumen_sin_clientes(self):
        clientes_falsos = []

        salida = StringIO()

        with redirect_stdout(salida):
            mostrar_resumen(clientes_falsos)

        resultado = salida.getvalue()

        self.assertIn("Total de clientes: 0", resultado)
        self.assertIn("Clientes con deuda: 0", resultado)
        self.assertIn("Clientes sin deudas: 0", resultado)
        self.assertIn("0,00", resultado)


        
    def test_registrar_pago(self):
        datos_falsos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 75.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["1", "25"]
        ), mock.patch("builtins.print"), \
            mock.patch("main.guardar_datos") as guardar:

            registrar_pago(datos_falsos)

        cliente = datos_falsos["clientes"][0]

        self.assertEqual(cliente["deuda"], 50.0)
        self.assertEqual(cliente["estado"], "CON DEUDA")
        self.assertEqual(len(cliente["pagos"]), 1)
        self.assertEqual(cliente["pagos"][0]["monto"], 25.0)

        guardar.assert_called_once_with(datos_falsos)



    
    def test_rechazar_pago_mayor_que_deuda(self):
        datos_falsos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 75.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["1", "100", "25"]
        ), mock.patch("builtins.print"), \
             mock.patch("main.guardar_datos"), \
             mock.patch("main.datetime") as fecha_falsa:

            fecha_falsa.now.return_value.strftime.return_value = "2026-10-19"
            registrar_pago(datos_falsos)

        cliente = datos_falsos["clientes"][0]

        self.assertEqual(cliente["deuda"], 50.0)
        self.assertEqual(cliente["estado"], "CON DEUDA")
        self.assertEqual(len(cliente["pagos"]), 1)
        self.assertEqual(cliente["pagos"][0]["monto"], 25.0)


    def test_rechazar_pagos_invalidos(self):
        datos_falsos ={
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 75.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["1", "0", "-10", "25"]
        ), mock.patch("builtins.print"), \
            mock.patch("main.guardar_datos"), \
            mock.patch("main.datetime") as fecha_falsa:

            fecha_falsa.now.return_value.strftime.return_value = "2026-10-19"
            registrar_pago(datos_falsos)

        cliente = datos_falsos["clientes"][0]


        self.assertEqual(cliente["deuda"], 50.0)
        self.assertEqual(cliente["estado"], "CON DEUDA")
        self.assertEqual(len(cliente["pagos"]), 1)
        self.assertEqual(cliente["pagos"][0]["monto"], 25.0)



    
    def test_rechazar_pago_con_letras(self):
        datos_falsos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 75.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["1", "abc", "25"]
        ), mock.patch("builtins.print") as imprimir, \
            mock.patch("main.guardar_datos"), \
            mock.patch("main.datetime") as fecha_falsa:

            fecha_falsa.now.return_value.strftime.return_value = "2026-10-19"
            registrar_pago(datos_falsos)

        cliente = datos_falsos["clientes"][0]

        self.assertEqual(cliente["deuda"], 50.0)
        self.assertEqual(cliente["estado"], "CON DEUDA")
        self.assertEqual(len(cliente["pagos"]), 1)
        self.assertEqual(cliente["pagos"][0]["monto"], 25.0)

        imprimir.assert_any_call(
            "ERROR: Por favor, ingrese un número válido para el pago."
        )


    
    def test_editar_nombre_cliente(self):
        datos_falsos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 75.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["1", "1", "ana nueva"]
        ), mock.patch("builtins.print"), \
             mock.patch("main.guardar_datos"), \
             mock.patch("main.datetime") as fecha_falsa:

            fecha_falsa.now.return_value.strftime.return_value = "2026-10-19"
            editar_cliente(datos_falsos)

        cliente = datos_falsos["clientes"][0]

        self.assertEqual(cliente["nombre"], "ana nueva")
        self.assertEqual(len(cliente["modificaciones"]), 1)
        self.assertEqual(
            cliente["modificaciones"][0]["nombre_anterior"], "ana"
        )
        self.assertEqual(
            cliente["modificaciones"][0]["nombre_nuevo"], "ana nueva"
        )


    
    def test_editar_deuda_cliente(self):
        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 75.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        cliente = datos["clientes"][0]

        with mock.patch(
            "builtins.input",
            side_effect=["1", "2", "120"]
        ), mock.patch("builtins.print"), mock.patch(
            "main.guardar_datos"
        ), mock.patch(
            "main.datetime"
        ) as fecha_falsa:

            fecha_falsa.now.return_value.strftime.return_value = "2026-10-19"

            editar_cliente(datos)

        # Verificar que la deuda se haya actualizado
        self.assertEqual(cliente["deuda"], 120.0)

        # Verificar que el estado siga siendo CON DEUDA
        self.assertEqual(cliente["estado"], "CON DEUDA")

        # Verificar que se haya registrado la modificación
        self.assertEqual(len(cliente["modificaciones"]), 1)

        modificacion = cliente["modificaciones"][0]

        self.assertEqual(modificacion["tipo"], "deuda")
        self.assertEqual(modificacion["deuda_anterior"], 75.0)
        self.assertEqual(modificacion["deuda_nueva"], 120.0)


    
    def test_editar_deuda_a_cero(self):
        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 75.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        cliente = datos["clientes"][0]

        with mock.patch(
            "builtins.input",
            side_effect=["1", "2", "0"]
        ), mock.patch("builtins.print"), mock.patch(
            "main.guardar_datos"
        ), mock.patch(
            "main.datetime"
        ) as fecha_falsa:

            fecha_falsa.now.return_value.strftime.return_value = "2026-10-19"

            editar_cliente(datos)

        self.assertEqual(cliente["deuda"], 0.0)
        self.assertEqual(cliente["estado"], "SIN DEUDA")
        self.assertEqual(len(cliente["modificaciones"]), 1)
        self.assertEqual(
            cliente["modificaciones"][0]["deuda_anterior"],
            75.0
        )
        self.assertEqual(
            cliente["modificaciones"][0]["deuda_nueva"],
            0.0
        )

    
    
    def test_guardar_datos(self):
        import json
        import os
        import tempfile
        from unittest import mock
        from main import guardar_datos

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 100.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with tempfile.TemporaryDirectory() as carpeta:
            ruta_original = os.getcwd()

            try:
                os.chdir(carpeta)

                with open("clientes.json", "w", encoding="utf-8") as archivo:
                    json.dump({"clientes": []}, archivo)

                guardar_datos(datos)

                with open("clientes.json", "r", encoding="utf-8") as archivo:
                    datos_guardados = json.load(archivo)

                self.assertEqual(datos_guardados, datos)
                self.assertFalse(os.path.exists("clientes.json.tmp"))

            finally:
                os.chdir(ruta_original)




    
    def test_cargar_clientes(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos_esperados = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 100.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos_esperados)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            datos_cargados = cargar_clientes()

        self.assertEqual(datos_cargados, datos_esperados)



    
    def test_cargar_clientes_sin_archivo(self):
        from unittest import mock
        from main import cargar_clientes

        with mock.patch(
            "builtins.open",
            side_effect=FileNotFoundError
        ):
            datos = cargar_clientes()

        self.assertEqual(datos["ultimo_id"], 0)
        self.assertEqual(datos["clientes"], [])



    
    def test_cargar_clientes_json_danado(self):
        from unittest import mock
        from main import cargar_clientes

        contenido_danado = '{"ultimo_id": 1, "clientes": ['

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_danado)
        ), mock.patch("builtins.print") as imprimir:

            with self.assertRaises(json.JSONDecodeError):
                cargar_clientes()

        imprimir.assert_any_call(
            "ERROR: El archivo clientes.json está dañado."
        )
        imprimir.assert_any_call(
            "No se cargarán datos vacíos para evitar perder información."
        )



    
    def test_cargar_clientes_ids_duplicados(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 2,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 100.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                },
                {
                    "id": 1,
                    "nombre": "pedro",
                    "deuda": 50.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Hay clientes con IDs duplicados."
            ):
                cargar_clientes()



    
    def test_cargar_clientes_deuda_negativa(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": -100.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Hay un cliente con una deuda inválida."
            ):
                cargar_clientes()


    
    def test_cargar_clientes_nombre_vacio(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "   ",
                    "deuda": 100.0,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Hay un cliente con un nombre inválido."
            ):
                cargar_clientes()



    
    def test_cargar_clientes_estado_incorrecto(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 100.0,
                    "estado": "SIN DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "El estado de un cliente no coincide con su deuda."
            ):
                cargar_clientes()



    
    def test_cargar_clientes_formato_viejo(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        clientes_antiguos = [
            
            {
                "id": 3,
                "nombre": "ana",
                "deuda": 100.0,
                "estado": "CON DEUDA"
            },

            {
                "id": 7,
                "nombre": "pedro",
                "deuda": 0.0,
                "estado": "SIN DEUDA",
                "pagos": [],
                "modificaciones": []
            }
        ]

        contenido_json = json.dumps(clientes_antiguos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ), mock.patch("main.guardar_datos") as guardar:

            datos = cargar_clientes()

        self.assertEqual(datos["ultimo_id"], 7)
        self.assertEqual(len(datos["clientes"]), 2)
        self.assertEqual(datos["clientes"][0]["nombre"], "ana")
        self.assertEqual(datos["clientes"][1]["nombre"], "pedro")

        guardar.assert_called_once_with(datos)


    
    def test_cargar_cliente_sin_modificaciones(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 100.0,
                    "estado": "CON DEUDA",
                    "pagos": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ), mock.patch("main.guardar_datos") as guardar:

            datos_cargados = cargar_clientes()

        cliente = datos_cargados["clientes"][0]

        self.assertEqual(cliente["modificaciones"], [])
        self.assertEqual(cliente["nombre"], "ana")
        self.assertEqual(cliente["deuda"], 100.0)

        guardar.assert_called_once_with(datos_cargados)



    
    def test_cargar_cliente_sin_pagos(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 100.0,
                    "estado": "CON DEUDA",
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ), mock.patch("main.guardar_datos") as guardar:

            datos_cargados = cargar_clientes()

        cliente = datos_cargados["clientes"][0]

        self.assertEqual(cliente["pagos"], [])
        self.assertEqual(cliente["nombre"], "ana")
        self.assertEqual(cliente["deuda"], 100.0)

        guardar.assert_called_once_with(datos_cargados)



    
    def test_cargar_clientes_estructura_incorrecta(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        contenido_json = json.dumps("hola")

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "El archivo JSON tiene una estructura incorrecta."
            ):
                cargar_clientes()



    
    def test_cargar_clientes_sin_ultimo_id(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "clientes": []
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Faltan datos obligatorios en el archivo JSON."
            ):
                cargar_clientes()



    
    def test_cargar_clientes_sin_lista_clientes(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 5
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Faltan datos obligatorios en el archivo JSON."
            ):
                cargar_clientes()



    
    def test_cargar_clientes_lista_incorrecta(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 1,
            "clientes": "ana"
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "La lista de clientes tiene un formato incorrecto."
            ):
                cargar_clientes()



    
    def test_cargar_clientes_ultimo_id_booleano(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": True,
            "clientes": []
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            
            with self.assertRaisesRegex(
                ValueError,
                "El último ID tiene un formato incorrecto."
            ):

                cargar_clientes()


    
    def test_cargar_cliente_sin_id(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 5,
            "clientes": [
                {
                    "nombre": "ana",
                    "deuda": 100,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with mock.patch("main.guardar_datos") as guardar:
                resultado = cargar_clientes()

        self.assertEqual(resultado["clientes"][0]["id"], 6)
        self.assertEqual(resultado["ultimo_id"], 6)
        guardar.assert_called_once_with(resultado)



    
    def test_cargar_cliente_sin_id_evitar_duplicados(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 5,
            "clientes": [
                {
                    "id": 8,
                    "nombre": "ana",
                    "deuda": 100,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                },
                {
                    "nombre": "juan",
                    "deuda": 200,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with mock.patch("main.guardar_datos") as guardar:
                resultado = cargar_clientes()

        ids = [cliente["id"] for cliente in resultado["clientes"]]

        
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(isinstance(id_cliente, int) and not isinstance(id_cliente, bool) and id_cliente > 0 for id_cliente in ids))
        self.assertEqual(resultado["ultimo_id"], max(ids))
        guardar.assert_called_once_with(resultado)



    
    def test_cargar_clientes_actualizar_ultimo_id(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 5,
            "clientes": [
                {
                    "id": 8,
                    "nombre": "ana",
                    "deuda": 100,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with mock.patch("main.guardar_datos") as guardar:
                resultado = cargar_clientes()

        self.assertEqual(resultado["ultimo_id"], 8)
        guardar.assert_called_once_with(resultado)



    
    def test_cargar_clientes_historial_pagos_incorrecto(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 100,
                    "estado": "CON DEUDA",
                    "pagos": "sin pagos",
                    "modificaciones": []
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "El historial de pagos tiene un formato incorrecto."
            ):
                cargar_clientes()



    
    def test_cargar_clientes_historial_modificaciones_incorrecto(self):
        import json
        from unittest import mock
        from main import cargar_clientes

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 100,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": "sin modificaciones"
                }
            ]
        }

        contenido_json = json.dumps(datos)

        with mock.patch(
            "builtins.open",
            mock.mock_open(read_data=contenido_json)
        ):
            with self.assertRaisesRegex(
                ValueError,
                "El historial de modificaciones tiene un formato incorrecto."
            ):
                cargar_clientes()



    
    def test_registrar_pago_cancela_deuda_completa(self):
        from unittest import mock
        from main import registrar_pago

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 500,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["1", "500"]
        ):
            with mock.patch("main.guardar_datos") as guardar:
                registrar_pago(datos)

        cliente = datos["clientes"][0]

        self.assertEqual(cliente["deuda"], 0)
        self.assertEqual(cliente["estado"], "SIN DEUDA")
        self.assertEqual(len(cliente["pagos"]), 1)
        self.assertEqual(cliente["pagos"][0]["monto"], 500)
        guardar.assert_called_once_with(datos)



    
    def test_rechazar_pago_cliente_sin_deuda(self):
        from unittest import mock
        from main import registrar_pago

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 0,
                    "estado": "SIN DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["1"]
        ):
            with mock.patch("main.guardar_datos") as guardar:
                registrar_pago(datos)

        cliente = datos["clientes"][0]

        self.assertEqual(cliente["deuda"], 0)
        self.assertEqual(cliente["estado"], "SIN DEUDA")
        self.assertEqual(cliente["pagos"], [])
        guardar.assert_not_called()



    
    def test_rechazar_pago_cliente_inexistente(self):
        from unittest import mock
        from main import registrar_pago

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 500,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["99"]
        ):
            with mock.patch("main.guardar_datos") as guardar:
                registrar_pago(datos)

        self.assertEqual(datos["clientes"][0]["deuda"], 500)
        self.assertEqual(datos["clientes"][0]["pagos"], [])
        guardar.assert_not_called()



    
    def test_rechazar_deuda_negativa_al_editar(self):
        from unittest import mock
        from main import editar_cliente

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 500,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        
        with mock.patch(
            "builtins.input",
            side_effect=["1", "2", "-100", "500"]
        ):
            with mock.patch("main.guardar_datos") as guardar:
                editar_cliente(datos)


        cliente = datos["clientes"][0]

        self.assertEqual(cliente["deuda"], 500)
        self.assertEqual(cliente["estado"], "CON DEUDA")
        self.assertEqual(cliente["modificaciones"], [])
        guardar.assert_not_called()



    
    def test_rechazar_nombre_vacio_al_editar(self):
        from unittest import mock
        from main import editar_cliente

        datos = {
            "ultimo_id": 1,
            "clientes": [
                {
                    "id": 1,
                    "nombre": "ana",
                    "deuda": 500,
                    "estado": "CON DEUDA",
                    "pagos": [],
                    "modificaciones": []
                }
            ]
        }

        with mock.patch(
            "builtins.input",
            side_effect=["1", "1", "   ", "ana"]
        ):
            with mock.patch("main.guardar_datos") as guardar:
                editar_cliente(datos)

        cliente = datos["clientes"][0]

        self.assertEqual(cliente["nombre"], "ana")
        self.assertEqual(cliente["modificaciones"], [])
        guardar.assert_not_called()





if __name__ == "__main__":
    unittest.main()
