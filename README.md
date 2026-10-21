# Book Manager - Sprint 3

## Objetivo
El objetivo principal de este proyecto es profundizar en la integración del sistema de gestión de libros con persistencia en base de datos relacional (PostgreSQL en Supabase / SQLite), incorporando web scraping para extracción de datos en tiempo real (Cúspide), importación secuencial mediante scripts SQL, generación de reportes y auditoría del sistema.

## Introducción y Contexto del problema
A partir de la arquitectura consolidada en los Sprint 1 y Sprint 2, este Sprint 3 incorpora:
- Inicialización y versionado sobre la rama `Sprint_3` con la estructura para `scraper` y `reportes`.
- Carga e importación secuencial directa desde los archivos `.sql` generados previamente.
- Integración de scraping mediante Scrapy para enriquecer la información de los libros del catálogo.
- Comparación de precios internos contra precios de mercado extraídos de la web.
- Generación de reportes tabulados en hojas de cálculo (Excel).
- Mecanismo de auditoría de operaciones sobre el inventario.

## Estado del Sprint
- Ejercicio 01: Inicialización y configuración de la herramienta de versionado (rama `Sprint_3`), y carpetas `scraper/` y `reportes/`. ✓
- Ejercicio 02: Carga de datos secuencial desde archivos SQL (`cargar_datos_sql`). ✓
- Ejercicio 03: Scraper de Cúspide con Scrapy (`CuspideSpider`), `CuspideItem`, `CuspideItemLoader` y `CuspideValidacionPipeline`. ✓
- Ejercicio 04: Comparación del precio interno contra el precio web y generación del archivo CSV de alertas descargable. ✓
- Ejercicio 05: Reporte en Excel con los precios comparados. ☐
- Ejercicio 06: Decorador de auditoría de las operaciones del sistema. ☐
- Ejercicio 07: Opciones de menú para scraping, reportes y auditoría. ☐

## Ejecución

Desde la raíz del repositorio, con el entorno virtual y `PYTHONPATH` apuntando a `src`:

```bash
PYTHONPATH=src .venv/bin/python -m book_manager.main
```

El sistema se ejecuta con los datos de precarga cargados desde `migrations/csv`. Para iniciarlo con los repositorios vacíos:

```bash
PYTHONPATH=src .venv/bin/python -c "from book_manager.main import main; main(import_default_data=False)"
```

## Scraping y alertas de precios (Sprint 3 - Ejercicios 03 y 04)

El scraper busca en Cúspide únicamente los libros del catálogo interno (hasta 10 resultados por título) y extrae precio, imagen, formas de pago y descripción. En cada ejecución compara el precio interno con el precio web y genera el archivo CSV de alertas:

```bash
PYTHONPATH=src .venv/bin/python -c "from book_manager.scraper.runner import solicitar_umbral_y_ejecutar; solicitar_umbral_y_ejecutar()"
```

La diferencia de precios admitida para generar alertas es ingresada por el usuario antes de cada ejecución. El archivo se genera en `src/book_manager/reportes/alertas_precios.csv` con las columnas `fecha_alerta`, `libro_id`, `isbn`, `titulo_interno`, `precio_interno`, `titulo_web`, `precio_web`, `diferencia`, `porcentaje_diferencia`, `umbral_configurado`, `tipo_alerta` y `url_web`, y puede descargarse para su análisis (en Google Colab la descarga se realiza con `files.download`).

El análisis del CSV generado está disponible con `resumen_estadistico_alertas` y la lectura de los registros con `leer_alertas_csv`, ambos en `book_manager.reportes.alertas`.

## Carga e importación desde SQL (Sprint 3 - Ejercicio 02)

Para importar secuencialmente los datos desde los archivos `.sql` (`01_generos.sql` a `09_cotizaciones_dolar.sql`) hacia la base de datos:

```bash
PYTHONPATH=src .venv/bin/python -m book_manager.migrations.migrations --from-sql
```

## Migración de datos (Sprint 2 - Ejercicio 05)

Para migrar los CSV a la base de datos y regenerar los scripts `.sql`:

```bash
PYTHONPATH=src .venv/bin/python -m book_manager.migrations.migrations
```

Los archivos `.sql` se generan en `src/book_manager/migrations/sql` y los datos se cargan en la base de datos indicada por las variables de entorno.

## Base de datos Supabase (PostgreSQL)

El sistema persiste en una base de datos relacional de [Supabase](https://supabase.com/) (PostgreSQL) mediante el ORM SQLAlchemy. La conexión se configura con variables de entorno definidas en `.env`:

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | Pooler en modo transacción (puerto 6543). Lo usa la aplicación. |
| `DIRECT_URL` | Pooler en modo sesión (puerto 5432). Lo usan las migraciones/DDL. |
| `SUPABASE_DB_PASSWORD` | Contraseña de la base. Se inyecta en las URL si contienen `[YOUR-PASSWORD]`. |

La URL de conexión se obtiene en el panel de Supabase en *Connect → ORM* (`DIRECT_URL`). El driver de PostgreSQL (`psycopg2-binary`) se declara en `requirements.txt`.

> Si no se definen las variables de Supabase, el sistema cae a SQLite local (`sqlite:///book_manager.db`) para desarrollo.

> El Sprint 2 reemplaza la persistencia en archivos por la base de datos relacional (Supabase + SQLAlchemy), cuya implementación se completa a lo largo de los ejercicios 02 a 08.