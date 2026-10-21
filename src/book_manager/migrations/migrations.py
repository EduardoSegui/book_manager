# -*- coding: utf-8 -*-
"""Migración y carga de datos hacia la base de datos.

Sprint 2 - Ejercicio 05: Leer los archivos del TP1 (migrations/csv), poblar la
base de datos relacional y generar los archivos `.sql` con las sentencias
INSERT correspondientes, almacenándolos en migrations/sql.

Sprint 3 - Ejercicio 02: Carga de datos secuencial desde archivos `.sql`
(migrations/sql) hacia la base de datos relacional mediante SQLAlchemy.
"""

import csv
import os
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB
from book_manager.models.models import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    LibroGenero,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)


# ---------------------------------------------------------------------------
# Lectura y parseo de los archivos CSV
# ---------------------------------------------------------------------------

def _leer_csv(carpeta_csvs: str, nombre_archivo: str) -> list[dict[str, str]]:
    """Lee un archivo CSV y devuelve una lista de diccionarios.

    Args:
        carpeta_csvs: Carpeta donde se encuentran los archivos CSV.
        nombre_archivo: Nombre del archivo CSV a leer.

    Returns:
        list[dict[str, str]]: Filas del CSV como diccionarios.
    """
    ruta = os.path.join(carpeta_csvs, nombre_archivo)
    with open(ruta, "r", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def _parsear_fecha(fecha_str: str) -> date:
    """Convierte una string de fecha ISO a objeto date."""
    return date.fromisoformat(fecha_str)


def _parsear_decimal(valor_str: str) -> Decimal:
    """Convierte una string a Decimal."""
    return Decimal(valor_str)


def _parsear_lista_enteros(valor_str: str) -> list[int]:
    """Convierte una string de IDs separados por comas a lista de enteros."""
    if not valor_str or not valor_str.strip():
        return []
    return [int(x.strip()) for x in valor_str.split(",")]


# ---------------------------------------------------------------------------
# Construcción de filas tipadas por tabla
# ---------------------------------------------------------------------------

def _filas_generos(carpeta_csvs: str) -> list[dict[str, Any]]:
    """Construye las filas tipadas de la tabla generos."""
    return [
        {
            "id": int(fila["id"]),
            "nombre": fila["nombre"],
            "descripcion": fila.get("descripcion", ""),
        }
        for fila in _leer_csv(carpeta_csvs, "generos.csv")
    ]


def _filas_editoriales(carpeta_csvs: str) -> list[dict[str, Any]]:
    """Construye las filas tipadas de la tabla editoriales."""
    return [
        {"id": int(fila["id"]), "nombre": fila["nombre"]}
        for fila in _leer_csv(carpeta_csvs, "editoriales.csv")
    ]


def _filas_monedas(carpeta_csvs: str) -> list[dict[str, Any]]:
    """Construye las filas tipadas de la tabla monedas."""
    return [
        {
            "id": int(fila["id"]),
            "codigo": fila["codigo"],
            "nombre": fila["nombre"],
            "simbolo": fila["simbolo"],
        }
        for fila in _leer_csv(carpeta_csvs, "monedas.csv")
    ]


def _filas_tipos_cotizacion(carpeta_csvs: str) -> list[dict[str, Any]]:
    """Construye las filas tipadas de la tabla tipos_cotizacion."""
    return [
        {
            "id": int(fila["id"]),
            "nombre": fila["nombre"],
            "descripcion": fila.get("descripcion", ""),
        }
        for fila in _leer_csv(carpeta_csvs, "tipos_cotizacion.csv")
    ]


def _filas_libros(
    carpeta_csvs: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Construye las filas de libros y de la tabla de asociación libro_genero.

    Returns:
        tuple: (filas de libros, filas de la asociación libro_genero).
    """
    filas_libros: list[dict[str, Any]] = []
    filas_asociacion: list[dict[str, Any]] = []

    for fila in _leer_csv(carpeta_csvs, "libros.csv"):
        libro_id = int(fila["id"])
        anio = fila.get("anio_publicacion", "")
        filas_libros.append(
            {
                "id": libro_id,
                "isbn": fila["isbn"],
                "titulo": fila["titulo"],
                "autor": fila["autor"],
                "anio_publicacion": int(anio) if anio else None,
                "editorial_id": int(fila["editorial_id"]),
                "descripcion": fila.get("descripcion", ""),
                "activo": True,
            }
        )
        for genero_id in _parsear_lista_enteros(fila.get("generos_ids", "")):
            filas_asociacion.append(
                {"libro_id": libro_id, "genero_id": genero_id}
            )

    return filas_libros, filas_asociacion


def _filas_precios(carpeta_csvs: str) -> list[dict[str, Any]]:
    """Construye las filas tipadas de la tabla precios."""
    return [
        {
            "id": int(fila["id"]),
            "libro_id": int(fila["libro_id"]),
            "moneda_id": int(fila["moneda_id"]),
            "valor": _parsear_decimal(fila["valor"]),
            "fecha": _parsear_fecha(fila["fecha"]),
        }
        for fila in _leer_csv(carpeta_csvs, "precios.csv")
    ]


def _filas_stock(carpeta_csvs: str) -> list[dict[str, Any]]:
    """Construye las filas tipadas de la tabla stock."""
    return [
        {
            "id": int(fila["id"]),
            "libro_id": int(fila["libro_id"]),
            "cantidad": int(fila["cantidad"]),
        }
        for fila in _leer_csv(carpeta_csvs, "stock.csv")
    ]


def _filas_cotizaciones(carpeta_csvs: str) -> list[dict[str, Any]]:
    """Construye las filas tipadas de la tabla cotizaciones_dolar."""
    return [
        {
            "id": int(fila["id"]),
            "tipo_id": int(fila["tipo_id"]),
            "fecha": _parsear_fecha(fila["fecha"]),
            "valor_compra": _parsear_decimal(fila["valor_compra"]),
            "valor_venta": _parsear_decimal(fila["valor_venta"]),
        }
        for fila in _leer_csv(carpeta_csvs, "cotizaciones_dolar.csv")
    ]


# ---------------------------------------------------------------------------
# Generación de los archivos .sql
# ---------------------------------------------------------------------------

def _literal_sql(valor: Any) -> str:
    """Convierte un valor de Python en un literal SQL válido.

    Args:
        valor: Valor a representar (None, bool, int, Decimal, date o str).

    Returns:
        str: El literal SQL correspondiente.
    """
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, (int, Decimal)):
        return str(valor)
    if isinstance(valor, date):
        return f"'{valor.isoformat()}'"
    texto = str(valor).replace("'", "''")
    return f"'{texto}'"


def _generar_sql(
    nombre_tabla: str,
    columnas: list[str],
    filas: list[dict[str, Any]],
) -> str:
    """Genera el contenido SQL con las sentencias INSERT de una tabla.

    Args:
        nombre_tabla: Nombre de la tabla destino.
        columnas: Nombres de las columnas a insertar.
        filas: Filas (diccionarios) con los valores a insertar.

    Returns:
        str: Contenido del archivo .sql.
    """
    lineas = [f"-- Migración de la tabla {nombre_tabla}", ""]
    lista_columnas = ", ".join(columnas)
    for fila in filas:
        valores = ", ".join(
            _literal_sql(fila[columna]) for columna in columnas
        )
        lineas.append(
            f"INSERT INTO {nombre_tabla} ({lista_columnas}) "
            f"VALUES ({valores});"
        )
    lineas.append("")
    return "\n".join(lineas)


def _escribir_sql(
    carpeta_sqls: str,
    prefijo: str,
    nombre_tabla: str,
    columnas: list[str],
    filas: list[dict[str, Any]],
) -> str:
    """Genera y guarda el archivo .sql de una tabla.

    Returns:
        str: Ruta del archivo .sql generado.
    """
    os.makedirs(carpeta_sqls, exist_ok=True)
    contenido = _generar_sql(nombre_tabla, columnas, filas)
    ruta = os.path.join(carpeta_sqls, f"{prefijo}_{nombre_tabla}.sql")
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)
    return ruta


# ---------------------------------------------------------------------------
# Poblado de la base de datos
# ---------------------------------------------------------------------------

# Tablas con clave primaria autoincremental (secuencia) en PostgreSQL.
_TABLAS_CON_SECUENCIA = (
    "generos",
    "editoriales",
    "monedas",
    "tipos_cotizacion",
    "libros",
    "precios",
    "stock",
    "cotizaciones_dolar",
)


def _vaciar_tablas(sesion: Session) -> None:
    """Borra los registros de las tablas respetando el orden de las FK."""
    orden = (
        CotizacionDolar,
        Stock,
        Precio,
        LibroGenero,
        Libro,
        TipoCotizacion,
        Moneda,
        Editorial,
        Genero,
    )
    for modelo in orden:
        sesion.execute(delete(modelo))


def _insertar(
    sesion: Session,
    modelo: type,
    filas: list[dict[str, Any]],
) -> None:
    """Inserta las filas indicadas creando instancias del modelo ORM."""
    for fila in filas:
        sesion.add(modelo(**fila))


def _reiniciar_secuencias(sesion: Session) -> None:
    """Ajusta las secuencias de PostgreSQL tras insertar IDs explícitos.

    Al migrar se insertan identificadores concretos, por lo que la secuencia
    (SERIAL) de cada tabla quedaría en su valor inicial y un alta posterior
    chocaría con una clave primaria repetida. En SQLite (sin secuencias) no
    hace nada.
    """
    if sesion.get_bind().dialect.name != "postgresql":
        return
    sesion.flush()
    for tabla in _TABLAS_CON_SECUENCIA:
        sesion.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {tabla}), 1))"
            )
        )


# ---------------------------------------------------------------------------
# Punto de entrada de la migración
# ---------------------------------------------------------------------------

def migrar_datos(carpeta_csvs: str, carpeta_sqls: str) -> dict[str, int]:
    """Migra los datos de CSV a SQL y puebla la base de datos.

    Lee los archivos CSV, genera los archivos .sql con las sentencias INSERT y
    carga los registros en la base de datos. Antes de cargar, vacía las tablas
    para que la migración sea idempotente.

    Args:
        carpeta_csvs: Carpeta donde se encuentran los archivos CSV de origen.
        carpeta_sqls: Carpeta donde se guardan los archivos .sql generados.

    Returns:
        dict[str, int]: Cantidad de registros migrados por tabla.
    """
    filas_generos = _filas_generos(carpeta_csvs)
    filas_editoriales = _filas_editoriales(carpeta_csvs)
    filas_monedas = _filas_monedas(carpeta_csvs)
    filas_tipos = _filas_tipos_cotizacion(carpeta_csvs)
    filas_libros, filas_libro_genero = _filas_libros(carpeta_csvs)
    filas_precios = _filas_precios(carpeta_csvs)
    filas_stock = _filas_stock(carpeta_csvs)
    filas_cotizaciones = _filas_cotizaciones(carpeta_csvs)

    columnas_generos = ["id", "nombre", "descripcion"]
    columnas_editoriales = ["id", "nombre"]
    columnas_monedas = ["id", "codigo", "nombre", "simbolo"]
    columnas_tipos = ["id", "nombre", "descripcion"]
    columnas_libros = [
        "id",
        "isbn",
        "titulo",
        "autor",
        "anio_publicacion",
        "editorial_id",
        "descripcion",
        "activo",
    ]
    columnas_libro_genero = ["libro_id", "genero_id"]
    columnas_precios = ["id", "libro_id", "moneda_id", "valor", "fecha"]
    columnas_stock = ["id", "libro_id", "cantidad"]
    columnas_cotizaciones = [
        "id",
        "tipo_id",
        "fecha",
        "valor_compra",
        "valor_venta",
    ]

    _escribir_sql(
        carpeta_sqls, "01", "generos", columnas_generos, filas_generos
    )
    _escribir_sql(
        carpeta_sqls,
        "02",
        "editoriales",
        columnas_editoriales,
        filas_editoriales,
    )
    _escribir_sql(
        carpeta_sqls, "03", "monedas", columnas_monedas, filas_monedas
    )
    _escribir_sql(
        carpeta_sqls, "04", "tipos_cotizacion", columnas_tipos, filas_tipos
    )
    _escribir_sql(carpeta_sqls, "05", "libros", columnas_libros, filas_libros)
    _escribir_sql(
        carpeta_sqls,
        "06",
        "libro_genero",
        columnas_libro_genero,
        filas_libro_genero,
    )
    _escribir_sql(
        carpeta_sqls, "07", "precios", columnas_precios, filas_precios
    )
    _escribir_sql(carpeta_sqls, "08", "stock", columnas_stock, filas_stock)
    _escribir_sql(
        carpeta_sqls,
        "09",
        "cotizaciones_dolar",
        columnas_cotizaciones,
        filas_cotizaciones,
    )

    ConexionDB.inicializar(para_migraciones=True)
    ConexionDB.crear_tablas()
    with ConexionDB.sesion() as sesion:
        _vaciar_tablas(sesion)
        _insertar(sesion, Genero, filas_generos)
        _insertar(sesion, Editorial, filas_editoriales)
        _insertar(sesion, Moneda, filas_monedas)
        _insertar(sesion, TipoCotizacion, filas_tipos)
        sesion.flush()
        _insertar(sesion, Libro, filas_libros)
        sesion.flush()
        _insertar(sesion, LibroGenero, filas_libro_genero)
        _insertar(sesion, Precio, filas_precios)
        _insertar(sesion, Stock, filas_stock)
        _insertar(sesion, CotizacionDolar, filas_cotizaciones)
        _reiniciar_secuencias(sesion)

    return {
        "generos": len(filas_generos),
        "editoriales": len(filas_editoriales),
        "monedas": len(filas_monedas),
        "tipos_cotizacion": len(filas_tipos),
        "libros": len(filas_libros),
        "libro_genero": len(filas_libro_genero),
        "precios": len(filas_precios),
        "stock": len(filas_stock),
        "cotizaciones_dolar": len(filas_cotizaciones),
    }


# ---------------------------------------------------------------------------
# Carga secuencial desde archivos SQL (Sprint 3 - Ejercicio 02)
# ---------------------------------------------------------------------------

def _extraer_sentencias_sql(ruta_archivo: str) -> list[str]:
    """Lee un archivo SQL y extrae las sentencias separadas por ';'.

    Args:
        ruta_archivo: Ruta al archivo .sql.

    Returns:
        list[str]: Sentencias SQL limpias listas para ejecutar.
    """
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        lineas = archivo.readlines()

    lineas_limpias: list[str] = []
    for linea in lineas:
        linea_strip = linea.strip()
        if not linea_strip or linea_strip.startswith("--"):
            continue
        lineas_limpias.append(linea)

    contenido = "".join(lineas_limpias)
    return [
        sentencia.strip()
        for sentencia in contenido.split(";")
        if sentencia.strip()
    ]


def cargar_datos_sql(
    carpeta_sqls: str | None = None,
    vaciar_antes: bool = True,
) -> dict[str, int]:
    """Carga e importa datos secuencialmente desde archivos .sql a la base.

    Lee los scripts SQL en ``carpeta_sqls`` (por defecto ``migrations/sql/``),
    extrae las sentencias DML (INSERT) y las ejecuta en orden secuencial sobre
    la base de datos configurada en SQLAlchemy.

    Args:
        carpeta_sqls: Directorio con los scripts .sql. Si es None, utiliza
            la carpeta 'sql' dentro del paquete migrations.
        vaciar_antes: Si es True, limpia las tablas antes de insertar para
            asegurar una carga limpia e idempotente.

    Returns:
        dict[str, int]: Cantidad de sentencias por cada archivo .sql.

    Raises:
        FileNotFoundError: Si no existe el directorio o no hay archivos .sql.
        ValueError: Si ocurre algún error durante la ejecución de las
            sentencias SQL.
    """
    if carpeta_sqls is None:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        carpeta_sqls = os.path.join(directorio_actual, "sql")

    if not os.path.isdir(carpeta_sqls):
        raise FileNotFoundError(
            f"No existe el directorio de archivos SQL: {carpeta_sqls}"
        )

    archivos_sql = sorted(
        archivo for archivo in os.listdir(carpeta_sqls)
        if archivo.endswith(".sql")
    )
    if not archivos_sql:
        raise FileNotFoundError(
            f"No se encontraron archivos .sql en: {carpeta_sqls}"
        )

    ConexionDB.inicializar(para_migraciones=True)
    ConexionDB.crear_tablas()

    conteo_por_archivo: dict[str, int] = {}

    try:
        with ConexionDB.sesion() as sesion:
            if vaciar_antes:
                _vaciar_tablas(sesion)

            for nombre_archivo in archivos_sql:
                ruta_completa = os.path.join(carpeta_sqls, nombre_archivo)
                sentencias = _extraer_sentencias_sql(ruta_completa)
                for sentencia in sentencias:
                    sesion.execute(text(sentencia))
                conteo_por_archivo[nombre_archivo] = len(sentencias)

            _reiniciar_secuencias(sesion)
    except Exception as error:
        raise ValueError(
            f"Error al cargar datos desde los archivos SQL: {error}"
        ) from error

    return conteo_por_archivo


if __name__ == "__main__":
    import sys

    _directorio = os.path.dirname(os.path.abspath(__file__))
    _carpeta_csvs = os.path.join(_directorio, "csv")
    _carpeta_sqls = os.path.join(_directorio, "sql")

    if "--from-sql" in sys.argv:
        _resultado = cargar_datos_sql(_carpeta_sqls)
        print("Carga desde SQL completada:")
        for _archivo, _cantidad in _resultado.items():
            print(f"  - {_archivo}: {_cantidad} sentencias")
    else:
        _resultado = migrar_datos(_carpeta_csvs, _carpeta_sqls)
        print("Migración completada:")
        for _entidad, _cantidad in _resultado.items():
            print(f"  - {_entidad}: {_cantidad}")
