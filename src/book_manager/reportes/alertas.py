# -*- coding: utf-8 -*-
"""Módulo de análisis, gestión y descarga de alertas de precios.

Ejercicio 04: Comparar el precio interno con el precio web y generar
alertas. Cada vez que se ejecuta el scraper se debe generar un archivo
de alertas del tipo CSV que se debe poder descargar para analizar los
precios.

Este módulo concentra la lógica de comparación de precios y la escritura
del CSV de alertas, de modo que el pipeline de Scrapy y el resto de la
aplicación compartan exactamente el mismo criterio de cálculo.
"""

import csv
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

CABECERAS_CSV: List[str] = [
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

TIPO_PRECIO_WEB_MAYOR = "PRECIO_WEB_MAYOR"
TIPO_PRECIO_WEB_MENOR = "PRECIO_WEB_MENOR"
TIPO_PRECIO_IGUAL = "PRECIO_IGUAL"
TIPO_SIN_PRECIO_INTERNO = "SIN_PRECIO_INTERNO"


def obtener_ruta_alertas_csv(ruta_archivo: Optional[str] = None) -> str:
    """Devuelve la ruta absoluta al archivo CSV de alertas de precios.

    Args:
        ruta_archivo: Ruta alternativa al archivo CSV. Si es None, se usa la
            ruta por defecto en `reportes/alertas_precios.csv`.

    Returns:
        Ruta absoluta del archivo CSV de alertas.
    """
    if ruta_archivo:
        return os.path.abspath(ruta_archivo)
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(directorio_actual, "alertas_precios.csv")


def calcular_diferencia_precio(
    precio_interno: Any,
    precio_web: Any,
) -> Tuple[float, float, str]:
    """Compara el precio interno contra el precio web de una publicación.

    Args:
        precio_interno: Precio interno del libro del catálogo.
        precio_web: Precio publicado en el sitio web.

    Returns:
        Tupla con la diferencia con signo (web - interno), el porcentaje de
        diferencia y el tipo de alerta detectado.
    """
    interno = float(precio_interno or 0.0)
    web = float(precio_web or 0.0)

    diferencia = round(web - interno, 2)
    if interno > 0:
        porcentaje = round((diferencia / interno) * 100, 2)
    else:
        porcentaje = 0.0

    if interno <= 0:
        # Sin precio interno no hay comparación posible con el precio web
        tipo_alerta = TIPO_SIN_PRECIO_INTERNO
    elif web > interno:
        tipo_alerta = TIPO_PRECIO_WEB_MAYOR
    elif web < interno:
        tipo_alerta = TIPO_PRECIO_WEB_MENOR
    else:
        tipo_alerta = TIPO_PRECIO_IGUAL

    return diferencia, porcentaje, tipo_alerta


def construir_fila_alerta(
    item: Any,
    umbral_diferencia: float = 0.0,
) -> Optional[Dict[str, Any]]:
    """Construye la fila de alerta de un item scrapeado.

    Args:
        item: Item del scraper (dict o `CuspideItem`) con los precios.
        umbral_diferencia: Diferencia de precios mínima para generar alerta.

    Returns:
        Diccionario con los campos de la alerta, o None si la diferencia de
        precios no alcanza el umbral configurado.
    """
    try:
        precio_interno = float(item.get("precio_interno", 0.0) or 0.0)
        precio_web = float(item.get("precio", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None

    diferencia, porcentaje, tipo_alerta = calcular_diferencia_precio(
        precio_interno, precio_web
    )

    if abs(diferencia) < float(umbral_diferencia):
        return None

    return {
        "fecha_alerta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "libro_id": item.get("libro_id", ""),
        "isbn": item.get("isbn", ""),
        "titulo_interno": item.get("titulo_interno", ""),
        "precio_interno": f"{precio_interno:.2f}",
        "titulo_web": item.get("titulo_web", ""),
        "precio_web": f"{precio_web:.2f}",
        "diferencia": f"{diferencia:.2f}",
        "porcentaje_diferencia": f"{porcentaje:.2f}%",
        "umbral_configurado": f"{float(umbral_diferencia):.2f}",
        "tipo_alerta": tipo_alerta,
        "url_web": item.get("url_web", ""),
    }


def escribir_alertas_csv(
    filas_alertas: Iterable[Dict[str, Any]],
    ruta_archivo: Optional[str] = None,
) -> str:
    """Escribe las filas de alerta en un archivo CSV.

    El archivo se genera siempre, incluso sin alertas, para que exista el
    reporte descargable de cada ejecución del scraper.

    Args:
        filas_alertas: Filas de alerta a escribir.
        ruta_archivo: Ruta alternativa del CSV. Si es None, se usa la ruta
            por defecto en `reportes/alertas_precios.csv`.

    Returns:
        Ruta absoluta del archivo CSV generado.
    """
    ruta = obtener_ruta_alertas_csv(ruta_archivo)

    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    with open(ruta, mode="w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CABECERAS_CSV)
        escritor.writeheader()
        for fila in filas_alertas:
            escritor.writerow(fila)

    return ruta


def generar_archivo_alertas_csv(
    items: Iterable[Any],
    umbral_diferencia: float = 0.0,
    ruta_archivo: Optional[str] = None,
) -> str:
    """Genera el archivo CSV de alertas a partir de los items scrapeados.

    Args:
        items: Items scrapeados con precios internos y web.
        umbral_diferencia: Diferencia de precios mínima para generar alerta.
        ruta_archivo: Ruta alternativa del CSV de alertas.

    Returns:
        Ruta absoluta del archivo CSV generado.
    """
    filas_alertas: List[Dict[str, Any]] = []
    for item in items:
        fila = construir_fila_alerta(item, umbral_diferencia)
        if fila:
            filas_alertas.append(fila)

    return escribir_alertas_csv(filas_alertas, ruta_archivo)


def leer_alertas_csv(
    ruta_archivo: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Lee el archivo CSV de alertas y devuelve una lista de diccionarios.

    Args:
        ruta_archivo: Ruta alternativa al archivo CSV. Si es None, usa la ruta
            por defecto en reportes/alertas_precios.csv.

    Returns:
        Lista de diccionarios con los campos de cada alerta generada.
    """
    ruta = obtener_ruta_alertas_csv(ruta_archivo)
    if not os.path.exists(ruta):
        return []

    alertas: List[Dict[str, str]] = []
    with open(ruta, mode="r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            alertas.append(dict(fila))
    return alertas


def resumen_estadistico_alertas(
    alertas: Optional[List[Dict[str, Any]]] = None,
    ruta_archivo: Optional[str] = None,
) -> Dict[str, Any]:
    """Calcula métricas estadísticas sobre las alertas de precios detectadas.

    Args:
        alertas: Lista de alertas pre-cargadas. Si es None, lee el CSV.
        ruta_archivo: Ruta opcional del CSV a analizar.

    Returns:
        Diccionario con indicadores analíticos: total, cantidad de casos con
        precio web mayor, menor o igual, diferencia promedio, diferencia
        máxima y libros con mayor brecha de precio.
    """
    if alertas is None:
        alertas = leer_alertas_csv(ruta_archivo)

    if not alertas:
        return {
            "total_alertas": 0,
            "precio_web_mayor": 0,
            "precio_web_menor": 0,
            "precio_igual": 0,
            "sin_precio_interno": 0,
            "diferencia_promedio": 0.0,
            "diferencia_promedio_absoluta": 0.0,
            "diferencia_maxima": 0.0,
            "mayores_discrepancias": [],
        }

    precio_web_mayor = 0
    precio_web_menor = 0
    precio_igual = 0
    sin_precio_interno = 0
    diferencias: List[float] = []

    for alerta in alertas:
        tipo = alerta.get("tipo_alerta", "")
        if tipo == TIPO_PRECIO_WEB_MAYOR:
            precio_web_mayor += 1
        elif tipo == TIPO_PRECIO_WEB_MENOR:
            precio_web_menor += 1
        elif tipo == TIPO_PRECIO_IGUAL:
            precio_igual += 1
        elif tipo == TIPO_SIN_PRECIO_INTERNO:
            sin_precio_interno += 1

        try:
            diferencias.append(float(alerta.get("diferencia", 0.0)))
        except (TypeError, ValueError):
            continue

    if diferencias:
        diferencia_promedio = round(sum(diferencias) / len(diferencias), 2)
        diferencia_promedio_absoluta = round(
            sum(abs(d) for d in diferencias) / len(diferencias), 2
        )
        diferencia_maxima = round(max(diferencias), 2)
    else:
        diferencia_promedio = 0.0
        diferencia_promedio_absoluta = 0.0
        diferencia_maxima = 0.0

    # Top discrepancias ordenadas de mayor a menor en valor absoluto
    ordenadas = sorted(
        alertas,
        key=lambda x: abs(float(x.get("diferencia", 0.0) or 0.0)),
        reverse=True,
    )
    mayores_discrepancias = [
        {
            "titulo": x.get("titulo_interno", ""),
            "precio_interno": float(x.get("precio_interno", 0.0) or 0.0),
            "precio_web": float(x.get("precio_web", 0.0) or 0.0),
            "diferencia": float(x.get("diferencia", 0.0) or 0.0),
            "tipo_alerta": x.get("tipo_alerta", ""),
        }
        for x in ordenadas[:5]
    ]

    return {
        "total_alertas": len(alertas),
        "precio_web_mayor": precio_web_mayor,
        "precio_web_menor": precio_web_menor,
        "precio_igual": precio_igual,
        "sin_precio_interno": sin_precio_interno,
        "diferencia_promedio": diferencia_promedio,
        "diferencia_promedio_absoluta": diferencia_promedio_absoluta,
        "diferencia_maxima": diferencia_maxima,
        "mayores_discrepancias": mayores_discrepancias,
    }


def descargar_archivo_alertas(ruta_archivo: Optional[str] = None) -> str:
    """Gestiona la descarga del archivo CSV de alertas en Colab o local.

    En Google Colab invoca files.download. En ejecución local verifica
    la existencia y devuelve la ruta absoluta del archivo para el usuario.
    """
    ruta = obtener_ruta_alertas_csv(ruta_archivo)
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"El archivo de alertas '{ruta}' aún no fue generado."
        )

    try:
        from google.colab import files  # type: ignore

        files.download(ruta)
        return f"Descarga iniciada en Google Colab desde: {ruta}"
    except ImportError:
        return f"Archivo disponible para descarga y análisis en: {ruta}"
