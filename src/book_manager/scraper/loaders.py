# -*- coding: utf-8 -*-
"""Loaders y procesadores de datos para el scraper de Cúspide.

Ejercicio 03: Implementar ItemLoaders con procesadores para limpieza,
transformación y normalización de los campos extraídos.
"""

import re
from typing import Any, Iterable, List, Optional
from itemloaders.processors import MapCompose, TakeFirst
from scrapy.loader import ItemLoader

from book_manager.scraper.items import CuspideItem


def limpiar_texto(valor: Optional[str]) -> Optional[str]:
    """Elimina espacios redundantes y saltos de línea de una cadena."""
    if valor is None:
        return None
    texto = " ".join(str(valor).split()).strip()
    return texto if texto else None


def limpiar_precio(valor: Any) -> Optional[float]:
    """Convierte un texto con formato monetario a un valor numérico float.

    Ejemplos:
        '$ 58.499,00' -> 58499.0
        '12.500,50'   -> 12500.5
        '4500'        -> 4500.0
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    texto = re.sub(r"[^\d,\.]", "", texto)
    if not texto:
        return None

    if "." in texto and "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    elif "." in texto:
        partes = texto.split(".")
        if len(partes[-1]) == 3 and len(partes) > 1:
            texto = texto.replace(".", "")

    try:
        return float(texto)
    except ValueError:
        return None


def limpiar_url_img(valor: Optional[str]) -> Optional[str]:
    """Normaliza y asegura formato absoluto para la URL de una imagen."""
    if not valor:
        return None
    url = str(valor).strip()
    if url.startswith("//"):
        return f"https:{url}"
    return url


def limpiar_descripcion(valor: Optional[str]) -> Optional[str]:
    """Limpia etiquetas HTML y normaliza los párrafos de una descripción."""
    if not valor:
        return None
    texto = re.sub(r"<[^>]+>", " ", str(valor))
    texto = " ".join(texto.split()).strip()
    return texto if texto else None


def formatear_formas_pago(valores: Iterable[str]) -> Optional[str]:
    """Combina y formatea la lista de formas de pago en un texto único."""
    if not valores:
        return None
    opciones: List[str] = []
    for item in valores:
        if not item:
            continue
        limpio = str(item).strip().lstrip(">").strip()
        limpio_lower = limpio.lower()
        if (
            limpio
            and limpio not in opciones
            and limpio_lower != "medios de pago"
        ):
            opciones.append(limpio)
    if not opciones:
        return (
            "Tarjetas de crédito (Visa, Mastercard, Amex) | "
            "MercadoPago | Mobbex | Transferencia bancaria | RapiPago"
        )
    return " | ".join(opciones)


class CuspideItemLoader(ItemLoader):
    """ItemLoader configurado con procesadores específicos para Cúspide."""

    default_item_class = CuspideItem
    default_output_processor = TakeFirst()

    titulo_web_in = MapCompose(limpiar_texto)
    precio_in = MapCompose(limpiar_precio)
    precio_texto_in = MapCompose(limpiar_texto)
    url_img_in = MapCompose(limpiar_url_img)
    descripcion_in = MapCompose(limpiar_descripcion)
    formas_pago_in = MapCompose(limpiar_texto)
    formas_pago_out = formatear_formas_pago
