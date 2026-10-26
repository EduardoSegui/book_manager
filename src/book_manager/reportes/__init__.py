# -*- coding: utf-8 -*-
"""Módulo de reportes y exportación de datos del sistema Book Manager.

Ejercicio 04: gestión de las alertas de diferencia de precios entre el
catálogo interno y los precios publicados en el sitio web de Cúspide.

Ejercicio 05: generación del reporte de comparación de precios en Excel con
los campos Libro, Precio interno, Precio web, Diferencia y Fecha de
extracción.
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
from book_manager.reportes.reporte_excel import (
    CABECERAS_REPORTE,
    construir_fila_reporte,
    descargar_reporte_excel,
    escribir_reporte_excel,
    generar_reporte_desde_alertas_csv,
    generar_reporte_excel,
    leer_reporte_excel,
    obtener_ruta_reporte_excel,
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
    "CABECERAS_REPORTE",
    "construir_fila_reporte",
    "descargar_reporte_excel",
    "escribir_reporte_excel",
    "generar_reporte_desde_alertas_csv",
    "generar_reporte_excel",
    "leer_reporte_excel",
    "obtener_ruta_reporte_excel",
]
