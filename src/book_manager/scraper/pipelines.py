# -*- coding: utf-8 -*-
"""Pipelines para el procesamiento y persistencia de items de Cúspide.

Ejercicio 03: Implementar pipelines para validar, normalizar y transformar
los items recolectados por la araña.

Ejercicio 04: Implementar pipeline de alertas de precios para comparar
el precio interno contra el precio web y generar un archivo CSV descargable.
"""

import os
from typing import Any, Dict, List, Optional
import scrapy
from scrapy.exceptions import DropItem

from book_manager.reportes.alertas import (
    CABECERAS_CSV,
    calcular_diferencia_precio,
    construir_fila_alerta,
    escribir_alertas_csv,
    obtener_ruta_alertas_csv,
)
from book_manager.scraper.items import CuspideItem

PIPELINES_CUSPIDE: Dict[str, int] = {
    "book_manager.scraper.pipelines.CuspideValidacionPipeline": 100,
    "book_manager.scraper.pipelines.AlertasPreciosPipeline": 300,
}


class CuspideValidacionPipeline:
    """Valida los campos obligatorios y normaliza datos de cada item."""

    def process_item(self, item: CuspideItem) -> CuspideItem:
        """Valida presencia de datos mínimos y complementa campos derivados.

        Raises:
            DropItem: Si el item no posee título o URL web válida.
        """
        titulo = item.get("titulo_web")
        url_web = item.get("url_web")

        if not titulo and not url_web:
            raise DropItem("Item descartado: carece de título y URL web.")

        # Garantizar valores por defecto coherentes
        if not item.get("precio"):
            item["precio"] = 0.0

        if not item.get("precio_texto"):
            item["precio_texto"] = f"${item['precio']:,.2f}"

        if not item.get("descripcion"):
            item["descripcion"] = (
                "Sin descripción detallada en la publicación web."
            )

        if not item.get("formas_pago"):
            item["formas_pago"] = (
                "Tarjetas de crédito (Visa, Mastercard, Amex) | "
                "MercadoPago | Mobbex | Transferencia bancaria"
            )

        # Formas de pago y precio combinados (consigna Ejercicio 03)
        item["formas_pago_y_precio"] = (
            f"Precio web: {item['precio_texto']} | "
            f"Medios: {item['formas_pago']}"
        )

        # Cálculo de diferencias de precio
        precio_web = float(item["precio"])
        precio_interno = float(item.get("precio_interno", 0.0))
        diferencia, porcentaje, _ = calcular_diferencia_precio(
            precio_interno, precio_web
        )
        item["diferencia_precio"] = diferencia
        item["porcentaje_diferencia"] = porcentaje

        return item


class AlertasPreciosPipeline:
    """Genera archivo de alertas CSV según diferencia de precios.

    Ejercicio 04: Comparar el precio interno con el precio web y generar
    alertas en un archivo CSV que se puede descargar para analizar los
    precios. El archivo se genera en cada ejecución del scraper, incluso
    cuando no se detectan diferencias por encima del umbral configurado.
    """

    CABECERAS: List[str] = CABECERAS_CSV

    def __init__(
        self,
        ruta_archivo: Optional[str] = None,
        umbral_diferencia: float = 0.0,
    ) -> None:
        """Inicializa la ruta de destino del archivo de alertas CSV."""
        self.ruta_archivo = obtener_ruta_alertas_csv(ruta_archivo)
        self.umbral_diferencia = float(umbral_diferencia)
        self.items_alertas: List[Dict[str, Any]] = []
        self.crawler: Optional[Any] = None

    @classmethod
    def from_crawler(cls, crawler: Any) -> "AlertasPreciosPipeline":
        """Instancia el pipeline leyendo la configuración del crawler."""
        pipeline = cls(
            ruta_archivo=crawler.settings.get("ALERTAS_CSV_PATH"),
            umbral_diferencia=crawler.settings.getfloat(
                "UMBRAL_DIFERENCIA", 0.0
            ),
        )
        pipeline.crawler = crawler
        return pipeline

    def _obtener_spider(self, spider: Optional[scrapy.Spider]) -> Any:
        """Devuelve la araña en ejecución para leer su configuración."""
        if spider is not None:
            return spider
        if self.crawler is not None:
            return getattr(self.crawler, "spider", None)
        return None

    def open_spider(self, spider: Optional[scrapy.Spider] = None) -> None:
        """Inicializa la lista de alertas antes de procesar."""
        self.items_alertas = []
        # Si la araña tiene umbral específico, tomarlo
        araña = self._obtener_spider(spider)
        umbral_spider = getattr(araña, "umbral_diferencia", None)
        if umbral_spider is not None:
            try:
                self.umbral_diferencia = float(umbral_spider)
            except (ValueError, TypeError):
                pass

    def process_item(self, item: CuspideItem) -> CuspideItem:
        """Compara precios y registra alertas si supera el umbral."""
        fila = construir_fila_alerta(item, self.umbral_diferencia)
        if fila:
            self.items_alertas.append(fila)

        return item

    def close_spider(self, spider: Optional[scrapy.Spider] = None) -> None:
        """Escribe todas las alertas recolectadas en el archivo CSV."""
        if not self.ruta_archivo:
            return

        escribir_alertas_csv(self.items_alertas, self.ruta_archivo)

        araña = self._obtener_spider(spider)
        mensaje = (
            "Archivo de alertas generado con %d registros en '%s'.",
            len(self.items_alertas),
            self.ruta_archivo,
        )
        if araña is not None:
            araña.logger.info(*mensaje)
        else:
            print(mensaje[0] % mensaje[1:])
