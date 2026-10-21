# -*- coding: utf-8 -*-
"""Módulo de web scraping para Cúspide con Scrapy.

Ejercicio 03: Implementar un scraper (CuspideSpider) con Scrapy que obtenga
del sitio de Cúspide:
- Precio.
- url de la img.
- Formas de pago y precio.
- Descripción detallada.
Solo trabaja con los libros del catálogo interno (máximo 10 resultados).

Ejercicio 04: Comparar el precio interno con el precio web y generar alertas
en formato CSV.
"""

from book_manager.scraper.cuspide_spider import CuspideSpider
from book_manager.scraper.items import CuspideItem
from book_manager.scraper.loaders import CuspideItemLoader
from book_manager.scraper.pipelines import (
    AlertasPreciosPipeline,
    CuspideValidacionPipeline,
)
from book_manager.scraper.runner import (
    ejecutar_scraper,
    solicitar_umbral_y_ejecutar,
)

__all__ = [
    "CuspideSpider",
    "CuspideItem",
    "CuspideItemLoader",
    "CuspideValidacionPipeline",
    "AlertasPreciosPipeline",
    "ejecutar_scraper",
    "solicitar_umbral_y_ejecutar",
]
