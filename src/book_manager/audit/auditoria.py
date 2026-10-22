# -*- coding: utf-8 -*-
"""Mecanismo de auditoría de las operaciones del sistema Book Manager.

Sprint 3 - Ejercicio 06: Crear un decorador para manejar las auditorías del
sistema; cada operación debe estar auditada.

El decorador ``auditar`` envuelve los métodos de los servicios de negocio y
registra en la tabla de auditoría la acción ejecutada, la fecha del hecho y el
detalle de la operación (servicio, datos involucrados y resultado). De este
modo el registro queda desacoplado del código de negocio y todas las altas,
modificaciones, bajas y operaciones relevantes del sistema quedan auditadas.
"""

import functools
import inspect
import re
import sys
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Optional, TypeVar

from book_manager.entities.entities import Auditoria
from book_manager.repositories.repositories import RepositorioAuditoria

F = TypeVar("F", bound=Callable[..., Any])

# Límites alineados con el tamaño de las columnas de la tabla de auditoría.
LIMITE_ACCION = 50
LIMITE_DETALLES = 500

# Límites de los resúmenes que se incluyen en el detalle de la operación.
MAXIMO_CAMPOS = 6
MAXIMO_ELEMENTOS = 3

# Palabras que se omiten al construir el nombre de la entidad auditada.
ARTICULOS = ("el", "la", "los", "las", "de")


# ---------------------------------------------------------------------------
# Utilidades internas de construcción del detalle
# ---------------------------------------------------------------------------

def _slug(texto: str) -> str:
    """Convierte un texto en un identificador corto, sin acentos.

    Args:
        texto (str): Texto a convertir (por ejemplo: "el género").

    Returns:
        str: Identificador en minúsculas separado por guiones bajos
            (por ejemplo: "genero").
    """
    normalizado = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(
        caracter for caracter in normalizado
        if not unicodedata.combining(caracter)
    )
    palabras = [
        palabra for palabra in re.split(r"[^A-Za-z0-9]+", sin_acentos.lower())
        if palabra and palabra not in ARTICULOS
    ]
    return "_".join(palabras)


def _resumen_valor(valor: Any) -> str:
    """Genera una descripción breve y legible de un valor.

    Args:
        valor (Any): Valor a resumir.

    Returns:
        str: Representación resumida del valor.
    """
    if valor is None:
        return "None"
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, (int, float, Decimal)):
        return str(valor)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, str):
        return f"'{valor}'"
    if isinstance(valor, dict):
        pares = list(valor.items())[:MAXIMO_CAMPOS]
        return "{" + ", ".join(
            f"{clave}={_resumen_valor(contenido)}"
            for clave, contenido in pares
        ) + "}"
    if isinstance(valor, (list, tuple, set)):
        elementos = list(valor)[:MAXIMO_ELEMENTOS]
        return "[" + ", ".join(
            _resumen_valor(elemento) for elemento in elementos
        ) + "]"
    if hasattr(valor, "model_dump"):
        datos = {
            clave: contenido
            for clave, contenido in valor.model_dump().items()
            if clave != "id"
        }
        campos = list(datos.items())[:MAXIMO_CAMPOS]
        detalle = ", ".join(
            f"{clave}={_resumen_valor(contenido)}"
            for clave, contenido in campos
        )
        nombre = type(valor).__name__
        return f"{nombre}(id={getattr(valor, 'id', 0)}, {detalle})"
    return str(valor)


def _es_metodo(funcion: Callable[..., Any]) -> bool:
    """Indica si la función decorada es un método de una clase.

    Args:
        funcion (Callable[..., Any]): Función decorada.

    Returns:
        bool: True si la función recibe al receptor como primer argumento.
    """
    try:
        parametros = list(inspect.signature(funcion).parameters)
    except (TypeError, ValueError):
        return False
    return bool(parametros) and parametros[0] in ("self", "cls")


def _datos_argumentos(
    funcion: Callable[..., Any], args: tuple, kwargs: dict
) -> str:
    """Resume los argumentos con los que se invocó una función.

    En los métodos se descarta el primer argumento (el receptor) para mostrar
    únicamente los datos propios de la operación.

    Args:
        funcion (Callable[..., Any]): Función decorada.
        args (tuple): Argumentos posicionales recibidos.
        kwargs (dict): Argumentos nominales recibidos.

    Returns:
        str: Resumen de los argumentos (cadena vacía si no se pudieron
            resolver).
    """
    try:
        firma = inspect.signature(funcion)
        vinculados = firma.bind_partial(*args, **kwargs)
        vinculados.apply_defaults()
    except (TypeError, ValueError):
        return ""
    argumentos = list(vinculados.arguments.items())
    if _es_metodo(funcion):
        argumentos = argumentos[1:]
    return ", ".join(
        f"{nombre}={_resumen_valor(valor)}"
        for nombre, valor in argumentos
    )


def _nombre_entidad(args: tuple) -> str:
    """Deduce el nombre de la entidad sobre la que opera una función.

    Args:
        args (tuple): Argumentos posicionales recibidos por la función.

    Returns:
        str: Nombre de la entidad en formato corto (por ejemplo: "genero").
    """
    if not args:
        return ""
    instancia = args[0]
    etiqueta = getattr(instancia, "_etiqueta", None)
    if isinstance(etiqueta, str) and etiqueta.strip():
        return _slug(etiqueta)
    nombre_clase = type(instancia).__name__
    if nombre_clase.startswith("Servicio"):
        nombre_clase = nombre_clase[len("Servicio"):]
    return _slug(nombre_clase)


def _construir_accion(
    operacion: str, entidad: Optional[str], args: tuple
) -> str:
    """Construye el nombre de la acción auditada.

    Args:
        operacion (str): Operación ejecutada (por ejemplo: "crear").
        entidad (Optional[str]): Entidad explícita, si se informó.
        args (tuple): Argumentos posicionales recibidos por la función.

    Returns:
        str: Acción auditada (por ejemplo: "crear_genero").
    """
    nombre = entidad or _nombre_entidad(args)
    return f"{operacion}_{nombre}" if nombre else operacion


def _construir_detalles(
    funcion: Callable[..., Any],
    args: tuple,
    kwargs: dict,
    resultado: Any,
    error: Optional[BaseException],
) -> str:
    """Construye el detalle de la operación auditada.

    Args:
        funcion (Callable[..., Any]): Función decorada.
        args (tuple): Argumentos posicionales recibidos.
        kwargs (dict): Argumentos nominales recibidos.
        resultado (Any): Resultado devuelto por la función (None si falló).
        error (Optional[BaseException]): Excepción lançada por la función.

    Returns:
        str: Detalle legible de la operación.
    """
    servicio = type(args[0]).__name__ if args else "-"
    partes = [
        f"servicio={servicio}",
        f"operacion={funcion.__name__}",
    ]

    datos = _datos_argumentos(funcion, args, kwargs)
    if datos:
        partes.append(f"datos={datos}")

    if error is not None:
        partes.append("resultado=ERROR")
        partes.append(f"mensaje={error}")
    else:
        partes.append("resultado=OK")
        identificador = _identificador_resultado(resultado)
        if identificador:
            partes.append(identificador)

    return " | ".join(partes)


def _identificador_resultado(resultado: Any) -> str:
    """Obtiene el identificador o el valor devuelto por la operación.

    Args:
        resultado (Any): Resultado de la función decorada.

    Returns:
        str: Identificador del resultado (cadena vacía si no aplica).
    """
    identificador = getattr(resultado, "id", None)
    if isinstance(identificador, int) and not isinstance(identificador, bool):
        return f"id={identificador}"
    if isinstance(resultado, (int, bool)):
        return f"retorno={resultado}"
    return ""


# ---------------------------------------------------------------------------
# Registro de auditoría
# ---------------------------------------------------------------------------

class Auditor:
    """Punto único de registro de las operaciones auditadas del sistema.

    Se encarga de persistir los registros de auditoría en la base de datos
    mediante el repositorio de la entidad ``Auditoria``. Si el registro no
    puede persistirse, la operación auditada no se interrumpe: se informa el
    motivo por pantalla y se continúa.
    """

    def __init__(
        self, repositorio: Optional[RepositorioAuditoria] = None
    ) -> None:
        """Inicializa el auditor con el repositorio de auditoría."""
        self._repositorio = repositorio

    @property
    def repositorio(self) -> RepositorioAuditoria:
        """Repositorio utilizado para persistir los registros de auditoría."""
        if self._repositorio is None:
            self._repositorio = RepositorioAuditoria()
        return self._repositorio

    def registrar(
        self, accion: str, detalles: str = ""
    ) -> Optional[Auditoria]:
        """Registra una operación en la tabla de auditoría.

        Args:
            accion (str): Acción auditada (por ejemplo: "crear_genero").
            detalles (str): Detalle de la operación auditada.

        Returns:
            Optional[Auditoria]: Registro creado, o None si no se pudo
                persistir.
        """
        try:
            auditoria = Auditoria(
                id=0,
                accion=accion[:LIMITE_ACCION],
                detalles=detalles[:LIMITE_DETALLES],
            )
            return self.repositorio.crear(auditoria)
        except Exception as error:
            print(
                f"[auditoría] No se pudo registrar la operación "
                f"'{accion}': {error}",
                file=sys.stderr,
            )
            return None


_auditor: Optional[Auditor] = None


def obtener_auditor() -> Auditor:
    """Devuelve el auditor utilizado por el decorador de auditoría.

    Returns:
        Auditor: Instancia única del auditor del sistema.
    """
    global _auditor
    if _auditor is None:
        _auditor = Auditor()
    return _auditor


def configurar_auditor(repositorio: RepositorioAuditoria) -> None:
    """Inyecta el repositorio de auditoría utilizado por el decorador.

    Args:
        repositorio (RepositorioAuditoria): Repositorio de auditoría a
            utilizar.
    """
    global _auditor
    _auditor = Auditor(repositorio)


# ---------------------------------------------------------------------------
# Decorador de auditoría
# ---------------------------------------------------------------------------

def auditar(
    operacion: str, entidad: Optional[str] = None
) -> Callable[[F], F]:
    """Decora una operación para que quede registrada en la auditoría.

    El decorador registra la acción ejecutada, la fecha del hecho y el detalle
    de la operación (servicio, datos involucrados y resultado). Las operaciones
    fallidas también se registran, indicando el mensaje de error, y la
    excepción original se vuelve a lanzar sin alterarla.

    Args:
        operacion (str): Nombre de la operación auditada (por ejemplo:
            "crear", "actualizar", "eliminar").
        entidad (Optional[str]): Entidad sobre la que se opera. Si no se
            indica, se deduce del servicio que ejecuta la operación.

    Returns:
        Callable[[F], F]: Decorador que envuelve la función auditada.

    Example:
        >>> @auditar("crear")
        ... def crear(self, entidad):
        ...     ...
    """

    def decorador(funcion: F) -> F:
        """Envuelve la función decorada registrando su ejecución."""

        @functools.wraps(funcion)
        def envoltorio(*args: Any, **kwargs: Any) -> Any:
            """Ejecuta la función decorada y audita el resultado."""
            accion = _construir_accion(operacion, entidad, args)
            try:
                resultado = funcion(*args, **kwargs)
            except Exception as error:
                obtener_auditor().registrar(
                    accion,
                    _construir_detalles(funcion, args, kwargs, None, error),
                )
                raise
            obtener_auditor().registrar(
                accion,
                _construir_detalles(funcion, args, kwargs, resultado, None),
            )
            return resultado

        return envoltorio  # type: ignore[return-value]

    return decorador
