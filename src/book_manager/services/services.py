# -*- coding: utf-8 -*-
"""Servicios del sistema Book Manager.

Ejercicio 04: Clases responsables de la lógica de negocio que se aplica a cada
operación (CRUD) de las entidades. Los repositorios se inyectan por constructor
y la persistencia se delega a la capa de repositorios.
"""

import abc
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable, Generic, List, Optional, TypeVar

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
from book_manager.repositories.repositories import (
    IRepositorio,
    IRepositorioCotizacionDolar,
    IRepositorioStock,
)

T = TypeVar("T", bound=EntidadBase)

CODIGO_MONEDA_BASE = "ARS"
CODIGO_MONEDA_DOLAR = "USD"
DOS_DECIMALES = Decimal("0.01")
MAXIMO_DETALLES = 3


# --- Utilidades internas de validación y cálculo ---

def _normalizar_texto(valor: str) -> str:
    """Normaliza un texto para compararlo sin distinguir mayúsculas ni espacios."""
    return " ".join(valor.split()).casefold()


def _exigir_existencia(entidad: Optional[T], id: int, etiqueta: str) -> T:
    """Devuelve la entidad solicitada o falla si no está registrada."""
    if entidad is None:
        raise ValueError(f"No existe {etiqueta} con el ID {id}.")
    return entidad


def _exigir_unicidad(
    existentes: List[T],
    campo: str,
    valor: str,
    etiqueta: str,
    id_actual: int,
) -> None:
    """Valida que el valor de un campo no esté repetido en otra entidad."""
    clave = _normalizar_texto(valor)
    for entidad in existentes:
        if entidad.id == id_actual:
            continue
        if _normalizar_texto(getattr(entidad, campo)) == clave:
            raise ValueError(f"Ya existe {etiqueta} con {campo} '{valor}'.")


def _exigir_referencias(
    referencias: List[int],
    existe: Callable[[int], bool],
    etiqueta: str,
) -> None:
    """Valida que todas las entidades referenciadas existan."""
    inexistentes = [
        str(referencia) for referencia in referencias if not existe(referencia)
    ]
    if inexistentes:
        raise ValueError(
            f"Referencias a {etiqueta} inexistentes: ID(s) {', '.join(inexistentes)}."
        )


def _resumen(detalles: List[str]) -> str:
    """Resume una lista de detalles para los mensajes de error."""
    texto = "; ".join(detalles[:MAXIMO_DETALLES])
    restantes = len(detalles) - MAXIMO_DETALLES
    return f"{texto} y {restantes} más" if restantes > 0 else texto


def _precio_vigente(
    repositorio: IRepositorio[Precio], libro_id: int, moneda_id: int
) -> Optional[Precio]:
    """Obtiene el último precio cargado de un libro en una moneda."""
    precios = [
        precio for precio in repositorio.leer_todos()
        if precio.libro_id == libro_id and precio.moneda_id == moneda_id
    ]
    if not precios:
        return None
    return max(precios, key=lambda precio: (precio.fecha, precio.id))


def _cotizacion_aplicable(
    repositorio: IRepositorioCotizacionDolar, tipo_id: int, fecha: Optional[date]
) -> Optional[CotizacionDolar]:
    """Obtiene la cotización de un tipo, exacta o la más reciente anterior."""
    if fecha is not None:
        exacta = repositorio.leer_por_tipo_y_fecha(tipo_id, fecha)
        if exacta is not None:
            return exacta
        candidatos = [cotizacion
                      for cotizacion in repositorio.leer_historico_por_tipo(tipo_id)
                      if cotizacion.fecha <= fecha]
    else:
        candidatos = repositorio.leer_historico_por_tipo(tipo_id)
    if not candidatos:
        return None
    return max(candidatos, key=lambda cotizacion: cotizacion.fecha)


def _convertir(
    valor: Decimal, cotizacion: CotizacionDolar, origen: str, destino: str
) -> Decimal:
    """Convierte un valor entre dólares y pesos con el valor de venta del dólar."""
    if origen == destino:
        return valor.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)
    if origen == CODIGO_MONEDA_DOLAR and destino == CODIGO_MONEDA_BASE:
        convertido = valor * cotizacion.valor_venta
    elif origen == CODIGO_MONEDA_BASE and destino == CODIGO_MONEDA_DOLAR:
        convertido = valor / cotizacion.valor_venta
    else:
        raise ValueError(
            f"La conversión de {origen} a {destino} no está soportada. Solo se "
            f"admiten conversiones entre {CODIGO_MONEDA_DOLAR} y {CODIGO_MONEDA_BASE}."
        )
    return convertido.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


# --- Interfaz genérica de los servicios de catálogo ---

class IServicio(abc.ABC, Generic[T]):
    """Interfaz para servicios que exponen el CRUD con lógica de negocio."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una entidad validando las reglas de negocio asociadas."""
        pass

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad por su ID, o None si no existe."""
        pass

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        """Lee todas las entidades."""
        pass

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad validando las reglas de negocio asociadas."""
        pass

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina una entidad por su ID si no está en uso por otra entidad."""
        pass


# --- Base común de los servicios de catálogo ---

class ServicioBase(IServicio[T]):
    """CRUD genérico con las validaciones de negocio como punto de extensión.

    Cada subclase declara su etiqueta y sus campos únicos, y sobrescribe los
    métodos ``_validar_*`` para agregar sus reglas sin repetir el CRUD.
    """

    _etiqueta: str = "la entidad"
    _campos_unicos: tuple[str, ...] = ()

    def __init__(self, repositorio: IRepositorio[T]) -> None:
        """Inicializa el servicio con el repositorio de su entidad."""
        self._repositorio = repositorio

    def crear(self, entidad: T) -> T:
        """Crea la entidad validando unicidad y reglas de negocio."""
        self._exigir_campos_unicos(entidad)
        self._validar_creacion(entidad)
        return self._repositorio.crear(entidad)

    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad por su ID."""
        return self._repositorio.leer_por_id(id)

    def leer_todos(self) -> List[T]:
        """Lee todas las entidades."""
        return self._repositorio.leer_todos()

    def leer_por_campo(self, campo: str, valor: str) -> Optional[T]:
        """Busca una entidad por un campo de texto, sin distinguir mayúsculas."""
        clave = _normalizar_texto(valor)
        for entidad in self._repositorio.leer_todos():
            if _normalizar_texto(getattr(entidad, campo)) == clave:
                return entidad
        return None

    def actualizar(self, entidad: T) -> T:
        """Actualiza la entidad validando su existencia, unicidad y reglas."""
        self._exigir_existente(entidad.id)
        self._exigir_campos_unicos(entidad)
        self._validar_actualizacion(entidad)
        return self._repositorio.actualizar(entidad)

    def eliminar(self, id: int) -> bool:
        """Elimina la entidad validando que no esté en uso."""
        self._validar_eliminacion(self._exigir_existente(id))
        return self._repositorio.eliminar(id)

    def _exigir_existente(self, id: int) -> T:
        """Devuelve la entidad registrada con ese ID o falla."""
        return _exigir_existencia(
            self._repositorio.leer_por_id(id), id, self._etiqueta
        )

    def _exigir_campos_unicos(self, entidad: T) -> None:
        """Valida que los campos declarados como únicos no estén repetidos."""
        for campo in self._campos_unicos:
            _exigir_unicidad(
                self._repositorio.leer_todos(),
                campo,
                getattr(entidad, campo),
                self._etiqueta,
                entidad.id,
            )

    def _validar_creacion(self, entidad: T) -> None:
        """Punto de extensión para las validaciones previas al alta."""

    def _validar_actualizacion(self, entidad: T) -> None:
        """Punto de extensión para las validaciones previas a la modificación."""

    def _validar_eliminacion(self, entidad: T) -> None:
        """Punto de extensión para las validaciones previas al borrado."""


# --- Servicios de las entidades de catálogo ---

class ServicioGenero(ServicioBase[Genero]):
    """Servicio con la lógica de negocio de los géneros del catálogo."""

    _etiqueta = "el género"
    _campos_unicos = ("nombre",)

    def __init__(
        self, repositorio: IRepositorio[Genero], repositorio_libro: IRepositorio[Libro]
    ) -> None:
        """Inicializa el servicio con los repositorios de género y de libros."""
        super().__init__(repositorio)
        self._repositorio_libro = repositorio_libro

    def _validar_eliminacion(self, entidad: Genero) -> None:
        """Impide borrar un género que está asociado a libros del catálogo."""
        en_uso = [libro.referencia_bibliografica
                  for libro in self._repositorio_libro.leer_todos()
                  if entidad.id in libro.generos_ids]
        if en_uso:
            raise ValueError(
                f"{self._etiqueta.capitalize()} '{entidad.nombre}' no se puede "
                f"eliminar porque está asociado a {len(en_uso)} libro(s): "
                f"{_resumen(en_uso)}."
            )


class ServicioEditorial(ServicioBase[Editorial]):
    """Servicio con la lógica de negocio de las editoriales."""

    _etiqueta = "la editorial"
    _campos_unicos = ("nombre",)

    def __init__(
        self,
        repositorio: IRepositorio[Editorial],
        repositorio_libro: IRepositorio[Libro],
    ) -> None:
        """Inicializa el servicio con los repositorios de editorial y de libros."""
        super().__init__(repositorio)
        self._repositorio_libro = repositorio_libro

    def _validar_eliminacion(self, entidad: Editorial) -> None:
        """Impide borrar una editorial que tiene libros publicados."""
        en_uso = [libro.referencia_bibliografica
                  for libro in self._repositorio_libro.leer_todos()
                  if libro.editorial_id == entidad.id]
        if en_uso:
            raise ValueError(
                f"{self._etiqueta.capitalize()} '{entidad.nombre}' no se puede "
                f"eliminar porque publica {len(en_uso)} libro(s): "
                f"{_resumen(en_uso)}."
            )


class ServicioMoneda(ServicioBase[Moneda]):
    """Servicio con la lógica de negocio de las monedas."""

    _etiqueta = "la moneda"
    _campos_unicos = ("codigo", "nombre")

    def _validar_eliminacion(self, entidad: Moneda) -> None:
        """Impide borrar las monedas necesarias para cotizar precios."""
        if entidad.codigo in (CODIGO_MONEDA_BASE, CODIGO_MONEDA_DOLAR):
            raise ValueError(
                f"La moneda '{entidad.codigo}' no se puede eliminar porque es "
                "necesaria para la cotización de precios."
            )


class ServicioTipoCotizacion(ServicioBase[TipoCotizacion]):
    """Servicio con la lógica de negocio de los tipos de cotización del dólar."""

    _etiqueta = "el tipo de cotización"
    _campos_unicos = ("nombre",)

    def __init__(
        self,
        repositorio: IRepositorio[TipoCotizacion],
        repositorio_cotizacion: IRepositorioCotizacionDolar,
    ) -> None:
        """Inicializa el servicio con los repositorios de tipo y de cotización."""
        super().__init__(repositorio)
        self._repositorio_cotizacion = repositorio_cotizacion

    def _validar_eliminacion(self, entidad: TipoCotizacion) -> None:
        """Impide borrar un tipo de cotización que tiene historial cargado."""
        cotizaciones = self._repositorio_cotizacion.leer_historico_por_tipo(entidad.id)
        if cotizaciones:
            raise ValueError(
                f"El tipo de cotización '{entidad.nombre}' no se puede eliminar "
                f"porque tiene {len(cotizaciones)} cotización(es) cargada(s)."
            )


# --- Servicio de libros ---

class ServicioLibro(ServicioBase[Libro]):
    """Servicio con la lógica de negocio del catálogo de libros."""

    _etiqueta = "el libro"

    def __init__(
        self,
        repositorio: IRepositorio[Libro],
        repositorio_genero: IRepositorio[Genero],
        repositorio_editorial: IRepositorio[Editorial],
        repositorio_precio: IRepositorio[Precio],
        repositorio_stock: IRepositorioStock,
    ) -> None:
        """Inicializa el servicio con los repositorios que valida y consulta."""
        super().__init__(repositorio)
        self._repositorio_genero = repositorio_genero
        self._repositorio_editorial = repositorio_editorial
        self._repositorio_precio = repositorio_precio
        self._repositorio_stock = repositorio_stock

    def buscar(self, texto: str) -> List[Libro]:
        """Busca libros por título, autor o ISBN, ordenados por título."""
        clave = _normalizar_texto(texto)
        coincidencias = [
            libro for libro in self._repositorio.leer_todos()
            if clave and (clave in _normalizar_texto(libro.titulo)
                          or clave in _normalizar_texto(libro.autor)
                          or clave in libro.isbn)
        ]
        return sorted(coincidencias, key=lambda libro: libro.titulo.casefold())

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Busca un libro por su ISBN, con o sin guiones."""
        return self.leer_por_campo("isbn", isbn.replace("-", "").replace(" ", ""))

    def leer_activos(self) -> List[Libro]:
        """Lista los libros dados de alta en el catálogo."""
        return [libro for libro in self._repositorio.leer_todos() if libro.activo]

    def leer_inactivos(self) -> List[Libro]:
        """Lista los libros dados de baja del catálogo."""
        return [libro for libro in self._repositorio.leer_todos() if not libro.activo]

    def dar_de_baja(self, id: int) -> Libro:
        """Saca un libro del catálogo conservando su historial."""
        return self._cambiar_estado(id, activar=False)

    def dar_de_alta(self, id: int) -> Libro:
        """Incorpora un libro al catálogo."""
        return self._cambiar_estado(id, activar=True)

    def _cambiar_estado(self, id: int, activar: bool) -> Libro:
        """Cambia el estado de alta del libro validando la transición."""
        libro = self._exigir_existente(id)
        if libro.activo == activar:
            estado = "alta" if activar else "baja"
            raise ValueError(f"El libro '{libro.titulo}' ya está dado de {estado}.")
        if activar:
            libro.activar()
        else:
            libro.desactivar()
        return self._repositorio.actualizar(libro)

    def _validar_creacion(self, entidad: Libro) -> None:
        """Valida editorial, géneros e ISBN antes del alta."""
        self._validar_referencias(entidad)
        self._validar_isbn(entidad.isbn, entidad.id)

    def _validar_actualizacion(self, entidad: Libro) -> None:
        """Valida editorial, géneros e ISBN antes de la modificación."""
        self._validar_creacion(entidad)

    def _validar_eliminacion(self, entidad: Libro) -> None:
        """Impide borrar un libro que tiene precios o stock asociado."""
        precios = [precio for precio in self._repositorio_precio.leer_todos()
                   if precio.libro_id == entidad.id]
        if precios or self._repositorio_stock.leer_por_libro(entidad.id) is not None:
            raise ValueError(
                f"El libro '{entidad.titulo}' no se puede eliminar porque tiene "
                f"{len(precios)} precio(s) y/o stock asociado. Si solo se quiere "
                "sacarlo del catálogo, utilice la baja lógica."
            )

    def _validar_referencias(self, entidad: Libro) -> None:
        """Valida que la editorial y los géneros referenciados existan."""
        if self._repositorio_editorial.leer_por_id(entidad.editorial_id) is None:
            raise ValueError(
                f"No existe la editorial con el ID {entidad.editorial_id}."
            )
        _exigir_referencias(
            entidad.generos_ids,
            lambda id: self._repositorio_genero.leer_por_id(id) is not None,
            "género",
        )

    def _validar_isbn(self, isbn: str, id_actual: int) -> None:
        """Valida que el ISBN no esté registrado en otro libro."""
        existente = self.leer_por_isbn(isbn)
        if existente is not None and existente.id != id_actual:
            raise ValueError(
                f"El ISBN {isbn} ya está registrado en "
                f"'{existente.referencia_bibliografica}'."
            )


# --- Servicio de cotizaciones del dólar ---

class ServicioCotizacionDolar:
    """Servicio con la lógica de negocio de las cotizaciones del dólar.

    Permite consultar la cotización vigente de un tipo, recorrer el histórico y
    convertir valores entre dólares y pesos.
    """

    def __init__(
        self,
        repositorio: IRepositorioCotizacionDolar,
        repositorio_tipo: IRepositorio[TipoCotizacion],
        repositorio_moneda: IRepositorio[Moneda],
    ) -> None:
        """Inicializa el servicio con los repositorios de cotización, tipo y moneda."""
        self._repositorio = repositorio
        self._repositorio_tipo = repositorio_tipo
        self._repositorio_moneda = repositorio_moneda

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una cotización validando el tipo de cotización referenciado."""
        self._exigir_existente(cotizacion.tipo_id)
        return self._repositorio.crear(cotizacion)

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza la cotización cargada para un tipo y una fecha."""
        self._exigir_existente(cotizacion.tipo_id)
        return self._repositorio.actualizar(cotizacion)

    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        """Elimina la cotización de un tipo en una fecha determinada."""
        self._exigir_existente(tipo_id)
        return self._repositorio.eliminar(tipo_id, fecha)

    def leer_todos(self) -> List[CotizacionDolar]:
        """Lee todas las cotizaciones ordenadas por fecha y tipo."""
        cotizaciones = []
        for tipo in self._repositorio_tipo.leer_todos():
            cotizaciones.extend(self._repositorio.leer_historico_por_tipo(tipo.id))
        return sorted(cotizaciones, key=lambda c: (c.fecha, c.tipo_id))

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de cotizaciones de un tipo en orden cronológico."""
        self._exigir_existente(tipo_id)
        return sorted(
            self._repositorio.leer_historico_por_tipo(tipo_id),
            key=lambda cotizacion: cotizacion.fecha,
        )

    def ultima_cotizacion(self, tipo_id: int) -> Optional[CotizacionDolar]:
        """Devuelve la cotización más reciente cargada para un tipo."""
        return _cotizacion_aplicable(self._repositorio, tipo_id, None)

    def convertir(
        self,
        valor: Decimal,
        moneda_origen: str,
        moneda_destino: str,
        tipo_id: int,
        fecha: Optional[date] = None,
    ) -> Decimal:
        """Convierte un valor entre las monedas del sistema.

        Se usa la cotización del tipo indicado; si no se pasa fecha se aplica
        la cotización más reciente del tipo.
        """
        origen = self._leer_moneda(moneda_origen)
        destino = self._leer_moneda(moneda_destino)
        cotizacion = _cotizacion_aplicable(self._repositorio, tipo_id, fecha)
        if cotizacion is None:
            raise ValueError(
                f"El tipo de cotización {tipo_id} no tiene cotizaciones cargadas."
            )
        return _convertir(valor, cotizacion, origen.codigo, destino.codigo)

    def _exigir_existente(self, tipo_id: int) -> TipoCotizacion:
        """Devuelve el tipo de cotización registrado con ese ID o falla."""
        return _exigir_existencia(
            self._repositorio_tipo.leer_por_id(tipo_id), tipo_id, "el tipo de cotización"
        )

    def _leer_moneda(self, codigo: str) -> Moneda:
        """Busca una moneda por su código exigiendo que esté registrada.

        Raises:
            ValueError: Si la moneda no está registrada en el sistema.
        """
        clave = _normalizar_texto(codigo)
        for moneda in self._repositorio_moneda.leer_todos():
            if _normalizar_texto(moneda.codigo) == clave:
                return moneda
        raise ValueError(f"La moneda '{codigo}' no está registrada en el sistema.")


# --- Servicio de precios ---

class ServicioPrecio(ServicioBase[Precio]):
    """Servicio con la lógica de negocio de los precios de los libros."""

    _etiqueta = "el precio"

    def __init__(
        self,
        repositorio: IRepositorio[Precio],
        repositorio_libro: IRepositorio[Libro],
        repositorio_moneda: IRepositorio[Moneda],
        repositorio_cotizacion: IRepositorioCotizacionDolar,
    ) -> None:
        """Inicializa el servicio con los repositorios que valida y consulta."""
        super().__init__(repositorio)
        self._repositorio_libro = repositorio_libro
        self._repositorio_moneda = repositorio_moneda
        self._repositorio_cotizacion = repositorio_cotizacion

    def leer_por_libro(self, libro_id: int) -> List[Precio]:
        """Lista los precios cargados de un libro ordenados por moneda y fecha.

        Raises:
            ValueError: Si el libro no existe.
        """
        _exigir_existencia(
            self._repositorio_libro.leer_por_id(libro_id), libro_id, "el libro"
        )
        precios = [precio for precio in self._repositorio.leer_todos()
                   if precio.libro_id == libro_id]
        return sorted(precios, key=lambda precio: (precio.moneda_id, precio.fecha))

    def precio_vigente(self, libro_id: int, moneda_id: int) -> Optional[Precio]:
        """Devuelve el último precio cargado de un libro en una moneda."""
        return _precio_vigente(self._repositorio, libro_id, moneda_id)

    def cotizar(
        self,
        libro_id: int,
        moneda_origen_id: int,
        moneda_destino_id: int,
        tipo_id: int,
        fecha: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Cotiza el precio vigente de un libro en otra moneda.

        Devuelve None si el libro no tiene precio cargado en la moneda de origen.
        """
        origen = self._leer_moneda(moneda_origen_id)
        destino = self._leer_moneda(moneda_destino_id)
        precio = self.precio_vigente(libro_id, moneda_origen_id)
        if precio is None:
            return None
        cotizacion = _cotizacion_aplicable(self._repositorio_cotizacion, tipo_id, fecha)
        if cotizacion is None:
            raise ValueError(
                f"El tipo de cotización {tipo_id} no tiene cotizaciones cargadas."
            )
        return _convertir(precio.valor, cotizacion, origen.codigo, destino.codigo)

    def _leer_moneda(self, moneda_id: int) -> Moneda:
        """Devuelve la moneda registrada con ese ID o falla."""
        return _exigir_existencia(
            self._repositorio_moneda.leer_por_id(moneda_id), moneda_id, "la moneda"
        )

    def _validar_creacion(self, entidad: Precio) -> None:
        """Valida que el libro y la moneda referenciados existan."""
        _exigir_existencia(
            self._repositorio_libro.leer_por_id(entidad.libro_id),
            entidad.libro_id,
            "el libro",
        )
        self._leer_moneda(entidad.moneda_id)

    def _validar_actualizacion(self, entidad: Precio) -> None:
        """Valida que el libro y la moneda referenciados existan."""
        self._validar_creacion(entidad)


# --- Servicio de stock ---

class ServicioStock:
    """Servicio con la lógica de negocio del inventario de libros.

    Gestiona los ingresos y egresos de unidades y, combinando el stock con los
    precios vigentes y la cotización del dólar, permite valorar el inventario.
    """

    def __init__(
        self,
        repositorio: IRepositorioStock,
        repositorio_libro: IRepositorio[Libro],
        repositorio_precio: IRepositorio[Precio],
        repositorio_moneda: IRepositorio[Moneda],
        repositorio_cotizacion: IRepositorioCotizacionDolar,
    ) -> None:
        """Inicializa el servicio con los repositorios que valida y consulta."""
        self._repositorio = repositorio
        self._repositorio_libro = repositorio_libro
        self._repositorio_precio = repositorio_precio
        self._repositorio_moneda = repositorio_moneda
        self._repositorio_cotizacion = repositorio_cotizacion

    def crear(self, stock: Stock) -> Stock:
        """Crea un registro de stock validando el libro referenciado."""
        self._exigir_libro(stock.libro_id)
        return self._repositorio.crear(stock)

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Lee el registro de stock de un libro, o None si no existe."""
        return self._repositorio.leer_por_libro(libro_id)

    def leer_todos(self) -> List[Stock]:
        """Lista el stock registrado de todos los libros del catálogo."""
        registros = []
        for libro in self._repositorio_libro.leer_todos():
            stock = self._repositorio.leer_por_libro(libro.id)
            if stock is not None:
                registros.append(stock)
        return registros

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza el stock de un libro validando su existencia."""
        self._exigir_libro(stock.libro_id)
        return self._repositorio.actualizar(stock)

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock de un libro que ya no tiene unidades disponibles.

        Raises:
            ValueError: Si el libro no tiene stock registrado o le quedan
                unidades disponibles.
        """
        stock = _exigir_existencia(
            self._repositorio.leer_por_libro(libro_id),
            libro_id,
            "el registro de stock del libro",
        )
        if stock.disponible:
            raise ValueError(
                f"No se puede eliminar el stock del libro {libro_id} porque aún "
                f"quedan {stock.cantidad} unidad(es). Egreselas antes de eliminarlo."
            )
        return self._repositorio.eliminar(libro_id)

    def ingresar(self, libro_id: int, cantidad: int) -> Stock:
        """Registra el stock de un libro o incrementa el existente.

        Raises:
            ValueError: Si la cantidad no es positiva o el libro no existe.
        """
        self._exigir_cantidad(cantidad, "ingresar")
        stock = self._repositorio.leer_por_libro(libro_id)
        if stock is None:
            registros = self.leer_todos()
            nuevo_id = max((registro.id for registro in registros), default=0) + 1
            return self.crear(
                Stock(id=nuevo_id, libro_id=libro_id, cantidad=cantidad)
            )
        stock.ajustar_cantidad(cantidad)
        return self._repositorio.actualizar(stock)

    def egresar(self, libro_id: int, cantidad: int) -> Stock:
        """Descuenta unidades del stock de un libro.

        Raises:
            ValueError: Si la cantidad no es positiva, el libro no tiene stock
                cargado o no hay unidades suficientes.
        """
        self._exigir_cantidad(cantidad, "egresar")
        stock = _exigir_existencia(
            self._repositorio.leer_por_libro(libro_id),
            libro_id,
            "el registro de stock del libro",
        )
        stock.ajustar_cantidad(-cantidad)
        return self._repositorio.actualizar(stock)

    def sin_disponibilidad(self) -> List[Stock]:
        """Lista los registros de stock agotados."""
        return [stock for stock in self.leer_todos() if not stock.disponible]

    def con_stock_bajo(self, cantidad_minima: int) -> List[Stock]:
        """Lista los registros de stock que están en o por debajo de un mínimo."""
        return [stock for stock in self.leer_todos() if stock.cantidad <= cantidad_minima]

    def valor_inventario(
        self,
        moneda_origen_id: int,
        moneda_destino_id: int,
        tipo_id: int,
        fecha: Optional[date] = None,
    ) -> Decimal:
        """Calcula el valor del inventario multiplicando stock por precio vigente.

        Los libros sin precio cargado en la moneda de origen se omiten del cálculo.
        """
        origen = self._leer_moneda(moneda_origen_id)
        destino = self._leer_moneda(moneda_destino_id)
        cotizacion = _cotizacion_aplicable(self._repositorio_cotizacion, tipo_id, fecha)
        if cotizacion is None:
            raise ValueError(
                f"El tipo de cotización {tipo_id} no tiene cotizaciones cargadas."
            )
        total = Decimal("0")
        for stock in self.leer_todos():
            precio = _precio_vigente(
                self._repositorio_precio, stock.libro_id, moneda_origen_id
            )
            if precio is not None:
                valor = Decimal(stock.cantidad) * precio.valor
                total += _convertir(valor, cotizacion, origen.codigo, destino.codigo)
        return total.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)

    def _leer_moneda(self, moneda_id: int) -> Moneda:
        """Devuelve la moneda registrada con ese ID o falla."""
        return _exigir_existencia(
            self._repositorio_moneda.leer_por_id(moneda_id), moneda_id, "la moneda"
        )

    def _exigir_libro(self, libro_id: int) -> Libro:
        """Devuelve el libro registrado con ese ID o falla."""
        return _exigir_existencia(
            self._repositorio_libro.leer_por_id(libro_id), libro_id, "el libro"
        )

    @staticmethod
    def _exigir_cantidad(cantidad: int, operacion: str) -> None:
        """Valida que la cantidad a mover sea mayor a cero."""
        if cantidad <= 0:
            raise ValueError(f"La cantidad a {operacion} debe ser mayor a cero.")
