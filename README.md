# Book Manager - Sprint 2

## Objetivo
El objetivo principal de este proyecto es aplicar los conocimientos adquiridos en programación orientada a objetos, almacenamiento de datos en archivos para su persistencia.

## Introducción y Contexto del problema
A partir del Sprint 1 (aplicación de consola que gestiona el inventario de una librería persistiendo en archivos), en este Sprint 2 se amplía el alcance haciendo que la aplicación persista en una base de datos relacional mediante el ORM SQLAlchemy.

La idea principal es realizar una migración de todos los datos cargados en los archivos (CSV) a tablas relacionales, consolidando las bases del manejo de bases de datos, la normalización, la conexión segura y la carga inicial.

Además se realizan consultas a APIs externas (cotizaciones del dólar) para registrar las cotizaciones en la base de datos.

## Estado del Sprint
- Ejercicio 01: Inicialización y configuración de la herramienta de versionado (rama `Sprint_2`). ✓
- Ejercicio 02: Clase `ConexionDB` para la conexión con SQLAlchemy. ⏳
- Ejercicio 03: Context manager para manejar las transacciones a la base de datos. ⏳
- Ejercicio 04: Creación de las tablas del sistema con tipos de datos y relaciones. ⏳
- Ejercicio 05: Migración de datos (CSV → SQL). ⏳
- Ejercicio 06: Modificaciones para que todo el sistema utilice base de datos. ⏳
- Ejercicio 07: API del dólar + dotenv. ⏳
- Ejercicio 08: Nuevas opciones de menú (cotizaciones por API, precios bimonetarios, exportación CSV). ⏳

## Ejecución

Desde la raíz del repositorio, con el entorno virtual y `PYTHONPATH` apuntando a `src`:

```bash
PYTHONPATH=src .venv/bin/python -m book_manager.main
```

El sistema se ejecuta con los datos de precarga cargados desde `migrations/csv`. Para iniciarlo con los repositorios vacíos:

```bash
PYTHONPATH=src .venv/bin/python -c "from book_manager.main import main; main(import_default_data=False)"
```

> El Sprint 2 reemplaza la persistencia en archivos por la base de datos relacional (SQLite + SQLAlchemy), cuya implementación se completa a lo largo de los ejercicios 02 a 08.