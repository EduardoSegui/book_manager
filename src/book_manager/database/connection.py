# -*- coding: utf-8 -*-
"""Configuración de la conexión a la base de datos con SQLAlchemy.

Ejercicio 02: Clase ConexionDB para la conexión con SQLAlchemy.
"""

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker

from book_manager.models.models import Base

# Cargar variables de entorno desde .env
load_dotenv()


class ConexionDB:
    """Gestiona la conexión y las sesiones con la base de datos.

    Proporciona un único punto de acceso al motor (engine) de SQLAlchemy
    y un context manager para manejar transacciones de forma segura.
    """

    _engine: Engine | None = None
    _session_factory: sessionmaker | None = None

    @classmethod
    def inicializar(cls, database_url: str | None = None) -> None:
        """Inicializa el motor y la fábrica de sesiones.

        Args:
            database_url: URL de conexión a la base de datos. Si no se proporciona,
                se lee de la variable de entorno DATABASE_URL.
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///book_manager.db")

        cls._engine = create_engine(database_url, echo=False)
        cls._session_factory = sessionmaker(bind=cls._engine, expire_on_commit=False)

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
        """Context manager para obtener una sesión con manejo automático de transacciones.

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