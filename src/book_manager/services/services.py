# -*- coding: utf-8 -*-
"""Servicios del sistema Book Manager.

Ejercicio 04: Clases responsables de la lógica de negocio que se aplica a cada
operación (CRUD) de las entidades. Los repositorios se inyectan por constructor
y la persistencia se delega a la capa de repositorios.

Sprint 3 - Ejercicio 06: Las operaciones de los servicios se decoran con
``auditar`` para que toda alta, modificación, baja y operación relevante del
sistema quede registrada en la tabla de auditoría (acción, fecha y detalles).
"""

import abc
import csv
import json
import os
import urllib.request
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from dotenv import load_dotenv

from book_manager.audit.auditoria import auditar
from book_manager.entities.entities import (
    Auditoria,
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
    RepositorioCotizacionDolar,
    RepositorioMoneda,
    RepositorioTipoCotizacion,
)

T = TypeVar("T", bound=EntidadBase)

CODIGO_MONEDA_BASE = "ARS"
CODIGO_MONEDA_DOLAR = "USD"
DOS_DECIMALES = Decimal("0.01")
MAXIMO_DETALLES = 3


# --- Utilidades internas de validación y cálculo ---

def _normalizar_texto(valor: str) -> str:
    """Normaliza texto para comparar sin mayúsculas ni espacios."""
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


def _asignar_id_pendiente(entidad: T, existentes: List[T]) -> T:
    """Asigna el siguiente identificador libre si la entidad aún no lo tiene.

    Las altas construidas desde la consola usan ``id=0`` como marcador de
    "identificador pendiente"; en ese caso se le asigna el siguiente
    correlativo disponible. Si la entidad ya trae un identificador explícito
    (por ejemplo, la precarga desde CSV) se respeta tal cual.
    """
    if entidad.id != 0:
        return entidad
    entidad.id = max((otra.id for otra in existentes), default=0) + 1
    return entidad


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
            f"Referencias a {etiqueta} inexistentes: "
            f"ID(s) {', '.join(inexistentes)}."
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
    repositorio: IRepositorioCotizacionDolar,
    tipo_id: int,
    fecha: Optional[date],
) -> Optional[CotizacionDolar]:
    """Obtiene la cotización de un tipo, exacta o la más reciente anterior."""
    if fecha is not None:
        exacta = repositorio.leer_por_tipo_y_fecha(tipo_id, fecha)
        if exacta is not None:
            return exacta
        candidatos = [
            cotizacion
            for cotizacion in repositorio.leer_historico_por_tipo(tipo_id)
            if cotizacion.fecha <= fecha
        ]
    else:
        candidatos = repositorio.leer_historico_por_tipo(tipo_id)
    if not candidatos:
        return None
    return max(candidatos, key=lambda cotizacion: cotizacion.fecha)


def _convertir(
    valor: Decimal,
    cotizacion: CotizacionDolar,
    origen: str,
    destino: str,
) -> Decimal:
    """Convierte entre dólares y pesos usando valor de venta del dólar."""
    if origen == destino:
        return valor.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)
    if origen == CODIGO_MONEDA_DOLAR and destino == CODIGO_MONEDA_BASE:
        convertido = valor * cotizacion.valor_venta
    elif origen == CODIGO_MONEDA_BASE and destino == CODIGO_MONEDA_DOLAR:
        convertido = valor / cotizacion.valor_venta
    else:
        raise ValueError(
            f"La conversión de {origen} a {destino} no está soportada. "
            f"Solo se admiten conversiones entre {CODIGO_MONEDA_DOLAR} y "
            f"{CODIGO_MONEDA_BASE}."
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

    @auditar("crear")
    def crear(self, entidad: T) -> T:
        """Crea la entidad asignando ID y validando unicidad y reglas."""
        _asignar_id_pendiente(entidad, self._repositorio.leer_todos())
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
        """Busca una entidad por un campo de texto (sin mayúsculas)."""
        clave = _normalizar_texto(valor)
        for entidad in self._repositorio.leer_todos():
            if _normalizar_texto(getattr(entidad, campo)) == clave:
                return entidad
        return None

    @auditar("actualizar")
    def actualizar(self, entidad: T) -> T:
        """Actualiza la entidad validando su existencia, unicidad y reglas."""
        self._exigir_existente(entidad.id)
        self._exigir_campos_unicos(entidad)
        self._validar_actualizacion(entidad)
        return self._repositorio.actualizar(entidad)

    @auditar("eliminar")
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
        """Validaciones previas a la modificación."""

    def _validar_eliminacion(self, entidad: T) -> None:
        """Punto de extensión para las validaciones previas al borrado."""


# --- Servicios de las entidades de catálogo ---

class ServicioGenero(ServicioBase[Genero]):
    """Servicio con la lógica de negocio de los géneros del catálogo."""

    _etiqueta = "el género"
    _campos_unicos = ("nombre",)

    def __init__(
        self,
        repositorio: IRepositorio[Genero],
        repositorio_libro: IRepositorio[Libro],
    ) -> None:
        """Inicializa con repositorios de género y de libros."""
        super().__init__(repositorio)
        self._repositorio_libro = repositorio_libro

    def _validar_eliminacion(self, entidad: Genero) -> None:
        """Impide borrar un género que está asociado a libros del catálogo."""
        en_uso = [libro.referencia_bibliografica
                  for libro in self._repositorio_libro.leer_todos()
                  if entidad.id in libro.generos_ids]
        if en_uso:
            raise ValueError(
                f"{self._etiqueta.capitalize()} '{entidad.nombre}' no "
                f"se puede "
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
        """Inicializa con repositorios de editorial y de libros."""
        super().__init__(repositorio)
        self._repositorio_libro = repositorio_libro

    def _validar_eliminacion(self, entidad: Editorial) -> None:
        """Impide borrar una editorial que tiene libros publicados."""
        en_uso = [libro.referencia_bibliografica
                  for libro in self._repositorio_libro.leer_todos()
                  if libro.editorial_id == entidad.id]
        if en_uso:
            raise ValueError(
                f"{self._etiqueta.capitalize()} '{entidad.nombre}' no "
                f"se puede "
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
    """Servicio con la lógica de los tipos de cotización del dólar."""

    _etiqueta = "el tipo de cotización"
    _campos_unicos = ("nombre",)

    def __init__(
        self,
        repositorio: IRepositorio[TipoCotizacion],
        repositorio_cotizacion: IRepositorioCotizacionDolar,
    ) -> None:
        """Inicializa el servicio con los repositorios de tipo y cotización."""
        super().__init__(repositorio)
        self._repositorio_cotizacion = repositorio_cotizacion

    def _validar_eliminacion(self, entidad: TipoCotizacion) -> None:
        """Impide borrar un tipo de cotización que tiene historial cargado."""
        cotizaciones = self._repositorio_cotizacion.leer_historico_por_tipo(
            entidad.id)
        if cotizaciones:
            raise ValueError(
                f"El tipo de cotización '{entidad.nombre}' no se puede "
                f"eliminar "
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
        """Inicializa el servicio con los repositorios de validación."""
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
        return self.leer_por_campo(
            "isbn", isbn.replace("-", "").replace(" ", "")
        )

    def leer_activos(self) -> List[Libro]:
        """Lista los libros dados de alta en el catálogo."""
        return [
            libro for libro in self._repositorio.leer_todos() if libro.activo
        ]

    def leer_inactivos(self) -> List[Libro]:
        """Lista los libros dados de baja del catálogo."""
        return [
            libro for libro in self._repositorio.leer_todos()
            if not libro.activo
        ]

    @auditar("dar_de_baja")
    def dar_de_baja(self, id: int) -> Libro:
        """Saca un libro del catálogo conservando su historial."""
        return self._cambiar_estado(id, activar=False)

    @auditar("dar_de_alta")
    def dar_de_alta(self, id: int) -> Libro:
        """Incorpora un libro al catálogo."""
        return self._cambiar_estado(id, activar=True)

    def _cambiar_estado(self, id: int, activar: bool) -> Libro:
        """Cambia el estado de alta del libro validando la transición."""
        libro = self._exigir_existente(id)
        if libro.activo == activar:
            estado = "alta" if activar else "baja"
            raise ValueError(
                f"El libro '{libro.titulo}' ya está dado de {estado}.")
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
        stock = self._repositorio_stock.leer_por_libro(entidad.id)
        if precios or stock is not None:
            raise ValueError(
                f"El libro '{entidad.titulo}' no se puede eliminar "
                f"porque tiene {len(precios)} precio(s) y/o stock asociado. "
                f"Si solo se quiere "
                "sacarlo del catálogo, utilice la baja lógica."
            )

    def _validar_referencias(self, entidad: Libro) -> None:
        """Valida que la editorial y los géneros referenciados existan."""
        editorial = self._repositorio_editorial.leer_por_id(
            entidad.editorial_id
        )
        if editorial is None:
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

    _etiqueta = "la cotización"

    def __init__(
        self,
        repositorio: IRepositorioCotizacionDolar,
        repositorio_tipo: IRepositorio[TipoCotizacion],
        repositorio_moneda: IRepositorio[Moneda],
    ) -> None:
        """Inicializa el servicio con sus repositorios de cotización y tipo."""
        self._repositorio = repositorio
        self._repositorio_tipo = repositorio_tipo
        self._repositorio_moneda = repositorio_moneda

    @auditar("crear")
    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una cotización validando el tipo de cotización referenciado."""
        _asignar_id_pendiente(cotizacion, self.leer_todos())
        self._exigir_existente(cotizacion.tipo_id)
        return self._repositorio.crear(cotizacion)

    @auditar("actualizar")
    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza la cotización cargada para un tipo y una fecha."""
        self._exigir_existente(cotizacion.tipo_id)
        return self._repositorio.actualizar(cotizacion)

    @auditar("eliminar")
    def eliminar(self, tipo_id: int, fecha: date) -> bool:
        """Elimina la cotización de un tipo en una fecha determinada."""
        self._exigir_existente(tipo_id)
        return self._repositorio.eliminar(tipo_id, fecha)

    def leer_todos(self) -> List[CotizacionDolar]:
        """Lee todas las cotizaciones ordenadas por fecha y tipo."""
        cotizaciones = []
        for tipo in self._repositorio_tipo.leer_todos():
            cotizaciones.extend(
                self._repositorio.leer_historico_por_tipo(tipo.id))
        return sorted(cotizaciones, key=lambda c: (c.fecha, c.tipo_id))

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Lee el histórico de cotizaciones de un tipo en orden cronológico."""
        self._exigir_existente(tipo_id)
        return sorted(
            self._repositorio.leer_historico_por_tipo(tipo_id),
            key=lambda cotizacion: cotizacion.fecha,
        )

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: date
    ) -> Optional[CotizacionDolar]:
        """Devuelve la cotización de un tipo en una fecha específica."""
        self._exigir_existente(tipo_id)
        for cotizacion in self._repositorio.leer_historico_por_tipo(tipo_id):
            if cotizacion.fecha == fecha:
                return cotizacion
        return None

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
                f"El tipo de cotización {tipo_id} no tiene cotizaciones "
                f"cargadas."
            )
        return _convertir(valor, cotizacion, origen.codigo, destino.codigo)

    def _exigir_existente(self, tipo_id: int) -> TipoCotizacion:
        """Devuelve el tipo de cotización registrado con ese ID o falla."""
        return _exigir_existencia(
            self._repositorio_tipo.leer_por_id(
                tipo_id), tipo_id, "el tipo de cotización"
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
        raise ValueError(
            f"La moneda '{codigo}' no está registrada en el sistema.")

    @auditar("obtener")
    def obtener_cotizaciones(
        self, api_url: Optional[str] = None
    ) -> List[CotizacionDolar]:
        """Busca, descarga y registra las cotizaciones del dólar desde la API.

        Consulta el endpoint configurado en la variable de entorno API_URL (o
        DOLAR_API_URL / valor por defecto) o el especificado por parámetro,
        procesa las cotizaciones recibidas y las persiste en la base de datos
        para la fecha correspondiente. Si la cotización ya existe para esa
        fecha y tipo, actualiza los valores.

        Args:
            api_url (Optional[str]): URL alternativa de la API. Si no se
                proporciona, se toma de la variable de entorno API_URL.

        Returns:
            List[CotizacionDolar]: Lista de cotizaciones registradas o
                actualizadas en el sistema.

        Raises:
            ValueError: Si ocurre un error al conectar con la API, descargar
                los datos o procesar la respuesta.
        """
        if not api_url:
            load_dotenv()
            api_url = (
                os.getenv("API_URL")
                or os.getenv("DOLAR_API_URL")
                or "https://dolarapi.com/v1/dolares"
            )

        peticion = urllib.request.Request(
            api_url,
            headers={"User-Agent": "BookManager/1.0"},
        )
        try:
            with urllib.request.urlopen(peticion, timeout=15) as respuesta:
                contenido = respuesta.read().decode("utf-8")
                datos = json.loads(contenido)
        except Exception as error:
            raise ValueError(
                f"Error al consultar la API del dólar en '{api_url}': {error}"
            ) from error

        if not isinstance(datos, list):
            raise ValueError(
                "La respuesta de la API del dólar debe ser una lista "
                "de cotizaciones."
            )

        registradas: List[CotizacionDolar] = []
        for item in datos:
            if not isinstance(item, dict):
                continue

            nombre = str(item.get("nombre", "")).strip()
            casa = str(item.get("casa", "")).strip()
            compra_raw = item.get("compra")
            venta_raw = item.get("venta")
            fecha_raw = item.get("fechaActualizacion")

            if compra_raw is None or venta_raw is None:
                continue

            try:
                valor_compra = Decimal(str(compra_raw))
                valor_venta = Decimal(str(venta_raw))
            except Exception:
                continue

            if valor_compra <= Decimal("0") or valor_venta <= Decimal("0"):
                continue

            if valor_venta < valor_compra:
                valor_venta = valor_compra

            fecha = self._parsear_fecha_api(fecha_raw)
            tipo = self._buscar_o_crear_tipo(nombre, casa)

            existente = self._repositorio.leer_por_tipo_y_fecha(tipo.id, fecha)
            if existente is not None:
                cotizacion = CotizacionDolar(
                    id=existente.id,
                    tipo_id=tipo.id,
                    fecha=fecha,
                    valor_compra=valor_compra,
                    valor_venta=valor_venta,
                )
                guardada = self.actualizar(cotizacion)
            else:
                cotizacion = CotizacionDolar(
                    id=0,
                    tipo_id=tipo.id,
                    fecha=fecha,
                    valor_compra=valor_compra,
                    valor_venta=valor_venta,
                )
                guardada = self.crear(cotizacion)
            registradas.append(guardada)

        return registradas

    def _parsear_fecha_api(self, fecha_raw: Optional[str]) -> date:
        """Parsea la fecha devuelta por la API asegurando que no sea futura."""
        if not fecha_raw:
            return date.today()
        try:
            fecha_iso = str(fecha_raw).split("T")[0]
            fecha = date.fromisoformat(fecha_iso)
        except ValueError:
            fecha = date.today()

        if fecha > date.today():
            fecha = date.today()
        return fecha

    def _buscar_o_crear_tipo(self, nombre: str, casa: str) -> TipoCotizacion:
        """Busca el TipoCotizacion coincidente o lo crea si no existe."""
        tipos = self._repositorio_tipo.leer_todos()
        nombre_norm = _normalizar_texto(nombre)
        casa_norm = _normalizar_texto(casa)

        for tipo in tipos:
            if _normalizar_texto(tipo.nombre) == nombre_norm:
                return tipo

        alias = {
            "contadoconliqui": "ccl",
            "bolsa": "bolsa",
            "mep": "mep",
            "oficial": "oficial",
            "blue": "blue",
            "tarjeta": "tarjeta",
            "mayorista": "mayorista",
            "cripto": "cripto",
        }
        alias_nombre = alias.get(casa_norm)
        if alias_nombre:
            for tipo in tipos:
                if _normalizar_texto(tipo.nombre) == alias_nombre:
                    return tipo

        nombre_final = nombre if nombre else casa.capitalize()
        nuevo_tipo = TipoCotizacion(
            id=0,
            nombre=nombre_final[:50],
            descripcion=f"Cotización {nombre_final} obtenida vía API",
        )
        _asignar_id_pendiente(nuevo_tipo, tipos)
        return self._repositorio_tipo.crear(nuevo_tipo)


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
        """Inicializa el servicio con los repositorios de validación."""
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
        return sorted(
            precios, key=lambda precio: (precio.moneda_id, precio.fecha)
        )

    def precio_vigente(
        self, libro_id: int, moneda_id: int
    ) -> Optional[Precio]:
        """Devuelve el último precio cargado de un libro en una moneda."""
        return _precio_vigente(self._repositorio, libro_id, moneda_id)

    @auditar("cotizar")
    def cotizar(
        self,
        libro_id: int,
        moneda_origen_id: int,
        moneda_destino_id: int,
        tipo_id: int,
        fecha: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Cotiza el precio vigente de un libro en otra moneda.

        Devuelve None si el libro no tiene precio en la moneda de origen.
        """
        origen = self._leer_moneda(moneda_origen_id)
        destino = self._leer_moneda(moneda_destino_id)
        precio = self.precio_vigente(libro_id, moneda_origen_id)
        if precio is None:
            return None
        cotizacion = _cotizacion_aplicable(
            self._repositorio_cotizacion, tipo_id, fecha)
        if cotizacion is None:
            raise ValueError(
                f"El tipo de cotización {tipo_id} no tiene cotizaciones "
                f"cargadas."
            )
        return _convertir(
            precio.valor, cotizacion, origen.codigo, destino.codigo
        )

    def lista_precios_bimonetaria(
        self,
        moneda_destino_id: int,
        tipo_id: int,
        fecha: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Genera la lista de precios bimonetaria de los libros.

        Calcula para cada libro su precio vigente en pesos (ARS) y en la moneda
        destino seleccionada, cotizando mediante el tipo de cotización si no
        cuenta con precio directo cargado.

        Args:
            moneda_destino_id: ID de la moneda secundaria a comparar.
            tipo_id: ID del tipo de cotización a aplicar.
            fecha: Fecha opcional para la cotización histórica.

        Returns:
            List[Dict[str, Any]]: Lista de registros con el libro y los precios
                en ambas monedas.

        Raises:
            ValueError: Si la moneda destino no existe o es ARS, o si el tipo
                de cotización no existe.
        """
        destino = self._leer_moneda(moneda_destino_id)
        if destino.codigo == CODIGO_MONEDA_BASE:
            raise ValueError(
                f"La moneda de comparación debe ser distinta de "
                f"{CODIGO_MONEDA_BASE}."
            )

        moneda_base = next(
            (m for m in self._repositorio_moneda.leer_todos()
             if m.codigo == CODIGO_MONEDA_BASE),
            None,
        )
        if moneda_base is None:
            raise ValueError(
                f"No se encuentra registrada la moneda base "
                f"{CODIGO_MONEDA_BASE}."
            )

        cotizacion = _cotizacion_aplicable(
            self._repositorio_cotizacion, tipo_id, fecha
        )
        if cotizacion is None:
            raise ValueError(
                f"El tipo de cotización {tipo_id} no tiene cotizaciones "
                f"disponibles."
            )

        filas: List[Dict[str, Any]] = []
        for libro in self._repositorio_libro.leer_todos():
            precio_base = self.precio_vigente(libro.id, moneda_base.id)
            precio_destino = self.precio_vigente(libro.id, destino.id)

            valor_base = precio_base.valor if precio_base else None
            valor_destino = precio_destino.valor if precio_destino else None
            es_cotizado = False

            if valor_destino is None and valor_base is not None:
                try:
                    valor_destino = _convertir(
                        valor_base,
                        cotizacion,
                        moneda_base.codigo,
                        destino.codigo,
                    )
                    es_cotizado = True
                except ValueError:
                    valor_destino = None

            filas.append({
                "libro": libro,
                "moneda_base": moneda_base,
                "precio_base": valor_base,
                "moneda_destino": destino,
                "precio_destino": valor_destino,
                "cotizado": es_cotizado,
                "cotizacion": cotizacion,
            })
        return filas

    @auditar("exportar_csv")
    def exportar_precios_csv(
        self,
        ruta_archivo: str,
        tipo_id: Optional[int] = None,
        fecha: Optional[date] = None,
    ) -> int:
        """Exporta los precios vigentes de los libros a un archivo CSV.

        Incluye los precios directos y los calculados por conversión
        de cotización si se especifica el tipo de cotización.

        Args:
            ruta_archivo: Ruta o nombre del archivo CSV a generar.
            tipo_id: ID opcional del tipo de cotización para conversión.
            fecha: Fecha opcional para la cotización.

        Returns:
            int: Cantidad de filas de precios exportadas.

        Raises:
            ValueError: Si no hay libros o monedas cargadas en el sistema.
            OSError: Si ocurre un error al escribir el archivo.
        """
        libros = self._repositorio_libro.leer_todos()
        monedas = self._repositorio_moneda.leer_todos()
        if not libros:
            raise ValueError("No hay libros registrados en el catálogo.")
        if not monedas:
            raise ValueError("No hay monedas registradas en el sistema.")

        moneda_base = next(
            (m for m in monedas if m.codigo == CODIGO_MONEDA_BASE), None
        )
        cotizacion = (
            _cotizacion_aplicable(self._repositorio_cotizacion, tipo_id, fecha)
            if tipo_id is not None
            else None
        )

        carpeta = os.path.dirname(ruta_archivo)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)

        contador = 0
        with open(ruta_archivo, mode="w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow([
                "libro_id",
                "titulo",
                "autor",
                "isbn",
                "moneda_id",
                "codigo_moneda",
                "nombre_moneda",
                "simbolo",
                "precio",
                "tipo_precio",
                "fecha",
            ])

            for libro in libros:
                for moneda in monedas:
                    precio_reg = self.precio_vigente(libro.id, moneda.id)
                    if precio_reg is not None:
                        escritor.writerow([
                            libro.id,
                            libro.titulo,
                            libro.autor,
                            libro.isbn,
                            moneda.id,
                            moneda.codigo,
                            moneda.nombre,
                            moneda.simbolo,
                            f"{precio_reg.valor:.2f}",
                            "Directo",
                            str(precio_reg.fecha),
                        ])
                        contador += 1
                    elif (
                        moneda_base
                        and cotizacion
                        and moneda.codigo in (
                            CODIGO_MONEDA_BASE, CODIGO_MONEDA_DOLAR
                        )
                    ):
                        precio_base = self.precio_vigente(
                            libro.id, moneda_base.id
                        )
                        if precio_base is not None:
                            try:
                                valor_cot = _convertir(
                                    precio_base.valor,
                                    cotizacion,
                                    moneda_base.codigo,
                                    moneda.codigo,
                                )
                                escritor.writerow([
                                    libro.id,
                                    libro.titulo,
                                    libro.autor,
                                    libro.isbn,
                                    moneda.id,
                                    moneda.codigo,
                                    moneda.nombre,
                                    moneda.simbolo,
                                    f"{valor_cot:.2f}",
                                    "Cotizado",
                                    str(cotizacion.fecha),
                                ])
                                contador += 1
                            except ValueError:
                                pass
        return contador

    def _leer_moneda(self, moneda_id: int) -> Moneda:
        """Devuelve la moneda registrada con ese ID o falla."""
        return _exigir_existencia(
            self._repositorio_moneda.leer_por_id(
                moneda_id), moneda_id, "la moneda"
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

    _etiqueta = "el stock"

    def __init__(
        self,
        repositorio: IRepositorioStock,
        repositorio_libro: IRepositorio[Libro],
        repositorio_precio: IRepositorio[Precio],
        repositorio_moneda: IRepositorio[Moneda],
        repositorio_cotizacion: IRepositorioCotizacionDolar,
    ) -> None:
        """Inicializa con repositorios que valida y consulta."""
        self._repositorio = repositorio
        self._repositorio_libro = repositorio_libro
        self._repositorio_precio = repositorio_precio
        self._repositorio_moneda = repositorio_moneda
        self._repositorio_cotizacion = repositorio_cotizacion

    @auditar("crear")
    def crear(self, stock: Stock) -> Stock:
        """Crea un registro de stock validando el libro referenciado."""
        _asignar_id_pendiente(stock, self.leer_todos())
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

    @auditar("actualizar")
    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza el stock de un libro validando su existencia."""
        self._exigir_libro(stock.libro_id)
        return self._repositorio.actualizar(stock)

    @auditar("eliminar")
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
                f"No se puede eliminar el stock del libro {libro_id} porque "
                f"aún quedan {stock.cantidad} unidad(es). Egreselas antes de "
                "eliminarlo."
            )
        return self._repositorio.eliminar(libro_id)

    @auditar("ingresar")
    def ingresar(self, libro_id: int, cantidad: int) -> Stock:
        """Registra el stock de un libro o incrementa el existente.

        Raises:
            ValueError: Si la cantidad no es positiva o el libro no existe.
        """
        self._exigir_cantidad(cantidad, "ingresar")
        stock = self._repositorio.leer_por_libro(libro_id)
        if stock is None:
            return self.crear(
                Stock(id=0, libro_id=libro_id, cantidad=cantidad)
            )
        stock.ajustar_cantidad(cantidad)
        return self._repositorio.actualizar(stock)

    @auditar("egresar")
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
        """Registros de stock en o por debajo del mínimo."""
        return [s for s in self.leer_todos() if s.cantidad <= cantidad_minima]

    def valor_inventario(
        self,
        moneda_origen_id: int,
        moneda_destino_id: int,
        tipo_id: int,
        fecha: Optional[date] = None,
    ) -> Decimal:
        """Calcula el valor del inventario (stock x precio vigente)."""

        origen = self._leer_moneda(moneda_origen_id)
        destino = self._leer_moneda(moneda_destino_id)
        cotizacion = _cotizacion_aplicable(
            self._repositorio_cotizacion, tipo_id, fecha)
        if cotizacion is None:
            raise ValueError(
                f"El tipo de cotización {tipo_id} no tiene cotizaciones "
                "cargadas."
            )
        total = Decimal("0")
        for stock in self.leer_todos():
            precio = _precio_vigente(
                self._repositorio_precio, stock.libro_id, moneda_origen_id
            )
            if precio is not None:
                valor = Decimal(stock.cantidad) * precio.valor
                total += _convertir(valor, cotizacion,
                                    origen.codigo, destino.codigo)
        return total.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)

    def _leer_moneda(self, moneda_id: int) -> Moneda:
        """Devuelve la moneda registrada con ese ID o falla."""
        return _exigir_existencia(
            self._repositorio_moneda.leer_por_id(
                moneda_id), moneda_id, "la moneda"
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
            raise ValueError(
                f"La cantidad a {operacion} debe ser mayor a cero.")


# --- Servicio de auditoría ---

class ServicioAuditoria:
    """Servicio de registro y consulta de la auditoría del sistema.

    Sprint 3 - Ejercicio 06: La tabla de auditoría registra la acción
    ejecutada, la fecha del hecho y el detalle de cada operación auditada.
    Este servicio permite registrar operaciones de forma explícita y consultar
    el historial de auditoría del sistema.
    """

    _etiqueta = "la auditoría"

    def __init__(self, repositorio: IRepositorio[Auditoria]) -> None:
        """Inicializa el servicio con el repositorio de auditoría."""
        self._repositorio = repositorio

    def registrar(self, accion: str, detalles: str = "") -> Auditoria:
        """Registra una operación en la tabla de auditoría.

        Args:
            accion (str): Acción auditada (por ejemplo: "crear_genero").
            detalles (str): Detalle de la operación auditada.

        Returns:
            Auditoria: Registro de auditoría creado.
        """
        auditoria = Auditoria(id=0, accion=accion, detalles=detalles)
        return self._repositorio.crear(auditoria)

    def leer_todos(self) -> List[Auditoria]:
        """Lista todos los registros de auditoría ordenados por fecha."""
        registros = self._repositorio.leer_todos()
        return sorted(registros, key=lambda registro: (registro.fecha,
                                                       registro.id))

    def leer_recientes(self, limite: int = 20) -> List[Auditoria]:
        """Lista los registros de auditoría más recientes.

        Args:
            limite (int): Cantidad máxima de registros a devolver.

        Returns:
            List[Auditoria]: Registros más recientes, del más nuevo al más
                antiguo.
        """
        if limite < 1:
            raise ValueError("El límite debe ser mayor a cero.")
        return list(reversed(self.leer_todos()))[:limite]

    def leer_por_accion(self, accion: str) -> List[Auditoria]:
        """Lista los registros de auditoría de una acción determinada.

        Args:
            accion (str): Acción buscada (sin distinguir mayúsculas).

        Returns:
            List[Auditoria]: Registros que corresponden a la acción.
        """
        clave = _normalizar_texto(accion)
        return [
            registro for registro in self.leer_todos()
            if _normalizar_texto(registro.accion) == clave
        ]

    def acciones_registradas(self) -> List[str]:
        """Lista las acciones distintas registradas en la auditoría."""
        acciones = {registro.accion for registro in self.leer_todos()}
        return sorted(acciones)

    def eliminar(self, id: int) -> bool:
        """Elimina un registro de auditoría por su ID.

        Args:
            id (int): ID del registro a eliminar.

        Returns:
            bool: True si el registro fue eliminado, False si no existía.
        """
        return self._repositorio.eliminar(id)


# --- Funciones de conveniencia a nivel de módulo ---

def obtener_cotizaciones(
    servicio: Optional[ServicioCotizacionDolar] = None,
    api_url: Optional[str] = None,
) -> List[CotizacionDolar]:
    """Función de conveniencia para obtener cotizaciones de la API del dólar.

    Delega en el método `obtener_cotizaciones` de `ServicioCotizacionDolar`.
    Si no se suministra un servicio, crea una instancia utilizando los
    repositorios con persistencia en base de datos.

    Args:
        servicio (Optional[ServicioCotizacionDolar]): Instancia del servicio.
        api_url (Optional[str]): URL alternativa de la API.

    Returns:
        List[CotizacionDolar]: Cotizaciones registradas en la base de datos.
    """
    if servicio is None:
        servicio = ServicioCotizacionDolar(
            repositorio=RepositorioCotizacionDolar(),
            repositorio_tipo=RepositorioTipoCotizacion(),
            repositorio_moneda=RepositorioMoneda(),
        )
    return servicio.obtener_cotizaciones(api_url=api_url)
