# -*- coding: utf-8 -*-
"""Ejecutor programático del scraper de Cúspide.

Permite ejecutar la araña Scrapy desde el código Python (notebooks, CLI
o scripts automatizados) de forma aislada y controlada.
"""

import json
import multiprocessing
import os
import tempfile
from typing import Any, Dict, List, Optional

from scrapy.crawler import CrawlerProcess

from book_manager.scraper.cuspide_spider import CuspideSpider


def _trabajador_scraper(
    libros: Optional[List[Dict[str, Any]]],
    max_resultados: int,
    umbral_diferencia: Optional[float],
    ruta_alertas_csv: Optional[str],
    ruta_salida_json: str,
) -> None:
    """Función de trabajo que corre CrawlerProcess en un proceso aislado."""
    pipelines: Dict[str, int] = {
        "book_manager.scraper.pipelines.CuspideValidacionPipeline": 100,
    }

    if umbral_diferencia is not None:
        pipelines[
            "book_manager.scraper.pipelines.AlertasPreciosPipeline"
        ] = 300

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
        "ITEM_PIPELINES": pipelines,
        "FEEDS": {
            ruta_salida_json: {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
            }
        },
    }

    if ruta_alertas_csv:
        configuracion["ALERTAS_CSV_PATH"] = ruta_alertas_csv
    if umbral_diferencia is not None:
        configuracion["UMBRAL_DIFERENCIA"] = float(umbral_diferencia)

    proceso = CrawlerProcess(settings=configuracion)
    proceso.crawl(
        CuspideSpider,
        libros=libros,
        max_resultados=max_resultados,
        umbral_diferencia=umbral_diferencia,
    )
    proceso.start()


def ejecutar_scraper(
    libros: Optional[List[Dict[str, Any]]] = None,
    umbral_diferencia: Optional[float] = None,
    ruta_alertas_csv: Optional[str] = None,
    max_resultados: int = 10,
    timeout: int = 180,
) -> List[Dict[str, Any]]:
    """Ejecuta el scraper de Cúspide y devuelve los resultados extraídos.

    Args:
        libros: Lista de libros a buscar. Si es None, busca los del catálogo.
        umbral_diferencia: Diferencia de precios para disparar alertas CSV.
        ruta_alertas_csv: Ruta del archivo CSV de alertas a generar.
        max_resultados: Límite de resultados por búsqueda (máximo 10).
        timeout: Tiempo máximo de espera en segundos.

    Returns:
        Lista de diccionarios con la información recolectada de cada libro.
    """
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
                umbral_diferencia,
                ruta_alertas_csv,
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


def solicitar_umbral_y_ejecutar(
    libros: Optional[List[Dict[str, Any]]] = None,
    ruta_alertas_csv: Optional[str] = None,
    max_resultados: int = 10,
) -> List[Dict[str, Any]]:
    """Solicita al usuario la diferencia de precios y ejecuta el scraper.

    Ejercicio 04: La diferencia de precios debe ser ingresada por el usuario
    antes de cada ejecución del scraper.
    """
    print("\n--- Configuración de Ejecución de Scraping y Alertas ---")
    entrada = input(
        "Ingrese la diferencia de precios máxima permitida para generar "
        "alertas (en $ ARS, ej: 5000 o 0 para todas): "
    ).strip()

    try:
        umbral = float(entrada) if entrada else 0.0
    except ValueError:
        print("Valor inválido. Se utilizará umbral 0.0 (todas las alertas).")
        umbral = 0.0

    print(
        f"Iniciando scraping en Cúspide (umbral: ${umbral:,.2f} ARS)..."
    )
    items = ejecutar_scraper(
        libros=libros,
        umbral_diferencia=umbral,
        ruta_alertas_csv=ruta_alertas_csv,
        max_resultados=max_resultados,
    )
    return items
