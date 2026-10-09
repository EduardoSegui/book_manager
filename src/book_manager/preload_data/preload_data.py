# -*- coding: utf-8 -*-
"""Módulo de precarga de datos para el sistema Book Manager.

Ejercicio 05: Crear archivos para la importación de datos.
Lee los archivos CSV ubicados en migrations/csv y los carga en los
repositorios correspondientes.
"""

import csv
import os
from datetime import date
from decimal import Decimal
from typing import Any

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)


# Ruta al directorio CSV (relativa a este archivo)
_CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations", "csv")


def _ruta_csv(nombre_archivo: str) -> str:
    """Devuelve la ruta absoluta al archivo CSV."""
    return os.path.abspath(os.path.join(_CSV_DIR, nombre_archivo))


def _leer_csv(nombre_archivo: str) -> list[dict[str, str]]:
    """Lee un archivo CSV y devuelve una lista de diccionarios."""
    ruta = _ruta_csv(nombre_archivo)
    with open(ruta, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        return list(lector)


def _parsear_fecha(fecha_str: str) -> date:
    """Convierte una string de fecha ISO a objeto date."""
    return date.fromisoformat(fecha_str)


def _parsear_decimal(valor_str: str) -> Decimal:
    """Convierte una string a Decimal."""
    return Decimal(valor_str)


def _parsear_lista_enteros(valor_str: str) -> list[int]:
    """Convierte una string de IDs separados por comas a lista de enteros."""
    if not valor_str.strip():
        return []
    return [int(x.strip()) for x in valor_str.split(",")]


def cargar_generos(repositorio: RepositorioGenero) -> int:
    """Carga los géneros desde el CSV al repositorio.

    Returns:
        int: Cantidad de registros cargados.
    """
    registros = _leer_csv("generos.csv")
    for fila in registros:
        genero = Genero(
            id=int(fila["id"]),
            nombre=fila["nombre"],
            descripcion=fila.get("descripcion", ""),
        )
        repositorio.crear(genero)
    return len(registros)


def cargar_editoriales(repositorio: RepositorioEditorial) -> int:
    """Carga las editoriales desde el CSV al repositorio.

    Returns:
        int: Cantidad de registros cargados.
    """
    registros = _leer_csv("editoriales.csv")
    for fila in registros:
        editorial = Editorial(
            id=int(fila["id"]),
            nombre=fila["nombre"],
        )
        repositorio.crear(editorial)
    return len(registros)


def cargar_monedas(repositorio: RepositorioMoneda) -> int:
    """Carga las monedas desde el CSV al repositorio.

    Returns:
        int: Cantidad de registros cargados.
    """
    registros = _leer_csv("monedas.csv")
    for fila in registros:
        moneda = Moneda(
            id=int(fila["id"]),
            codigo=fila["codigo"],
            nombre=fila["nombre"],
            simbolo=fila["simbolo"],
        )
        repositorio.crear(moneda)
    return len(registros)


def cargar_tipos_cotizacion(repositorio: RepositorioTipoCotizacion) -> int:
    """Carga los tipos de cotización desde el CSV al repositorio.

    Returns:
        int: Cantidad de registros cargados.
    """
    registros = _leer_csv("tipos_cotizacion.csv")
    for fila in registros:
        tipo = TipoCotizacion(
            id=int(fila["id"]),
            nombre=fila["nombre"],
            descripcion=fila.get("descripcion", ""),
        )
        repositorio.crear(tipo)
    return len(registros)


def cargar_libros(repositorio: RepositorioLibro) -> int:
    """Carga los libros desde el CSV al repositorio.

    Returns:
        int: Cantidad de registros cargados.
    """
    registros = _leer_csv("libros.csv")
    for fila in registros:
        libro = Libro(
            id=int(fila["id"]),
            isbn=fila["isbn"],
            titulo=fila["titulo"],
            autor=fila["autor"],
            anio_publicacion=int(fila["anio_publicacion"]) if fila.get("anio_publicacion") else None,
            editorial_id=int(fila["editorial_id"]),
            generos_ids=_parsear_lista_enteros(fila.get("generos_ids", "")),
            descripcion=fila.get("descripcion", ""),
        )
        repositorio.crear(libro)
    return len(registros)


def cargar_precios(repositorio: RepositorioPrecio) -> int:
    """Carga los precios desde el CSV al repositorio.

    Returns:
        int: Cantidad de registros cargados.
    """
    registros = _leer_csv("precios.csv")
    for fila in registros:
        precio = Precio(
            id=int(fila["id"]),
            libro_id=int(fila["libro_id"]),
            moneda_id=int(fila["moneda_id"]),
            valor=_parsear_decimal(fila["valor"]),
            fecha=_parsear_fecha(fila["fecha"]),
        )
        repositorio.crear(precio)
    return len(registros)


def cargar_stock(repositorio: RepositorioStock) -> int:
    """Carga el stock desde el CSV al repositorio.

    Returns:
        int: Cantidad de registros cargados.
    """
    registros = _leer_csv("stock.csv")
    for fila in registros:
        stock = Stock(
            id=int(fila["id"]),
            libro_id=int(fila["libro_id"]),
            cantidad=int(fila["cantidad"]),
        )
        repositorio.crear(stock)
    return len(registros)


def cargar_cotizaciones_dolar(repositorio: RepositorioCotizacionDolar) -> int:
    """Carga las cotizaciones del dólar desde el CSV al repositorio.

    Returns:
        int: Cantidad de registros cargados.
    """
    registros = _leer_csv("cotizaciones_dolar.csv")
    for fila in registros:
        cotizacion = CotizacionDolar(
            id=int(fila["id"]),
            tipo_id=int(fila["tipo_id"]),
            fecha=_parsear_fecha(fila["fecha"]),
            valor_compra=_parsear_decimal(fila["valor_compra"]),
            valor_venta=_parsear_decimal(fila["valor_venta"]),
        )
        repositorio.crear(cotizacion)
    return len(registros)


def cargar_todos_los_datos(
    repo_genero: RepositorioGenero,
    repo_editorial: RepositorioEditorial,
    repo_moneda: RepositorioMoneda,
    repo_tipo_cotizacion: RepositorioTipoCotizacion,
    repo_libro: RepositorioLibro,
    repo_precio: RepositorioPrecio,
    repo_stock: RepositorioStock,
    repo_cotizacion: RepositorioCotizacionDolar,
) -> dict[str, int]:
    """Carga todos los datos desde los CSV a los repositorios.

    Args:
        repo_genero: Repositorio de géneros.
        repo_editorial: Repositorio de editoriales.
        repo_moneda: Repositorio de monedas.
        repo_tipo_cotizacion: Repositorio de tipos de cotización.
        repo_libro: Repositorio de libros.
        repo_precio: Repositorio de precios.
        repo_stock: Repositorio de stock.
        repo_cotizacion: Repositorio de cotizaciones del dólar.

    Returns:
        dict[str, int]: Diccionario con la cantidad de registros cargados por entidad.
    """
    resultados: dict[str, int] = {}

    resultados["generos"] = cargar_generos(repo_genero)
    resultados["editoriales"] = cargar_editoriales(repo_editorial)
    resultados["monedas"] = cargar_monedas(repo_moneda)
    resultados["tipos_cotizacion"] = cargar_tipos_cotizacion(repo_tipo_cotizacion)
    resultados["libros"] = cargar_libros(repo_libro)
    resultados["precios"] = cargar_precios(repo_precio)
    resultados["stock"] = cargar_stock(repo_stock)
    resultados["cotizaciones_dolar"] = cargar_cotizaciones_dolar(repo_cotizacion)

    return resultados
