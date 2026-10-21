# -*- coding: utf-8 -*-
"""Spider de Scrapy para la extracción de libros desde Cúspide.

Ejercicio 03: Implementar un scraper (CuspideSpider) con Scrapy que obtenga
del sitio de Cúspide los datos requeridos (precio, imagen, formas de pago
y descripción detallada). Solo se trabaja con los libros del catálogo interno,
limitando a los 10 primeros resultados de cada búsqueda por título.
"""

from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterable, List, Optional
import urllib.parse

import scrapy
from scrapy.http import Response

from book_manager.scraper.loaders import CuspideItemLoader


class CuspideSpider(scrapy.Spider):
    """Araña para scrapear información de libros en cuspide.com."""

    name = "cuspide"
    allowed_domains = ["cuspide.com", "cdn.livriz.com"]

    custom_settings = {
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
        "ITEM_PIPELINES": {
            "book_manager.scraper.pipelines.CuspideValidacionPipeline": 100,
        },
    }

    def __init__(
        self,
        libros: Optional[List[Dict[str, Any]]] = None,
        max_resultados: int = 10,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Inicializa la araña con los libros del catálogo a buscar.

        Args:
            libros: Lista opcional de libros internos a consultar.
                Si no se provee, se cargan los libros activos del catálogo.
            max_resultados: Cantidad máxima de publicaciones web por libro.
        """
        super().__init__(*args, **kwargs)
        self.max_resultados = int(max_resultados)
        if libros is not None:
            self.libros = libros
        else:
            self.libros = self._cargar_libros_catalogo()

    def _cargar_libros_catalogo(self) -> List[Dict[str, Any]]:
        """Carga los libros activos y sus precios en ARS desde el sistema."""
        try:
            from book_manager.repositories.repositories import (
                RepositorioLibro,
                RepositorioPrecio,
            )

            repo_libro = RepositorioLibro()
            repo_precio = RepositorioPrecio()

            libros_activos = [
                libro for libro in repo_libro.leer_todos() if libro.activo
            ]
            todos_precios = repo_precio.leer_todos()

            resultado: List[Dict[str, Any]] = []
            for libro in libros_activos:
                precios_ars = [
                    p.valor
                    for p in todos_precios
                    if p.libro_id == libro.id and p.moneda_id == 1
                ]
                precio_interno = float(precios_ars[-1]) if precios_ars else 0.0
                resultado.append(
                    {
                        "id": libro.id,
                        "isbn": libro.isbn,
                        "titulo": libro.titulo,
                        "precio_interno": precio_interno,
                    }
                )
            return resultado
        except Exception as error:
            self.logger.warning(
                "Error al cargar libros desde repositorios: %s", error
            )
            return []

    def _generar_solicitudes(self) -> Iterable[scrapy.Request]:
        """Genera solicitudes de búsqueda solo para libros del catálogo."""
        if not self.libros:
            self.logger.warning(
                "No hay libros en el catálogo disponibles para buscar."
            )
            return

        for libro in self.libros:
            titulo = libro.get("titulo", "").strip()
            if not titulo:
                continue
            query = urllib.parse.quote_plus(titulo)
            url = f"https://cuspide.com/?s={query}&post_type=product"
            meta = {
                "libro_id": libro.get("id"),
                "isbn": libro.get("isbn"),
                "titulo_interno": titulo,
                "precio_interno": float(libro.get("precio_interno", 0.0)),
            }
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta=meta,
                dont_filter=True,
            )

    async def start(self) -> AsyncIterator[scrapy.Request]:
        """Punto de entrada asíncrono para Scrapy 2.13+."""
        for request in self._generar_solicitudes():
            yield request

    def start_requests(self) -> Iterable[scrapy.Request]:
        """Punto de entrada síncrono para compatibilidad hacia atrás."""
        return self._generar_solicitudes()

    def parse(self, response: Response) -> Iterable[scrapy.Request]:
        """Extrae hasta 10 enlaces de resultados por cada libro buscado."""
        links = response.css(
            "div.product-small a[href*='/producto/']::attr(href)"
        ).getall()

        vistos = set()
        urls_filtradas: List[str] = []
        for link in links:
            url_abs = response.urljoin(link)
            if url_abs not in vistos:
                vistos.add(url_abs)
                urls_filtradas.append(url_abs)

        # Restricción: como máximo los 10 primeros resultados de la búsqueda
        urls_seleccionadas = urls_filtradas[: self.max_resultados]
        self.logger.info(
            "Búsqueda '%s': %d publicaciones encontradas, siguiendo %d.",
            response.meta.get("titulo_interno"),
            len(urls_filtradas),
            len(urls_seleccionadas),
        )

        meta_detalle = {
            "libro_id": response.meta.get("libro_id"),
            "isbn": response.meta.get("isbn"),
            "titulo_interno": response.meta.get("titulo_interno"),
            "precio_interno": response.meta.get("precio_interno"),
        }

        for url in urls_seleccionadas:
            yield response.follow(
                url=url,
                callback=self.parse_detalle,
                meta=meta_detalle,
            )

    def parse_detalle(self, response: Response) -> Iterable[Any]:
        """Extrae precio, imagen, formas de pago y descripción detallada."""
        loader = CuspideItemLoader(response=response)

        # Título web
        loader.add_css("titulo_web", "h1.product-title::text")
        loader.add_xpath(
            "titulo_web", "//h1[contains(@class, 'product-title')]/text()"
        )
        loader.add_xpath(
            "titulo_web", "//h1[contains(@class, 'entry-title')]/text()"
        )

        # Precio
        loader.add_css(
            "precio", "p.price span.woocommerce-Price-amount bdi::text"
        )
        loader.add_css(
            "precio", "p.price ins span.woocommerce-Price-amount bdi::text"
        )
        loader.add_css("precio", "p.price span.woocommerce-Price-amount::text")
        loader.add_css(
            "precio_texto", "p.price span.woocommerce-Price-amount bdi::text"
        )
        loader.add_css(
            "precio_texto", "p.price span.woocommerce-Price-amount::text"
        )

        # URL de la imagen
        loader.add_css(
            "url_img", "img.wp-post-image::attr(data-large_image)"
        )
        loader.add_css("url_img", "img.wp-post-image::attr(data-src)")
        loader.add_css("url_img", "img.wp-post-image::attr(src)")

        # Formas de pago
        xpath_medios = (
            "//*[contains(text(), 'Medios de pago')]"
            "/following::ul[1]/li/text()"
        )
        loader.add_xpath("formas_pago", xpath_medios)
        loader.add_css("formas_pago", "#contentPaymentsPopUp li::text")
        loader.add_css("formas_pago", ".payments-methods::text")
        loader.add_css("formas_pago", ".price-installments::text")

        # Descripción detallada
        loader.add_css(
            "descripcion", ".product-section .panel.entry-content p::text"
        )
        loader.add_css("descripcion", "#tab-description p::text")
        loader.add_css(
            "descripcion",
            ".woocommerce-product-details__short-description p::text",
        )
        loader.add_css("descripcion", ".panel.entry-content::text")

        # Metadatos internos
        loader.add_value("libro_id", response.meta.get("libro_id"))
        loader.add_value("isbn", response.meta.get("isbn"))
        loader.add_value(
            "titulo_interno", response.meta.get("titulo_interno")
        )
        loader.add_value(
            "precio_interno", response.meta.get("precio_interno")
        )
        loader.add_value("url_web", response.url)
        loader.add_value(
            "fecha_extraccion",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        yield loader.load_item()
