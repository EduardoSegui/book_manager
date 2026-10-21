# -*- coding: utf-8 -*-
"""Módulo de reportes y exportación de datos del sistema Book Manager.

Ejercicio 04: gestión de las alertas de diferencia de precios entre el
catálogo interno y los precios publicados en el sitio web de Cúspide.
"""

from book_manager.reportes.alertas import (
    CABECERAS_CSV,
    calcular_diferencia_precio,
    construir_fila_alerta,
    descargar_archivo_alertas,
    escribir_alertas_csv,
    generar_archivo_alertas_csv,
    leer_alertas_csv,
    obtener_ruta_alertas_csv,
    resumen_estadistico_alertas,
)

__all__ = [
    "CABECERAS_CSV",
    "calcular_diferencia_precio",
    "construir_fila_alerta",
    "descargar_archivo_alertas",
    "escribir_alertas_csv",
    "generar_archivo_alertas_csv",
    "leer_alertas_csv",
    "obtener_ruta_alertas_csv",
    "resumen_estadistico_alertas",
]
