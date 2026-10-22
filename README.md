

# Sistema de Cobranzas en Python

Sistema de gestión de cobranzas desarrollado en Python, ejecutado desde la consola y con almacenamiento de datos en formato JSON.

## Funcionalidades

- Registro de clientes.
- Consulta y búsqueda de clientes.
- Edición de datos y deudas.
- Registro de pagos parciales y cancelación de deudas.
- Historial de pagos y modificaciones.
- Eliminación de clientes.
- Resumen general de cobranzas.
- Validación de datos ingresados.
- Persistencia de información mediante archivos JSON.
- Compatibilidad con una estructura de datos anterior.
- Pruebas automatizadas con `unittest`.

## Tecnologías utilizadas

- Python
- JSON
- `unittest` para pruebas automatizadas
- Git y GitHub (para control de versiones y publicación, una vez configurados)

## Requisitos

- Python 3 instalado.

## Instalación y ejecución

1. Descargar o clonar el repositorio.
2. Abrir una terminal en la carpeta del proyecto.
3. Ejecutar:

   ```bash
   python main.py
   ```

## Ejecutar las pruebas

Desde la carpeta del proyecto, ejecutar:

```bash
python -m unittest -v test_cobranzas.py
```

El proyecto cuenta actualmente con 35 pruebas automatizadas aprobadas en el entorno de desarrollo.

## Almacenamiento de datos

Los registros se guardan en `clientes.json`. El sistema utiliza un archivo temporal durante el guardado para reducir el riesgo de dejar el archivo principal incompleto ante un error de escritura.

**Importante:** antes de utilizarlo con información real, se recomienda mantener copias de seguridad periódicas.

## Estado del proyecto

Proyecto en desarrollo. La versión actual funciona desde la consola y puede ampliarse posteriormente con una interfaz gráfica o web.

## Objetivo

Proyecto personal de práctica y portfolio orientado al desarrollo con Python, la validación de datos, el manejo de archivos JSON y las pruebas automatizadas.
