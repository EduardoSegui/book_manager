# -*- coding: utf-8 -*-
"""Ejecutor programático del scraper de Cúspide.

Permite ejecutar la araña Scrapy desde el código Python (notebooks, CLI
o scripts automatizados) de forma aislada y controlada.

Ejercicio 04: En cada ejecución se genera el archivo CSV de alertas de
precios. La diferencia de precios admitida es ingresada por el usuario antes
de cada ejecución del scraper.
"""

import json
import multiprocessing
import os
import tempfile
from typing import Any, Dict, List, Optional

from scrapy.crawler import CrawlerProcess

from book_manager.reportes.alertas import obtener_ruta_alertas_csv
from book_manager.scraper.cuspide_spider import CuspideSpider
from book_manager.scraper.pipelines import PIPELINES_CUSPIDE


def _trabajador_scraper(
    libros: Optional[List[Dict[str, Any]]],
    max_resultados: int,
    umbral_diferencia: float,
    ruta_alertas_csv: str,
    ruta_salida_json: str,
) -> None:
    """Función de trabajo que corre CrawlerProcess en un proceso aislado."""
    configuracion: Dict[str, Any] = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "COOKIES_ENABLED": False,
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": PIPELINES_CUSPIDE,
        "ALERTAS_CSV_PATH": ruta_alertas_csv,
        "UMBRAL_DIFERENCIA": float(umbral_diferencia),
        "FEEDS": {
            ruta_salida_json: {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
            }
        },
    }

    proceso = CrawlerProcess(settings=configuracion)
    proceso.crawl(
        CuspideSpider,
        libros=libros,
        max_resultados=max_resultados,
        umbral_diferencia=float(umbral_diferencia),
    )
    proceso.start()


def ejecutar_scraper(
    libros: Optional[List[Dict[str, Any]]] = None,
    umbral_diferencia: float = 0.0,
    ruta_alertas_csv: Optional[str] = None,
    max_resultados: int = 10,
    timeout: int = 180,
) -> List[Dict[str, Any]]:
    """Ejecuta el scraper de Cúspide y devuelve los resultados extraídos.

    En cada ejecución se genera el archivo CSV con las alertas de diferencia
    de precios entre el precio interno y el precio web (Ejercicio 04).

    Args:
        libros: Lista de libros a buscar. Si es None, busca los del catálogo.
        umbral_diferencia: Diferencia de precios admitida para generar
            alertas. Con 0.0 se registran todas las diferencias detectadas.
        ruta_alertas_csv: Ruta del archivo CSV de alertas a generar.
        max_resultados: Límite de resultados por búsqueda (máximo 10).
        timeout: Tiempo máximo de espera en segundos.

    Returns:
        Lista de diccionarios con la información recolectada de cada libro.
    """
    ruta_alertas = obtener_ruta_alertas_csv(ruta_alertas_csv)

    with tempfile.NamedTemporaryFile(
        suffix=".json", delete=False
    ) as archivo_temp:
        ruta_temp = archivo_temp.name

    try:
        proceso = multiprocessing.Process(
            target=_trabajador_scraper,
            args=(
                libros,
                max_resultados,
                float(umbral_diferencia),
                ruta_alertas,
                ruta_temp,
            ),
        )
        proceso.start()
        proceso.join(timeout=timeout)

        if proceso.is_alive():
            proceso.terminate()
            proceso.join()
            raise TimeoutError(
                f"El scraping excedió el tiempo límite de {timeout} segundos."
            )

        if os.path.exists(ruta_temp) and os.path.getsize(ruta_temp) > 0:
            with open(ruta_temp, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    finally:
        if os.path.exists(ruta_temp):
            try:
                os.remove(ruta_temp)
            except OSError:
                pass


def solicitar_umbral_diferencia() -> float:
    """Solicita al usuario la diferencia de precios admitida para alertar.

    Returns:
        Diferencia de precios admitida en pesos; 0.0 indica que se
        registrará cualquier diferencia detectada.
    """
    print("\n--- Configuración de Diferencia de Precios para Alertas ---")
    while True:
        try:
            entrada = input(
                "Ingrese la diferencia de precios aceptable para generar "
                "alertas (en $ ARS, ej: 5000; 0 para todas): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print(
                "\nNo se ingresó una diferencia de precios: se generarán "
                "alertas por cualquier diferencia detectada."
            )
            return 0.0

        if not entrada:
            print("Sin valor ingresado: se generarán alertas por cualquier "
                  "diferencia de precio.")
            return 0.0

        try:
            umbral = float(entrada)
        except ValueError:
            print("Valor inválido. Ingrese un número (ej: 5000 o 0).")
            continue

        if umbral < 0:
            print("La diferencia de precios no puede ser negativa.")
            continue

        return umbral


def solicitar_umbral_y_ejecutar(
    libros: Optional[List[Dict[str, Any]]] = None,
    ruta_alertas_csv: Optional[str] = None,
    max_resultados: int = 10,
    timeout: int = 180,
) -> List[Dict[str, Any]]:
    """Solicita al usuario la diferencia de precios y ejecuta el scraper.

    Ejercicio 04: La diferencia de precios debe ser ingresada por el usuario
    antes de cada ejecución del scraper.

    Args:
        libros: Lista de libros a buscar. Si es None, busca los del catálogo.
        ruta_alertas_csv: Ruta del archivo CSV de alertas a generar.
        max_resultados: Límite de resultados por búsqueda (máximo 10).
        timeout: Tiempo máximo de espera en segundos.

    Returns:
        Lista de diccionarios con la información recolectada de cada libro.
    """
    umbral = solicitar_umbral_diferencia()

    print(
        f"Iniciando scraping en Cúspide (umbral de alerta: ${umbral:,.2f} "
        "ARS)..."
    )
    items = ejecutar_scraper(
        libros=libros,
        umbral_diferencia=umbral,
        ruta_alertas_csv=ruta_alertas_csv,
        max_resultados=max_resultados,
        timeout=timeout,
    )

    ruta_alertas = obtener_ruta_alertas_csv(ruta_alertas_csv)
    print(f"Archivo de alertas de precios generado en: {ruta_alertas}")

    return items
