# -*- coding: utf-8 -*-
"""Repositorios del sistema Book Manager con persistencia en base de datos.

Ejercicio 03: Clases responsables de la persistencia de datos con su CRUD
completo (Create/Read/Update/Delete / Alta/Lectura/Modificación/Borrado).

Ejercicio 06: Se modifican los repositorios para que toda la persistencia se
realice sobre la base de datos relacional a través de SQLAlchemy. Las entidades
del dominio (Pydantic) se traducen a los modelos ORM y viceversa, de modo que
los servicios y la consola sigan trabajando con las entidades de negocio.
"""

import abc
from datetime import date
from typing import ClassVar, Generic, List, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB
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
from book_manager.models import models as orm

T = TypeVar("T", bound=EntidadBase)
M = TypeVar("M")


# ---------------------------------------------------------------------------
# Traducción entre entidades de dominio (Pydantic) y modelos ORM (SQLAlchemy)
# ---------------------------------------------------------------------------

def _entidad_desde_orm(clase_entidad: type[T], registro: M) -> T:
    """Construye una entidad de dominio a partir de una instancia ORM.

    Copia por nombre los valores de las columnas del modelo ORM a los campos
    de la entidad. Las relaciones especiales (por ejemplo los géneros de un
    libro) se resuelven en los repositorios que las necesitan.
    """
    datos = {
        columna.name: getattr(registro, columna.name)
        for columna in registro.__table__.columns
    }
    return clase_entidad(**datos)


def _copiar_a_orm(registro: M, entidad: T) -> M:
    """Vuelca los campos de una entidad de dominio sobre una instancia ORM.

    Solo copia las columnas cuyo nombre coincide con un atributo de la
    entidad; el identificador se asigna únicamente si la entidad lo trae.
    """
    for columna in registro.__table__.columns:
        if columna.name == "id":
            continue
        if hasattr(entidad, columna.name):
            setattr(registro, columna.name, getattr(entidad, columna.name))
    if entidad.id:
        registro.id = entidad.id
    return registro


def _confirmar(sesion: Session) -> None:
    """Fuerza la escritura de los cambios, traduciendo errores de integridad.

    Raises:
        ValueError: Si la operación viola una restricción de unicidad o de
            integridad referencial de la base de datos.
    """
    try:
        sesion.flush()
    except IntegrityError as error:
        raise ValueError(
            "No se pudo guardar el registro: ya existe un dato duplicado o "
            "alguna de las referencias indicadas no es válida."
        ) from error


# ---------------------------------------------------------------------------
# Interfaces abstractas
# ---------------------------------------------------------------------------

class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios con operaciones CRUD básicas."""

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
            Optional[Stock]: El stock si se encuentra, None en caso contrario.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza un registro de stock existente.

        Args:
            stock (Stock): El Stock a actualizar (con libro_id existente).

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
    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: date
    ) -> Optional[CotizacionDolar]:
        """Lee una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (date): La fecha de la cotización.

        Returns:
            Optional[CotizacionDolar]: La cotización si se encuentra, None.
        """
        pass

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de cotizaciones para un tipo específico.

        Args:
            tipo_id (int): El ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Lista histórica del tipo de cotización.
        """
        pass

    @abc.abstractmethod
    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza una cotización de dólar existente.

        Args:
            cotizacion (CotizacionDolar): La cotización a actualizar.

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
# Repositorio genérico con persistencia en base de datos
# ---------------------------------------------------------------------------

class RepositorioBase(IRepositorio[T], Generic[T, M]):
    """Repositorio genérico que concentra el CRUD sobre la base de datos.

    Cada repositorio concreto solo declara el modelo ORM (``_modelo``) y la
    entidad de dominio (``_clase_entidad``); la traducción por defecto copia
    los campos cuyo nombre coincide. Los repositorios con relaciones o claves
    especiales sobrescriben los métodos de traducción.
    """

    _modelo: ClassVar[type]
    _clase_entidad: ClassVar[type]

    def _a_orm(
        self, entidad: T, sesion: Session, instancia: Optional[M] = None
    ) -> M:
        """Convierte una entidad de dominio en una instancia ORM."""
        registro = instancia if instancia is not None else self._modelo()
        return _copiar_a_orm(registro, entidad)

    def _a_entidad(self, registro: M) -> T:
        """Convierte una instancia ORM en una entidad de dominio."""
        return _entidad_desde_orm(self._clase_entidad, registro)

    def crear(self, entidad: T) -> T:
        """Crea (o actualiza, si el ID existe) la entidad."""
        with ConexionDB.sesion() as sesion:
            registro = (
                sesion.get(self._modelo, entidad.id) if entidad.id else None
            )
            if registro is None:
                registro = self._a_orm(entidad, sesion)
                sesion.add(registro)
            else:
                self._a_orm(entidad, sesion, registro)
            _confirmar(sesion)
            entidad.id = registro.id
            return self._a_entidad(registro)

    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad por su ID desde la base de datos."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.get(self._modelo, id)
            return None if registro is None else self._a_entidad(registro)

    def leer_todos(self) -> List[T]:
        """Lee todas las entidades ordenadas por ID."""
        with ConexionDB.sesion() as sesion:
            registros = sesion.scalars(
                select(self._modelo).order_by(self._modelo.id)
            ).all()
            return [self._a_entidad(registro) for registro in registros]

    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en la base de datos."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.get(self._modelo, entidad.id)
            if registro is None:
                raise ValueError(
                    f"No existe un registro con el ID {entidad.id} "
                    f"para actualizar."
                )
            self._a_orm(entidad, sesion, registro)
            _confirmar(sesion)
            return self._a_entidad(registro)

    def eliminar(self, id: int) -> bool:
        """Elimina una entidad por su ID de la base de datos."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.get(self._modelo, id)
            if registro is None:
                return False
            sesion.delete(registro)
            return True


# ---------------------------------------------------------------------------
# Repositorios de las entidades de catálogo
# ---------------------------------------------------------------------------

class RepositorioGenero(RepositorioBase[Genero, orm.Genero]):
    """Repositorio para la entidad Genero."""

    _modelo = orm.Genero
    _clase_entidad = Genero


class RepositorioEditorial(RepositorioBase[Editorial, orm.Editorial]):
    """Repositorio para la entidad Editorial."""

    _modelo = orm.Editorial
    _clase_entidad = Editorial


class RepositorioMoneda(RepositorioBase[Moneda, orm.Moneda]):
    """Repositorio para la entidad Moneda."""

    _modelo = orm.Moneda
    _clase_entidad = Moneda


class RepositorioTipoCotizacion(
    RepositorioBase[TipoCotizacion, orm.TipoCotizacion]
):
    """Repositorio para la entidad TipoCotizacion."""

    _modelo = orm.TipoCotizacion
    _clase_entidad = TipoCotizacion


class RepositorioPrecio(RepositorioBase[Precio, orm.Precio]):
    """Repositorio para la entidad Precio."""

    _modelo = orm.Precio
    _clase_entidad = Precio


class RepositorioLibro(RepositorioBase[Libro, orm.Libro]):
    """Repositorio para la entidad Libro.

    Resuelve la relación muchos a muchos con los géneros y reconstruye el
    estado de alta del libro (``activo``) al traducir desde/hacia el ORM.
    """

    _modelo = orm.Libro
    _clase_entidad = Libro

    def _a_orm(
        self, entidad: Libro, sesion: Session,
        instancia: Optional[orm.Libro] = None,
    ) -> orm.Libro:
        """Convierte el libro y asigna los géneros referenciados."""
        registro = super()._a_orm(entidad, sesion, instancia)
        registro.generos = self._resolver_generos(sesion, entidad.generos_ids)
        return registro

    def _a_entidad(self, registro: orm.Libro) -> Libro:
        """Reconstruye el libro incluyendo sus géneros y su estado de alta."""
        libro = Libro(
            id=registro.id,
            isbn=registro.isbn,
            titulo=registro.titulo,
            autor=registro.autor,
            anio_publicacion=registro.anio_publicacion,
            editorial_id=registro.editorial_id,
            generos_ids=[genero.id for genero in registro.generos],
            descripcion=registro.descripcion,
        )
        libro._activo = registro.activo
        return libro

    @staticmethod
    def _resolver_generos(
        sesion: Session, generos_ids: List[int]
    ) -> List[orm.Genero]:
        """Busca las instancias ORM de los géneros indicados."""
        if not generos_ids:
            return []
        return list(
            sesion.scalars(
                select(orm.Genero).where(orm.Genero.id.in_(generos_ids))
            )
        )


# ---------------------------------------------------------------------------
# Repositorios especializados — Stock y CotizacionDolar
# ---------------------------------------------------------------------------

class RepositorioStock(IRepositorioStock):
    """Repositorio de Stock (acceso por libro_id) con base de datos."""

    def crear(self, stock: Stock) -> Stock:
        """Crea el stock de un libro o actualiza el existente (idempotente)."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.scalar(
                select(orm.Stock).where(orm.Stock.libro_id == stock.libro_id)
            )
            if registro is None:
                registro = _copiar_a_orm(orm.Stock(), stock)
                sesion.add(registro)
            else:
                _copiar_a_orm(registro, stock)
            _confirmar(sesion)
            stock.id = registro.id
            return _entidad_desde_orm(Stock, registro)

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Lee el stock de un libro por su ID."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.scalar(
                select(orm.Stock).where(orm.Stock.libro_id == libro_id)
            )
            return None if registro is None else _entidad_desde_orm(
                Stock, registro
            )

    def leer_todos(self) -> List[Stock]:
        """Lee todos los registros de stock ordenados por ID."""
        with ConexionDB.sesion() as sesion:
            registros = sesion.scalars(
                select(orm.Stock).order_by(orm.Stock.id)
            ).all()
            return [
                _entidad_desde_orm(Stock, registro)
                for registro in registros
            ]

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza el stock del libro referenciado."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.scalar(
                select(orm.Stock).where(orm.Stock.libro_id == stock.libro_id)
            )
            if registro is None:
                raise ValueError(
                    f"No existe un Stock para el libro con ID "
                    f"{stock.libro_id}."
                )
            _copiar_a_orm(registro, stock)
            _confirmar(sesion)
            return _entidad_desde_orm(Stock, registro)

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock de un libro por su ID."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.scalar(
                select(orm.Stock).where(orm.Stock.libro_id == libro_id)
            )
            if registro is None:
                return False
            sesion.delete(registro)
            return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio de CotizacionDolar (acceso por tipo_id + fecha)."""

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea o actualiza la cotización de un tipo en una fecha."""
        with ConexionDB.sesion() as sesion:
            registro = (
                sesion.get(orm.CotizacionDolar, cotizacion.id)
                if cotizacion.id else None
            )
            if registro is None:
                registro = sesion.scalar(
                    select(orm.CotizacionDolar).where(
                        orm.CotizacionDolar.tipo_id == cotizacion.tipo_id,
                        orm.CotizacionDolar.fecha == cotizacion.fecha,
                    )
                )
            if registro is None:
                registro = _copiar_a_orm(orm.CotizacionDolar(), cotizacion)
                sesion.add(registro)
            else:
                _copiar_a_orm(registro, cotizacion)
            _confirmar(sesion)
            cotizacion.id = registro.id
            return _entidad_desde_orm(CotizacionDolar, registro)

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: date
    ) -> Optional[CotizacionDolar]:
        """Lee la cotización de un tipo en una fecha."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.scalar(
                select(orm.CotizacionDolar).where(
                    orm.CotizacionDolar.tipo_id == tipo_id,
                    orm.CotizacionDolar.fecha == fecha,
                )
            )
            return (
                None
                if registro is None
                else _entidad_desde_orm(CotizacionDolar, registro)
            )

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de un tipo ordenado cronológicamente."""
        with ConexionDB.sesion() as sesion:
            registros = sesion.scalars(
                select(orm.CotizacionDolar)
                .where(orm.CotizacionDolar.tipo_id == tipo_id)
                .order_by(orm.CotizacionDolar.fecha)
            ).all()
            return [
                _entidad_desde_orm(CotizacionDolar, registro)
                for registro in registros
            ]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza la cotización de un tipo en una fecha."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.scalar(
                select(orm.CotizacionDolar).where(
                    orm.CotizacionDolar.tipo_id == cotizacion.tipo_id,
                    orm.CotizacionDolar.fecha == cotizacion.fecha,
                )
            )
            if registro is None:
                raise ValueError(
                    f"No existe una CotizacionDolar para el tipo "
                    f"{cotizacion.tipo_id} en la fecha "
                    f"{cotizacion.fecha}."
                )
            _copiar_a_orm(registro, cotizacion)
            _confirmar(sesion)
            return _entidad_desde_orm(CotizacionDolar, registro)

    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        """Elimina la cotización de un tipo en una fecha."""
        with ConexionDB.sesion() as sesion:
            registro = sesion.scalar(
                select(orm.CotizacionDolar).where(
                    orm.CotizacionDolar.tipo_id == tipo_id,
                    orm.CotizacionDolar.fecha == fecha,
                )
            )
            if registro is None:
                return False
            sesion.delete(registro)
            return True
