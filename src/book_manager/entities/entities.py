# -*- coding: utf-8 -*-
"""Entidades del sistema Book Manager.

Ejercicio 02: Definir las clases entidad necesarias para el uso del sistema
(Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock, CotizacionDolar).

Los modelos heredan de :class:`EntidadBase` y utilizan Pydantic para la
validación automática de datos. Se aplica encapsulación mediante atributos
privados, propiedades de solo lectura y métodos que controlan el estado
interno de cada entidad.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
)


class EntidadBase(BaseModel):
    """Entidad base con el identificador común a todas las entidades."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(ge=1, description="Identificador único de la entidad.")


class Genero(EntidadBase):
    """Categoría literaria a la que pertenece un libro (novela, ensayo, etc.)."""

    nombre: str = Field(min_length=3, max_length=50)
    descripcion: str = Field(default="", max_length=200)

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, valor: str) -> str:
        """Normaliza el nombre quitando los espacios en blanco de los bordes."""
        nombre = valor.strip()
        if not nombre:
            raise ValueError("El nombre del género no puede estar vacío.")
        return nombre


class Editorial(EntidadBase):
    """Proveedor/distribuidora que provee los libros a la librería."""

    nombre: str = Field(min_length=3, max_length=100)

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, valor: str) -> str:
        """Normaliza el nombre quitando los espacios en blanco de los bordes."""
        nombre = valor.strip()
        if not nombre:
            raise ValueError("El nombre de la editorial no puede estar vacío.")
        return nombre


class Moneda(EntidadBase):
    """Moneda en la que se puede expresar un precio (ARS, USD, etc.)."""

    codigo: str = Field(min_length=3, max_length=3, description="Código ISO 4217.")
    nombre: str = Field(min_length=3, max_length=50, description="Nombre de la moneda.")
    simbolo: str = Field(min_length=1, max_length=5, description="Símbolo de la moneda.")

    @field_validator("codigo")
    @classmethod
    def _codigo_mayuscula(cls, valor: str) -> str:
        """Normaliza el código de moneda a mayúsculas."""
        return valor.upper()

    @field_validator("simbolo")
    @classmethod
    def _simbolo_no_vacio(cls, valor: str) -> str:
        """Normaliza el símbolo quitando los espacios en blanco de los bordes."""
        simbolo = valor.strip()
        if not simbolo:
            raise ValueError("El símbolo de la moneda no puede estar vacío.")
        return simbolo


class TipoCotizacion(EntidadBase):
    """Tipo de cotización del dólar (Oficial, Blue, MEP, etc.)."""

    nombre: str = Field(min_length=3, max_length=50)
    descripcion: str = Field(default="", max_length=200)

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, valor: str) -> str:
        """Normaliza el nombre quitando los espacios en blanco de los bordes."""
        nombre = valor.strip()
        if not nombre:
            raise ValueError("El nombre del tipo de cotización no puede estar vacío.")
        return nombre


class Libro(EntidadBase):
    """Representa cada título del catálogo de la librería."""

    isbn: str = Field(min_length=10, max_length=17, description="ISBN de 10 o 13 dígitos.")
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=150)
    anio_publicacion: Optional[int] = Field(
        default=None, ge=0, le=date.today().year
    )
    editorial_id: int = Field(ge=1, description="Referencia a la entidad Editorial.")
    generos_ids: list[int] = Field(
        default_factory=list, description="Referencias a las entidades Genero."
    )
    descripcion: str = Field(default="", max_length=500)

    _activo: bool = PrivateAttr(default=True)

    @field_validator("isbn")
    @classmethod
    def _isbn_valido(cls, valor: str) -> str:
        """Normaliza el ISBN quitando guiones y valida que sea de 10 o 13 dígitos."""
        isbn = valor.replace("-", "").replace(" ", "").strip()
        if not isbn.isdigit() or len(isbn) not in (10, 13):
            raise ValueError("El ISBN debe contener 10 o 13 dígitos numéricos.")
        return isbn

    @field_validator("generos_ids")
    @classmethod
    def _generos_ids_validos(cls, valores: list[int]) -> list[int]:
        """Valida que los IDs de género sean positivos y no estén duplicados."""
        if any(valor < 1 for valor in valores):
            raise ValueError("Los IDs de género deben ser positivos.")
        if len(set(valores)) != len(valores):
            raise ValueError("Un libro no puede repetir el mismo género.")
        return valores

    @property
    def referencia_bibliografica(self) -> str:
        """Referencia legible del libro para mostrar al usuario."""
        return f"{self.titulo} - {self.autor} (ISBN: {self.isbn})"

    @property
    def activo(self) -> bool:
        """Estado de alta del libro en el catálogo (solo lectura)."""
        return self._activo

    def desactivar(self) -> None:
        """Da de baja el libro del catálogo."""
        self._activo = False

    def activar(self) -> None:
        """Da de alta el libro en el catálogo."""
        self._activo = True


class Precio(EntidadBase):
    """Valor monetario asociado a un libro en una moneda determinada."""

    libro_id: int = Field(ge=1, description="Referencia a la entidad Libro.")
    moneda_id: int = Field(ge=1, description="Referencia a la entidad Moneda.")
    valor: Decimal = Field(gt=0, description="Valor del precio, mayor a cero.")
    fecha: date = Field(default_factory=date.today, description="Fecha del precio.")

    @model_validator(mode="after")
    def _fecha_no_futura(self) -> "Precio":
        """Valida que la fecha del precio no sea futura."""
        if self.fecha > date.today():
            raise ValueError("La fecha del precio no puede ser futura.")
        return self


class Stock(EntidadBase):
    """Cantidad disponible de cada libro en el inventario."""

    libro_id: int = Field(ge=1, description="Referencia a la entidad Libro.")
    cantidad: int = Field(ge=0, description="Cantidad de unidades disponibles.")

    @property
    def disponible(self) -> bool:
        """Indica si hay unidades disponibles del libro."""
        return self.cantidad > 0

    def ajustar_cantidad(self, delta: int) -> None:
        """Modifica la cantidad de stock de forma encapsulada.

        Args:
            delta (int): Variación de unidades. Positivo ingresa stock,
                negativo lo egresa.

        Raises:
            ValueError: Si el resultado de la operación fuera negativo.
        """
        nueva_cantidad = self.cantidad + delta
        if nueva_cantidad < 0:
            raise ValueError(
                f"No hay stock suficiente: {self.cantidad} unidades disponibles."
            )
        self.cantidad = nueva_cantidad


class CotizacionDolar(EntidadBase):
    """Registro histórico de las cotizaciones del dólar por tipo y fecha."""

    tipo_id: int = Field(ge=1, description="Referencia a la entidad TipoCotizacion.")
    fecha: date = Field(default_factory=date.today, description="Fecha de la cotización.")
    valor_compra: Decimal = Field(gt=0, description="Valor de compra del dólar.")
    valor_venta: Decimal = Field(gt=0, description="Valor de venta del dólar.")

    @property
    def spread(self) -> Decimal:
        """Diferencia entre el valor de venta y el de compra (solo lectura)."""
        return self.valor_venta - self.valor_compra

    @model_validator(mode="after")
    def _validar_cotizacion(self) -> "CotizacionDolar":
        """Valida la fecha y la consistencia entre el valor de compra y venta."""
        if self.fecha > date.today():
            raise ValueError("La fecha de la cotización no puede ser futura.")
        if self.valor_venta < self.valor_compra:
            raise ValueError("El valor de venta no puede ser menor al valor de compra.")
        return self
