# Book Manager - Sprint 1

## Objetivo
El objetivo principal de este proyecto es aplicar los conocimientos adquiridos en programación orientada a objetos, almacenamiento de datos en archivos para su persistencia.

## Introducción y Contexto del problema
Una librería con venta al público necesita modernizar su sistema de gestión de inventario de libros. Debido a la fluctuación en los costos de importación de material bibliográfico, el sistema debe gestionar precios en diferentes monedas y seguir de cerca la cotización del dólar para actualizar sus valores en tiempo real.
El objetivo es desarrollar una aplicación de consola (CLI) robusta en Python que permita gestionar el inventario de una librería, cotizar los libros en tiempo real según el valor del dólar y comparar precios automáticamente con la competencia web.

## Estado del Sprint
- Ejercicio 01: Inicialización y configuración de la herramienta de versionado. ✓
- Ejercicio 02: Definición de las clases entidad (Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock, CotizacionDolar). ✓
- Ejercicio 03: Definición de las clases responsables de la persistencia de datos (repositorios con CRUD completo). ✓
- Ejercicio 04: Definición de las clases responsables de la lógica de negocio (servicios). ✓
- Ejercicio 05: Creación de archivos para la importación de datos (CSV con precarga). ✓
- Ejercicio 06: Interfaz de consola con los CRUD de todas las entidades. ✓
- Ejercicio 07: Creación del archivo main.py que se encarga de ejecutar el sistema. ✓

## Ejecución

Desde la raíz del repositorio, con el entorno virtual y `PYTHONPATH` apuntando a `src`:

```bash
PYTHONPATH=src .venv/bin/python -m book_manager.main
```

El sistema se ejecuta con los datos de precarga cargados desde `migrations/csv`. Para iniciarlo con los repositorios vacíos:

```bash
PYTHONPATH=src .venv/bin/python -c "from book_manager.main import main; main(import_default_data=False)"
```

Los repositorios trabajan en memoria, por lo que los datos no se persisten entre ejecuciones.
