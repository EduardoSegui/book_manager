# -*- coding: utf-8 -*-
"""Modelos ORM de SQLAlchemy para el sistema Book Manager.

Ejercicio 04: Creación de las tablas del sistema con tipos de datos y relaciones.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM."""
    pass


# Tabla de asociación para la relación muchos a muchos entre Libro y Genero
class LibroGenero(Base):
    """Asociación entre Libro y Genero (muchos a muchos)."""

    __tablename__ = "libro_genero"

    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), primary_key=True
    )
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos.id", ondelete="CASCADE"), primary_key=True
    )


class Genero(Base):
    """Género literario."""

    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), default="", nullable=False)

    # Relación inversa
    libros: Mapped[list["Libro"]] = relationship(
        secondary="libro_genero", back_populates="generos"
    )


class Editorial(Base):
    """Editorial o distribuidora."""

    __tablename__ = "editoriales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Relación inversa
    libros: Mapped[list["Libro"]] = relationship(back_populates="editorial")


class Moneda(Base):
    """Moneda (código ISO 4217)."""

    __tablename__ = "monedas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    simbolo: Mapped[str] = mapped_column(String(5), nullable=False)

    # Relaciones inversas
    precios: Mapped[list["Precio"]] = relationship(back_populates="moneda")


class TipoCotizacion(Base):
    """Tipo de cotización del dólar (Oficial, Blue, MEP, etc.)."""

    __tablename__ = "tipos_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), default="", nullable=False)

    # Relaciones inversas
    cotizaciones: Mapped[list["CotizacionDolar"]] = relationship(
        back_populates="tipo", cascade="all, delete-orphan"
    )


class Libro(Base):
    """Libro del catálogo."""

    __tablename__ = "libros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    isbn: Mapped[str] = mapped_column(String(17), unique=True, nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    autor: Mapped[str] = mapped_column(String(150), nullable=False)
    anio_publicacion: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    editorial_id: Mapped[int] = mapped_column(
        ForeignKey("editoriales.id", ondelete="RESTRICT"), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relaciones
    editorial: Mapped["Editorial"] = relationship(back_populates="libros")
    generos: Mapped[list["Genero"]] = relationship(
        secondary="libro_genero", back_populates="libros"
    )
    precios: Mapped[list["Precio"]] = relationship(
        back_populates="libro", cascade="all, delete-orphan"
    )
    stock: Mapped[Optional["Stock"]] = relationship(
        back_populates="libro", uselist=False, cascade="all, delete-orphan"
    )


class Precio(Base):
    """Precio de un libro en una moneda."""

    __tablename__ = "precios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), nullable=False
    )
    moneda_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id", ondelete="RESTRICT"), nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)

    # Relaciones
    libro: Mapped["Libro"] = relationship(back_populates="precios")
    moneda: Mapped["Moneda"] = relationship(back_populates="precios")


class Stock(Base):
    """Stock de un libro."""

    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relación
    libro: Mapped["Libro"] = relationship(back_populates="stock")


class CotizacionDolar(Base):
    """Cotización histórica del dólar por tipo y fecha."""

    __tablename__ = "cotizaciones_dolar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_cotizacion.id", ondelete="CASCADE"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    valor_compra: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    valor_venta: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    # Constraint único: un tipo de cotización por fecha
    __table_args__ = (
        UniqueConstraint("tipo_id", "fecha", name="uq_tipo_fecha"),
    )

    # Relación
    tipo: Mapped["TipoCotizacion"] = relationship(back_populates="cotizaciones")