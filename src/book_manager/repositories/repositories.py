# -*- coding: utf-8 -*-
"""Repositorios del sistema Book Manager.

Ejercicio 03: Clases responsables de la persistencia de datos.
Todas las clases implementan su CRUD completo
(Create/Read/Update/Delete / Alta/Lectura/Modificación/Borrado).
"""

import abc
from datetime import date
from typing import Generic, List, Optional, TypeVar

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    EntidadBase,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)


# ---------------------------------------------------------------------------
# Interfaces abstractas
# ---------------------------------------------------------------------------

class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios que manejan entidades con operaciones CRUD básicas."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una nueva entidad en el repositorio.

        Args:
            entidad (T): La entidad a crear.

        Returns:
            T: La entidad creada.

        Raises:
            ValueError: Si ya existe una entidad con el mismo ID.
        """
        pass

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a leer.

        Returns:
            Optional[T]: La entidad si se encuentra, None en caso contrario.
        """
        pass

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        """Lee todas las entidades del repositorio.

        Returns:
            List[T]: Una lista de todas las entidades.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.

        Args:
            entidad (T): La entidad a actualizar (debe tener un ID existente).

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a eliminar.

        Returns:
            bool: True si la entidad fue eliminada, False si no se encontró.
        """
        pass


class IRepositorioStock(abc.ABC):
    """Interfaz para repositorios del tipo Stock."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro de stock.

        Args:
            stock (Stock): El objeto Stock a crear.

        Returns:
            Stock: El objeto Stock creado.

        Raises:
            ValueError: Si ya existe un registro de stock para el mismo libro.
        """
        pass

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Lee un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock.

        Returns:
            Optional[Stock]: El objeto Stock si se encuentra, None en caso contrario.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza un registro de stock existente.

        Args:
            stock (Stock): El objeto Stock a actualizar (debe tener un libro_id existente).

        Returns:
            Stock: El objeto Stock actualizado.

        Raises:
            ValueError: Si no se encuentra el stock para actualizar.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        """Elimina un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock a eliminar.

        Returns:
            bool: True si el stock fue eliminado, False si no se encontró.
        """
        pass


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para repositorios del tipo CotizacionDolar."""

    @abc.abstractmethod
    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una nueva cotización de dólar.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a crear.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar creado.

        Raises:
            ValueError: Si ya existe una cotización para el mismo tipo y fecha.
        """
        pass

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: date) -> Optional[CotizacionDolar]:
        """Lee una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización (e.g., 'Oficial', 'Blue').
            fecha (date): La fecha de la cotización.

        Returns:
            Optional[CotizacionDolar]: La cotización si se encuentra, None en caso contrario.
        """
        pass

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de cotizaciones para un tipo específico.

        Args:
            tipo_id (int): El ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Una lista de cotizaciones históricas para el tipo dado.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza una cotización de dólar existente.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a actualizar.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar actualizado.
        """
        pass

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        """Elimina una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (date): La fecha de la cotización a eliminar.

        Returns:
            bool: True si la cotización fue eliminada, False si no se encontró.
        """
        pass


# ---------------------------------------------------------------------------
# Implementaciones concretas — CRUD genérico en memoria
# ---------------------------------------------------------------------------

class RepositorioGenero(IRepositorio[Genero]):
    """Repositorio en memoria para la entidad Genero."""

    def __init__(self) -> None:
        self._datos: dict[int, Genero] = {}

    def crear(self, entidad: Genero) -> Genero:
        if entidad.id in self._datos:
            raise ValueError(f"Ya existe un Genero con el ID {entidad.id}.")
        self._datos[entidad.id] = entidad
        return entidad

    def leer_por_id(self, id: int) -> Optional[Genero]:
        return self._datos.get(id)

    def leer_todos(self) -> List[Genero]:
        return list(self._datos.values())

    def actualizar(self, entidad: Genero) -> Genero:
        if entidad.id not in self._datos:
            raise ValueError(f"No existe un Genero con el ID {entidad.id} para actualizar.")
        self._datos[entidad.id] = entidad
        return entidad

    def eliminar(self, id: int) -> bool:
        if id not in self._datos:
            return False
        del self._datos[id]
        return True


class RepositorioEditorial(IRepositorio[Editorial]):
    """Repositorio en memoria para la entidad Editorial."""

    def __init__(self) -> None:
        self._datos: dict[int, Editorial] = {}

    def crear(self, entidad: Editorial) -> Editorial:
        if entidad.id in self._datos:
            raise ValueError(f"Ya existe una Editorial con el ID {entidad.id}.")
        self._datos[entidad.id] = entidad
        return entidad

    def leer_por_id(self, id: int) -> Optional[Editorial]:
        return self._datos.get(id)

    def leer_todos(self) -> List[Editorial]:
        return list(self._datos.values())

    def actualizar(self, entidad: Editorial) -> Editorial:
        if entidad.id not in self._datos:
            raise ValueError(f"No existe una Editorial con el ID {entidad.id} para actualizar.")
        self._datos[entidad.id] = entidad
        return entidad

    def eliminar(self, id: int) -> bool:
        if id not in self._datos:
            return False
        del self._datos[id]
        return True


class RepositorioMoneda(IRepositorio[Moneda]):
    """Repositorio en memoria para la entidad Moneda."""

    def __init__(self) -> None:
        self._datos: dict[int, Moneda] = {}

    def crear(self, entidad: Moneda) -> Moneda:
        if entidad.id in self._datos:
            raise ValueError(f"Ya existe una Moneda con el ID {entidad.id}.")
        self._datos[entidad.id] = entidad
        return entidad

    def leer_por_id(self, id: int) -> Optional[Moneda]:
        return self._datos.get(id)

    def leer_todos(self) -> List[Moneda]:
        return list(self._datos.values())

    def actualizar(self, entidad: Moneda) -> Moneda:
        if entidad.id not in self._datos:
            raise ValueError(f"No existe una Moneda con el ID {entidad.id} para actualizar.")
        self._datos[entidad.id] = entidad
        return entidad

    def eliminar(self, id: int) -> bool:
        if id not in self._datos:
            return False
        del self._datos[id]
        return True


class RepositorioTipoCotizacion(IRepositorio[TipoCotizacion]):
    """Repositorio en memoria para la entidad TipoCotizacion."""

    def __init__(self) -> None:
        self._datos: dict[int, TipoCotizacion] = {}

    def crear(self, entidad: TipoCotizacion) -> TipoCotizacion:
        if entidad.id in self._datos:
            raise ValueError(f"Ya existe un TipoCotizacion con el ID {entidad.id}.")
        self._datos[entidad.id] = entidad
        return entidad

    def leer_por_id(self, id: int) -> Optional[TipoCotizacion]:
        return self._datos.get(id)

    def leer_todos(self) -> List[TipoCotizacion]:
        return list(self._datos.values())

    def actualizar(self, entidad: TipoCotizacion) -> TipoCotizacion:
        if entidad.id not in self._datos:
            raise ValueError(f"No existe un TipoCotizacion con el ID {entidad.id} para actualizar.")
        self._datos[entidad.id] = entidad
        return entidad

    def eliminar(self, id: int) -> bool:
        if id not in self._datos:
            return False
        del self._datos[id]
        return True


class RepositorioLibro(IRepositorio[Libro]):
    """Repositorio en memoria para la entidad Libro."""

    def __init__(self) -> None:
        self._datos: dict[int, Libro] = {}

    def crear(self, entidad: Libro) -> Libro:
        if entidad.id in self._datos:
            raise ValueError(f"Ya existe un Libro con el ID {entidad.id}.")
        self._datos[entidad.id] = entidad
        return entidad

    def leer_por_id(self, id: int) -> Optional[Libro]:
        return self._datos.get(id)

    def leer_todos(self) -> List[Libro]:
        return list(self._datos.values())

    def actualizar(self, entidad: Libro) -> Libro:
        if entidad.id not in self._datos:
            raise ValueError(f"No existe un Libro con el ID {entidad.id} para actualizar.")
        self._datos[entidad.id] = entidad
        return entidad

    def eliminar(self, id: int) -> bool:
        if id not in self._datos:
            return False
        del self._datos[id]
        return True


class RepositorioPrecio(IRepositorio[Precio]):
    """Repositorio en memoria para la entidad Precio."""

    def __init__(self) -> None:
        self._datos: dict[int, Precio] = {}

    def crear(self, entidad: Precio) -> Precio:
        if entidad.id in self._datos:
            raise ValueError(f"Ya existe un Precio con el ID {entidad.id}.")
        self._datos[entidad.id] = entidad
        return entidad

    def leer_por_id(self, id: int) -> Optional[Precio]:
        return self._datos.get(id)

    def leer_todos(self) -> List[Precio]:
        return list(self._datos.values())

    def actualizar(self, entidad: Precio) -> Precio:
        if entidad.id not in self._datos:
            raise ValueError(f"No existe un Precio con el ID {entidad.id} para actualizar.")
        self._datos[entidad.id] = entidad
        return entidad

    def eliminar(self, id: int) -> bool:
        if id not in self._datos:
            return False
        del self._datos[id]
        return True


# ---------------------------------------------------------------------------
# Repositorios especializados — Stock y CotizacionDolar
# ---------------------------------------------------------------------------

class RepositorioStock(IRepositorioStock):
    """Repositorio en memoria para la entidad Stock (acceso por libro_id)."""

    def __init__(self) -> None:
        self._datos: dict[int, Stock] = {}

    def crear(self, stock: Stock) -> Stock:
        if stock.libro_id in self._datos:
            raise ValueError(f"Ya existe un Stock para el libro con ID {stock.libro_id}.")
        self._datos[stock.libro_id] = stock
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        return self._datos.get(libro_id)

    def actualizar(self, stock: Stock) -> Stock:
        if stock.libro_id not in self._datos:
            raise ValueError(f"No existe un Stock para el libro con ID {stock.libro_id}.")
        self._datos[stock.libro_id] = stock
        return stock

    def eliminar(self, libro_id: int) -> bool:
        if libro_id not in self._datos:
            return False
        del self._datos[libro_id]
        return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio en memoria para la entidad CotizacionDolar (acceso por tipo_id + fecha)."""

    def __init__(self) -> None:
        self._datos: dict[tuple[int, date], CotizacionDolar] = {}

    def _clave(self, tipo_id: int, fecha: date) -> tuple[int, date]:
        return (tipo_id, fecha)

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        clave = self._clave(cotizacion.tipo_id, cotizacion.fecha)
        if clave in self._datos:
            raise ValueError(
                f"Ya existe una CotizacionDolar para el tipo {cotizacion.tipo_id} "
                f"en la fecha {cotizacion.fecha}."
            )
        self._datos[clave] = cotizacion
        return cotizacion

    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: date) -> Optional[CotizacionDolar]:
        return self._datos.get(self._clave(tipo_id, fecha))

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        return [c for (t, _), c in self._datos.items() if t == tipo_id]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        clave = self._clave(cotizacion.tipo_id, cotizacion.fecha)
        if clave not in self._datos:
            raise ValueError(
                f"No existe una CotizacionDolar para el tipo {cotizacion.tipo_id} "
                f"en la fecha {cotizacion.fecha}."
            )
        self._datos[clave] = cotizacion
        return cotizacion

    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        clave = self._clave(tipo_id, fecha)
        if clave not in self._datos:
            return False
        del self._datos[clave]
        return True
