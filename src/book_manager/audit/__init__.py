# -*- coding: utf-8 -*-
"""Paquete de auditoría del sistema Book Manager.

Sprint 3 - Ejercicio 06: expone el decorador ``auditar`` y el auditor del
sistema, utilizados para registrar cada operación ejecutada.
"""

from book_manager.audit.auditoria import (
    Auditor,
    auditar,
    configurar_auditor,
    obtener_auditor,
)

__all__ = [
    "Auditor",
    "auditar",
    "configurar_auditor",
    "obtener_auditor",
]
