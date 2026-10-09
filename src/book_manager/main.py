# -*- coding: utf-8 -*-
"""Punto de entrada del sistema Book Manager.

Ejercicio 07: Crear el archivo main.py que se encarga de ejecutar el sistema.
Se encargar de armar la composición del sistema (repositorios, servicios y
consola) y de ponerlo en marcha.
"""

from book_manager.preload_data.preload_data import cargar_todos_los_datos
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
)
from book_manager.ui.console import Consola


def _crear_repositorios() -> dict:
    """Crea las instancias de los repositorios del sistema."""
    return {
        "genero": RepositorioGenero(),
        "editorial": RepositorioEditorial(),
        "moneda": RepositorioMoneda(),
        "tipo_cotizacion": RepositorioTipoCotizacion(),
        "libro": RepositorioLibro(),
        "precio": RepositorioPrecio(),
        "stock": RepositorioStock(),
        "cotizacion": RepositorioCotizacionDolar(),
    }


def _crear_servicios(repos: dict) -> Consola:
    """Crea los servicios inyectando los repositorios y arma la consola."""
    return Consola(
        servicio_genero=ServicioGenero(repos["genero"], repos["libro"]),
        servicio_editorial=ServicioEditorial(
            repos["editorial"], repos["libro"]
        ),
        servicio_moneda=ServicioMoneda(repos["moneda"]),
        servicio_tipo_cotizacion=ServicioTipoCotizacion(
            repos["tipo_cotizacion"], repos["cotizacion"]
        ),
        servicio_libro=ServicioLibro(
            repos["libro"],
            repos["genero"],
            repos["editorial"],
            repos["precio"],
            repos["stock"],
        ),
        servicio_precio=ServicioPrecio(
            repos["precio"],
            repos["libro"],
            repos["moneda"],
            repos["cotizacion"],
        ),
        servicio_stock=ServicioStock(
            repos["stock"],
            repos["libro"],
            repos["precio"],
            repos["moneda"],
            repos["cotizacion"],
        ),
        servicio_cotizacion=ServicioCotizacionDolar(
            repos["cotizacion"],
            repos["tipo_cotizacion"],
            repos["moneda"],
        ),
    )


def main(import_default_data: bool = True) -> None:
    """Ejecuta el sistema Book Manager.

    Args:
        import_default_data: Si es True, precarga los datos de los archivos CSV
            de migrations/csv antes de iniciar la consola.
    """
    repos = _crear_repositorios()

    if import_default_data:
        resultados = cargar_todos_los_datos(
            repo_genero=repos["genero"],
            repo_editorial=repos["editorial"],
            repo_moneda=repos["moneda"],
            repo_tipo_cotizacion=repos["tipo_cotizacion"],
            repo_libro=repos["libro"],
            repo_precio=repos["precio"],
            repo_stock=repos["stock"],
            repo_cotizacion=repos["cotizacion"],
        )
        total = sum(resultados.values())
        print(f"Datos de precarga cargados: {total} registros en total.")
        for entidad, cantidad in resultados.items():
            print(f"  - {entidad}: {cantidad}")

    _crear_servicios(repos).ejecutar()


if __name__ == "__main__":
    main()
