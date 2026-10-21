# -*- coding: utf-8 -*-
"""Pipelines para el procesamiento y persistencia de items de Cúspide.

Ejercicio 03: Implementar pipelines para validar, normalizar y transformar
los items recolectados por la araña.

Ejercicio 04: Implementar pipeline de alertas de precios para comparar
el precio interno contra el precio web y generar un archivo CSV descargable.
"""

import csv
from datetime import datetime
import os
from typing import Any, Dict, List, Optional
import scrapy
from scrapy.exceptions import DropItem

from book_manager.scraper.items import CuspideItem


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
        diferencia = round(precio_web - precio_interno, 2)
        item["diferencia_precio"] = diferencia

        if precio_interno > 0:
            porcentaje = round((diferencia / precio_interno) * 100, 2)
        else:
            porcentaje = 0.0
        item["porcentaje_diferencia"] = porcentaje

        return item


class AlertasPreciosPipeline:
    """Genera archivo de alertas CSV según diferencia de precios.

    Ejercicio 04: Comparar el precio interno con el precio web y generar
    alertas en un archivo CSV que se puede descargar para analizar los precios.
    """

    CABECERAS: List[str] = [
        "fecha_alerta",
        "libro_id",
        "isbn",
        "titulo_interno",
        "precio_interno",
        "titulo_web",
        "precio_web",
        "diferencia",
        "porcentaje_diferencia",
        "umbral_configurado",
        "tipo_alerta",
        "url_web",
    ]

    def __init__(
        self,
        ruta_archivo: Optional[str] = None,
        umbral_diferencia: float = 0.0,
    ) -> None:
        """Inicializa la ruta de destino del archivo de alertas CSV."""
        if ruta_archivo:
            self.ruta_archivo = ruta_archivo
        else:
            directorio = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "reportes"
            )
            os.makedirs(directorio, exist_ok=True)
            self.ruta_archivo = os.path.join(
                directorio, "alertas_precios.csv"
            )
        self.umbral_diferencia = float(umbral_diferencia)
        self.items_alertas: List[Dict[str, Any]] = []

    @classmethod
    def from_crawler(cls, crawler: Any) -> "AlertasPreciosPipeline":
        """Instancia el pipeline leyendo la configuración del crawler."""
        ruta = crawler.settings.get("ALERTAS_CSV_PATH")
        umbral = crawler.settings.getfloat("UMBRAL_DIFERENCIA", 0.0)
        return cls(ruta_archivo=ruta, umbral_diferencia=umbral)

    def open_spider(self, spider: scrapy.Spider) -> None:
        """Inicializa la lista de alertas antes de procesar."""
        self.items_alertas = []
        # Si la araña tiene umbral específico, tomarlo
        umbral_spider = getattr(spider, "umbral_diferencia", None)
        if umbral_spider is not None:
            try:
                self.umbral_diferencia = float(umbral_spider)
            except (ValueError, TypeError):
                pass

    def process_item(self, item: CuspideItem) -> CuspideItem:
        """Compara precios y registra alertas si supera el umbral."""
        precio_web = float(item.get("precio", 0.0))
        precio_interno = float(item.get("precio_interno", 0.0))
        diferencia = round(abs(precio_web - precio_interno), 2)
        diferencia_con_signo = round(precio_web - precio_interno, 2)
        porcentaje = float(item.get("porcentaje_diferencia", 0.0))

        # Se dispara la alerta si la diferencia absoluta supera el umbral
        if diferencia >= self.umbral_diferencia:
            tipo = (
                "PRECIO_WEB_MAYOR"
                if precio_web > precio_interno
                else "PRECIO_WEB_MENOR"
            )
            registro = {
                "fecha_alerta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "libro_id": item.get("libro_id", 0),
                "isbn": item.get("isbn", ""),
                "titulo_interno": item.get("titulo_interno", ""),
                "precio_interno": f"{precio_interno:.2f}",
                "titulo_web": item.get("titulo_web", ""),
                "precio_web": f"{precio_web:.2f}",
                "diferencia": f"{diferencia_con_signo:.2f}",
                "porcentaje_diferencia": f"{porcentaje:.2f}%",
                "umbral_configurado": f"{self.umbral_diferencia:.2f}",
                "tipo_alerta": tipo,
                "url_web": item.get("url_web", ""),
            }
            self.items_alertas.append(registro)

        return item

    def close_spider(self, spider: scrapy.Spider) -> None:
        """Escribe todas las alertas recolectadas en el archivo CSV."""
        if not self.ruta_archivo:
            return

        carpeta = os.path.dirname(self.ruta_archivo)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)

        with open(
            self.ruta_archivo, mode="w", newline="", encoding="utf-8"
        ) as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=self.CABECERAS)
            escritor.writeheader()
            for alerta in self.items_alertas:
                escritor.writerow(alerta)

        spider.logger.info(
            "Archivo de alertas generado con %d registros en '%s'.",
            len(self.items_alertas),
            self.ruta_archivo,
        )
