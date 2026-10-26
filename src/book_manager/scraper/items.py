# -*- coding: utf-8 -*-
"""Definición de items para el scraper de Cúspide.

Ejercicio 03: Implementar un scraper (CuspideSpider) con Scrapy que obtenga
del sitio de Cúspide los datos requeridos (precio, imagen, formas de pago
y descripción detallada).
"""

from typing import Any
import scrapy


class CuspideItem(scrapy.Item):
    """Item que contiene los datos extraídos de un libro desde Cúspide."""

    libro_id = scrapy.Field()
    isbn = scrapy.Field()
    titulo_interno = scrapy.Field()
    precio_interno = scrapy.Field()
    titulo_web = scrapy.Field()
    precio = scrapy.Field()
    precio_texto = scrapy.Field()
    url_img = scrapy.Field()
    formas_pago = scrapy.Field()
    formas_pago_y_precio = scrapy.Field()
    descripcion = scrapy.Field()
    url_web = scrapy.Field()
    fecha_extraccion = scrapy.Field()
    diferencia_precio = scrapy.Field()
    porcentaje_diferencia = scrapy.Field()
