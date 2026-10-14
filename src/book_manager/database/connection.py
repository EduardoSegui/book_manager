# -*- coding: utf-8 -*-
"""Configuración de la conexión a la base de datos con SQLAlchemy.

Ejercicio 02: Clase ConexionDB para la conexión con SQLAlchemy.
Ejercicio 03: Context manager para manejar transacciones a la base de datos.
"""

import os
from contextlib import contextmanager
from typing import Generator
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from book_manager.models.models import Base

# Cargar variables de entorno desde .env
load_dotenv()

# URL de respaldo para desarrollo local sin variables de entorno.
URL_POR_DEFECTO = "sqlite:///book_manager.db"

# Marcador que la documentación de Supabase usa en sus cadenas de conexión.
MARCADOR_PASSWORD = "[YOUR-PASSWORD]"


def _resolver_password(database_url: str) -> str:
    """Inyecta la contraseña de Supabase en la URL de conexión.

    Si la URL contiene el marcador ``[YOUR-PASSWORD]`` y existe la variable de
    entorno ``SUPABASE_DB_PASSWORD``, se reemplaza el marcador por la
    contraseña (codificada para URL). Esto evita versionar la contraseña.
    """
    password = os.getenv("SUPABASE_DB_PASSWORD")
    if password and MARCADOR_PASSWORD in database_url:
        return database_url.replace(
            MARCADOR_PASSWORD, quote(password, safe="")
        )
    return database_url


def _crear_engine(database_url: str) -> Engine:
    """Crea el motor de SQLAlchemy adaptado al backend indicado.

    Para SQLite se conserva el comportamiento simple. Para PostgreSQL
    (Supabase) se habilita ``pool_pre_ping``, se fuerza SSL y, si la URL
    corresponde al pooler en modo transacción (pgbouncer, puerto 6543), se usa
    ``NullPool`` porque ese pooler no admite estado de sesión persistente.
    """
    database_url = _resolver_password(database_url)
    url: URL = make_url(database_url)

    if url.get_backend_name() != "postgresql":
        return create_engine(url)

    opciones: dict = {"pool_pre_ping": True}
    parametros = dict(url.query)
    usa_pgbouncer = "pgbouncer" in parametros or url.port == 6543
    parametros.pop("pgbouncer", None)
    if "sslmode" not in parametros:
        parametros["sslmode"] = "require"
    url = url.set(query=parametros)
    if usa_pgbouncer:
        opciones["poolclass"] = NullPool
        # psycopg 3 prepara sentencias automáticamente, pero el pooler en modo
        # transacción de Supabase reutiliza conexiones de servidor entre
        # clientes y provoca "DuplicatePreparedStatement". Se desactiva la
        # preparación automática solo para ese driver.
        if url.get_driver_name() == "psycopg":
            opciones["connect_args"] = {"prepare_threshold": None}
    return create_engine(url, **opciones)


class ConexionDB:
    """Gestiona la conexión y las sesiones con la base de datos.

    Proporciona un único punto de acceso al motor (engine) de SQLAlchemy
    y un context manager para manejar transacciones de forma segura.
    """

    _engine: Engine | None = None
    _session_factory: sessionmaker | None = None

    @classmethod
    def inicializar(
        cls,
        database_url: str | None = None,
        para_migraciones: bool = False,
    ) -> None:
        """Inicializa el motor y la fábrica de sesiones.

        Args:
            database_url: URL de conexión a la base de datos. Si no se pasa,
                se toma de las variables de entorno.
            para_migraciones: Si es True se prioriza ``DIRECT_URL`` (pooler en
                modo sesión), recomendado para DDL y migraciones en Supabase.
                En caso contrario se prioriza ``DATABASE_URL`` (pooler en modo
                transacción) que usa la aplicación.
        """
        if database_url is None:
            if para_migraciones:
                database_url = (
                    os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")
                )
            else:
                database_url = (
                    os.getenv("DATABASE_URL") or os.getenv("DIRECT_URL")
                )
        if not database_url:
            database_url = URL_POR_DEFECTO

        if cls._engine is not None:
            cls._engine.dispose()

        cls._engine = _crear_engine(database_url)
        cls._session_factory = sessionmaker(
            bind=cls._engine, expire_on_commit=False)

    @classmethod
    def obtener_engine(cls) -> Engine:
        """Retorna el motor de SQLAlchemy, inicializándolo si es necesario."""
        if cls._engine is None:
            cls.inicializar()
        return cls._engine

    @classmethod
    def crear_tablas(cls) -> None:
        """Crea todas las tablas definidas en los modelos (Base.metadata)."""
        engine = cls.obtener_engine()
        Base.metadata.create_all(engine)

    @classmethod
    @contextmanager
    def sesion(cls) -> Generator[Session, None, None]:
        """Context manager para obtener una sesión con transacciones.

        Yields:
            Session: Sesión de SQLAlchemy lista para usar.

        Example:
            with ConexionDB.sesion() as session:
                libro = session.get(Libro, 1)
                ...
        """
        if cls._session_factory is None:
            cls.inicializar()

        session = cls._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def cerrar(cls) -> None:
        """Cierra el motor y libera los recursos."""
        if cls._engine is not None:
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
