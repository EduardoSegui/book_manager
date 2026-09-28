# -*- coding: utf-8 -*-
"""Interfaz de consola del sistema Book Manager.

Ejercicio 06: Interfaces gráficas del sistema que operan con los CRUD de cada clase.
"""

import os
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Callable, List, Optional, TypeVar

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
)

T = TypeVar("T")


class Consola:
    """Interfaz de consola para el sistema Book Manager."""

    def __init__(
        self,
        servicio_genero: ServicioGenero,
        servicio_editorial: ServicioEditorial,
        servicio_moneda: ServicioMoneda,
        servicio_tipo_cotizacion: ServicioTipoCotizacion,
        servicio_libro: ServicioLibro,
        servicio_precio: ServicioPrecio,
        servicio_stock: ServicioStock,
        servicio_cotizacion: ServicioCotizacionDolar,
    ) -> None:
        """Inicializa la consola con los servicios del sistema."""
        self._servicio_genero = servicio_genero
        self._servicio_editorial = servicio_editorial
        self._servicio_moneda = servicio_moneda
        self._servicio_tipo_cotizacion = servicio_tipo_cotizacion
        self._servicio_libro = servicio_libro
        self._servicio_precio = servicio_precio
        self._servicio_stock = servicio_stock
        self._servicio_cotizacion = servicio_cotizacion

    def ejecutar(self) -> None:
        """Ejecuta el bucle principal de la consola."""
        self._limpiar_pantalla()
        print("=" * 60)
        print("  BOOK MANAGER - Sistema de Gestión de Librería")
        print("=" * 60)

        while True:
            self._mostrar_menu_principal()
            opcion = input("\nSeleccione una opción: ").strip()

            if opcion == "0":
                print("\nGracias por usar Book Manager. ¡Hasta luego!")
                break
            elif opcion == "1":
                self._menu_generos()
            elif opcion == "2":
                self._menu_editoriales()
            elif opcion == "3":
                self._menu_monedas()
            elif opcion == "4":
                self._menu_tipos_cotizacion()
            elif opcion == "5":
                self._menu_libros()
            elif opcion == "6":
                self._menu_precios()
            elif opcion == "7":
                self._menu_stock()
            elif opcion == "8":
                self._menu_cotizaciones()
            else:
                print("\nOpción no válida. Intente nuevamente.")

            input("\nPresione Enter para continuar...")
            self._limpiar_pantalla()

    # ------------------------------------------------------------------
    # Utilidades de consola
    # ------------------------------------------------------------------

    @staticmethod
    def _limpiar_pantalla() -> None:
        """Limpia la pantalla de la consola."""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def _pedir_texto(mensaje: str, obligatorio: bool = True) -> str:
        """Pide un texto al usuario."""
        while True:
            valor = input(mensaje).strip()
            if valor or not obligatorio:
                return valor
            print("Este campo es obligatorio.")

    @staticmethod
    def _pedir_entero(mensaje: str, minimo: Optional[int] = None, maximo: Optional[int] = None) -> int:
        """Pide un número entero al usuario."""
        while True:
            try:
                valor = int(input(mensaje).strip())
                if minimo is not None and valor < minimo:
                    print(f"El valor debe ser mayor o igual a {minimo}.")
                    continue
                if maximo is not None and valor > maximo:
                    print(f"El valor debe ser menor o igual a {maximo}.")
                    continue
                return valor
            except ValueError:
                print("Debe ingresar un número entero válido.")

    @staticmethod
    def _pedir_decimal(mensaje: str) -> Decimal:
        """Pide un número decimal al usuario."""
        while True:
            try:
                return Decimal(input(mensaje).strip())
            except InvalidOperation:
                print("Debe ingresar un número válido.")

    @staticmethod
    def _pedir_fecha(mensaje: str) -> Optional[date]:
        """Pide una fecha al usuario (formato YYYY-MM-DD)."""
        while True:
            texto = input(mensaje).strip()
            if not texto:
                return None
            try:
                return date.fromisoformat(texto)
            except ValueError:
                print("Formato de fecha inválido. Use YYYY-MM-DD.")

    @staticmethod
    def _confirmar(mensaje: str) -> bool:
        """Pide confirmación al usuario."""
        respuesta = input(f"{mensaje} (s/n): ").strip().lower()
        return respuesta in ("s", "si", "sí")

    @staticmethod
    def _mostrar_titulo(titulo: str) -> None:
        """Muestra un título de sección."""
        print(f"\n{'─' * 50}")
        print(f"  {titulo}")
        print(f"{'─' * 50}")

    @staticmethod
    def _mostrar_lista(items: List[T], formatear: Callable[[T], str]) -> None:
        """Muestra una lista de elementos."""
        if not items:
            print("  No hay registros para mostrar.")
            return
        for item in items:
            print(f"  {formatear(item)}")

    # ------------------------------------------------------------------
    # Menú principal
    # ------------------------------------------------------------------

    def _mostrar_menu_principal(self) -> None:
        """Muestra el menú principal."""
        print("\n" + "=" * 50)
        print("  MENÚ PRINCIPAL")
        print("=" * 50)
        print("  1. Gestión de Géneros")
        print("  2. Gestión de Editoriales")
        print("  3. Gestión de Monedas")
        print("  4. Gestión de Tipos de Cotización")
        print("  5. Gestión de Libros")
        print("  6. Gestión de Precios")
        print("  7. Gestión de Stock")
        print("  8. Gestión de Cotizaciones del Dólar")
        print("  0. Salir")

    # ------------------------------------------------------------------
    # Gestión de Géneros
    # ------------------------------------------------------------------

    def _menu_generos(self) -> None:
        """Menú de gestión de géneros."""
        self._mostrar_titulo("GESTIÓN DE GÉNEROS")
        print("  1. Listar géneros")
        print("  2. Crear género")
        print("  3. Modificar género")
        print("  4. Eliminar género")
        print("  0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            self._listar_generos()
        elif opcion == "2":
            self._crear_genero()
        elif opcion == "3":
            self._modificar_genero()
        elif opcion == "4":
            self._eliminar_genero()

    def _listar_generos(self) -> None:
        """Lista todos los géneros."""
        generos = self._servicio_genero.leer_todos()
        self._mostrar_lista(generos, lambda g: f"[{g.id}] {g.nombre} - {g.descripcion}")

    def _crear_genero(self) -> None:
        """Crea un nuevo género."""
        try:
            nombre = self._pedir_texto("Nombre del género: ")
            descripcion = self._pedir_texto("Descripción: ", obligatorio=False)
            genero = Genero(id=0, nombre=nombre, descripcion=descripcion)
            self._servicio_genero.crear(genero)
            print(f"\nGénero '{nombre}' creado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _modificar_genero(self) -> None:
        """Modifica un género existente."""
        try:
            id_genero = self._pedir_entero("ID del género a modificar: ", minimo=1)
            genero = self._servicio_genero.leer_por_id(id_genero)
            if genero is None:
                print(f"\nNo existe un género con el ID {id_genero}.")
                return

            print(f"\nNombre actual: {genero.nombre}")
            nombre = self._pedir_texto("Nuevo nombre: ")
            print(f"Descripción actual: {genero.descripcion}")
            descripcion = self._pedir_texto("Nueva descripción: ", obligatorio=False)

            genero.nombre = nombre
            genero.descripcion = descripcion
            self._servicio_genero.actualizar(genero)
            print(f"\nGénero modificado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _eliminar_genero(self) -> None:
        """Elimina un género."""
        try:
            id_genero = self._pedir_entero("ID del género a eliminar: ", minimo=1)
            if self._confirmar("¿Está seguro de eliminar este género?"):
                if self._servicio_genero.eliminar(id_genero):
                    print("\nGénero eliminado exitosamente.")
                else:
                    print(f"\nNo existe un género con el ID {id_genero}.")
        except ValueError as e:
            print(f"\nError: {e}")

    # ------------------------------------------------------------------
    # Gestión de Editoriales
    # ------------------------------------------------------------------

    def _menu_editoriales(self) -> None:
        """Menú de gestión de editoriales."""
        self._mostrar_titulo("GESTIÓN DE EDITORIALES")
        print("  1. Listar editoriales")
        print("  2. Crear editorial")
        print("  3. Modificar editorial")
        print("  4. Eliminar editorial")
        print("  0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            self._listar_editoriales()
        elif opcion == "2":
            self._crear_editorial()
        elif opcion == "3":
            self._modificar_editorial()
        elif opcion == "4":
            self._eliminar_editorial()

    def _listar_editoriales(self) -> None:
        """Lista todas las editoriales."""
        editoriales = self._servicio_editorial.leer_todos()
        self._mostrar_lista(editoriales, lambda e: f"[{e.id}] {e.nombre}")

    def _crear_editorial(self) -> None:
        """Crea una nueva editorial."""
        try:
            nombre = self._pedir_texto("Nombre de la editorial: ")
            editorial = Editorial(id=0, nombre=nombre)
            self._servicio_editorial.crear(editorial)
            print(f"\nEditorial '{nombre}' creada exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _modificar_editorial(self) -> None:
        """Modifica una editorial existente."""
        try:
            id_editorial = self._pedir_entero("ID de la editorial a modificar: ", minimo=1)
            editorial = self._servicio_editorial.leer_por_id(id_editorial)
            if editorial is None:
                print(f"\nNo existe una editorial con el ID {id_editorial}.")
                return

            print(f"\nNombre actual: {editorial.nombre}")
            nombre = self._pedir_texto("Nuevo nombre: ")

            editorial.nombre = nombre
            self._servicio_editorial.actualizar(editorial)
            print(f"\nEditorial modificada exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _eliminar_editorial(self) -> None:
        """Elimina una editorial."""
        try:
            id_editorial = self._pedir_entero("ID de la editorial a eliminar: ", minimo=1)
            if self._confirmar("¿Está seguro de eliminar esta editorial?"):
                if self._servicio_editorial.eliminar(id_editorial):
                    print("\nEditorial eliminada exitosamente.")
                else:
                    print(f"\nNo existe una editorial con el ID {id_editorial}.")
        except ValueError as e:
            print(f"\nError: {e}")

    # ------------------------------------------------------------------
    # Gestión de Monedas
    # ------------------------------------------------------------------

    def _menu_monedas(self) -> None:
        """Menú de gestión de monedas."""
        self._mostrar_titulo("GESTIÓN DE MONEDAS")
        print("  1. Listar monedas")
        print("  2. Crear moneda")
        print("  3. Modificar moneda")
        print("  4. Eliminar moneda")
        print("  0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            self._listar_monedas()
        elif opcion == "2":
            self._crear_moneda()
        elif opcion == "3":
            self._modificar_moneda()
        elif opcion == "4":
            self._eliminar_moneda()

    def _listar_monedas(self) -> None:
        """Lista todas las monedas."""
        monedas = self._servicio_moneda.leer_todos()
        self._mostrar_lista(monedas, lambda m: f"[{m.id}] {m.codigo} - {m.nombre} ({m.simbolo})")

    def _crear_moneda(self) -> None:
        """Crea una nueva moneda."""
        try:
            codigo = self._pedir_texto("Código ISO (ej: ARS, USD): ").upper()
            nombre = self._pedir_texto("Nombre de la moneda: ")
            simbolo = self._pedir_texto("Símbolo (ej: $, US$): ")
            moneda = Moneda(id=0, codigo=codigo, nombre=nombre, simbolo=simbolo)
            self._servicio_moneda.crear(moneda)
            print(f"\nMoneda '{nombre}' creada exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _modificar_moneda(self) -> None:
        """Modifica una moneda existente."""
        try:
            id_moneda = self._pedir_entero("ID de la moneda a modificar: ", minimo=1)
            moneda = self._servicio_moneda.leer_por_id(id_moneda)
            if moneda is None:
                print(f"\nNo existe una moneda con el ID {id_moneda}.")
                return

            print(f"\nCódigo actual: {moneda.codigo}")
            codigo = self._pedir_texto("Nuevo código: ").upper()
            print(f"Nombre actual: {moneda.nombre}")
            nombre = self._pedir_texto("Nuevo nombre: ")
            print(f"Símbolo actual: {moneda.simbolo}")
            simbolo = self._pedir_texto("Nuevo símbolo: ")

            moneda.codigo = codigo
            moneda.nombre = nombre
            moneda.simbolo = simbolo
            self._servicio_moneda.actualizar(moneda)
            print(f"\nMoneda modificada exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _eliminar_moneda(self) -> None:
        """Elimina una moneda."""
        try:
            id_moneda = self._pedir_entero("ID de la moneda a eliminar: ", minimo=1)
            if self._confirmar("¿Está seguro de eliminar esta moneda?"):
                if self._servicio_moneda.eliminar(id_moneda):
                    print("\nMoneda eliminada exitosamente.")
                else:
                    print(f"\nNo existe una moneda con el ID {id_moneda}.")
        except ValueError as e:
            print(f"\nError: {e}")

    # ------------------------------------------------------------------
    # Gestión de Tipos de Cotización
    # ------------------------------------------------------------------

    def _menu_tipos_cotizacion(self) -> None:
        """Menú de gestión de tipos de cotización."""
        self._mostrar_titulo("GESTIÓN DE TIPOS DE COTIZACIÓN")
        print("  1. Listar tipos de cotización")
        print("  2. Crear tipo de cotización")
        print("  3. Modificar tipo de cotización")
        print("  4. Eliminar tipo de cotización")
        print("  0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            self._listar_tipos_cotizacion()
        elif opcion == "2":
            self._crear_tipo_cotizacion()
        elif opcion == "3":
            self._modificar_tipo_cotizacion()
        elif opcion == "4":
            self._eliminar_tipo_cotizacion()

    def _listar_tipos_cotizacion(self) -> None:
        """Lista todos los tipos de cotización."""
        tipos = self._servicio_tipo_cotizacion.leer_todos()
        self._mostrar_lista(tipos, lambda t: f"[{t.id}] {t.nombre} - {t.descripcion}")

    def _crear_tipo_cotizacion(self) -> None:
        """Crea un nuevo tipo de cotización."""
        try:
            nombre = self._pedir_texto("Nombre del tipo de cotización: ")
            descripcion = self._pedir_texto("Descripción: ", obligatorio=False)
            tipo = TipoCotizacion(id=0, nombre=nombre, descripcion=descripcion)
            self._servicio_tipo_cotizacion.crear(tipo)
            print(f"\nTipo de cotización '{nombre}' creado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _modificar_tipo_cotizacion(self) -> None:
        """Modifica un tipo de cotización existente."""
        try:
            id_tipo = self._pedir_entero("ID del tipo de cotización a modificar: ", minimo=1)
            tipo = self._servicio_tipo_cotizacion.leer_por_id(id_tipo)
            if tipo is None:
                print(f"\nNo existe un tipo de cotización con el ID {id_tipo}.")
                return

            print(f"\nNombre actual: {tipo.nombre}")
            nombre = self._pedir_texto("Nuevo nombre: ")
            print(f"Descripción actual: {tipo.descripcion}")
            descripcion = self._pedir_texto("Nueva descripción: ", obligatorio=False)

            tipo.nombre = nombre
            tipo.descripcion = descripcion
            self._servicio_tipo_cotizacion.actualizar(tipo)
            print(f"\nTipo de cotización modificado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _eliminar_tipo_cotizacion(self) -> None:
        """Elimina un tipo de cotización."""
        try:
            id_tipo = self._pedir_entero("ID del tipo de cotización a eliminar: ", minimo=1)
            if self._confirmar("¿Está seguro de eliminar este tipo de cotización?"):
                if self._servicio_tipo_cotizacion.eliminar(id_tipo):
                    print("\nTipo de cotización eliminado exitosamente.")
                else:
                    print(f"\nNo existe un tipo de cotización con el ID {id_tipo}.")
        except ValueError as e:
            print(f"\nError: {e}")

    # ------------------------------------------------------------------
    # Gestión de Libros
    # ------------------------------------------------------------------

    def _menu_libros(self) -> None:
        """Menú de gestión de libros."""
        self._mostrar_titulo("GESTIÓN DE LIBROS")
        print("  1. Listar libros")
        print("  2. Buscar libro")
        print("  3. Crear libro")
        print("  4. Modificar libro")
        print("  5. Eliminar libro")
        print("  6. Dar de baja libro")
        print("  7. Dar de alta libro")
        print("  0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            self._listar_libros()
        elif opcion == "2":
            self._buscar_libro()
        elif opcion == "3":
            self._crear_libro()
        elif opcion == "4":
            self._modificar_libro()
        elif opcion == "5":
            self._eliminar_libro()
        elif opcion == "6":
            self._dar_de_baja_libro()
        elif opcion == "7":
            self._dar_de_alta_libro()

    def _listar_libros(self) -> None:
        """Lista todos los libros."""
        libros = self._servicio_libro.leer_todos()
        self._mostrar_lista(libros, lambda l: f"[{l.id}] {l.titulo} - {l.autor} (ISBN: {l.isbn})")

    def _buscar_libro(self) -> None:
        """Busca un libro por título, autor o ISBN."""
        texto = self._pedir_texto("Texto a buscar (título, autor o ISBN): ")
        libros = self._servicio_libro.buscar(texto)
        if not libros:
            print("\nNo se encontraron libros.")
            return
        self._mostrar_lista(libros, lambda l: f"[{l.id}] {l.titulo} - {l.autor} (ISBN: {l.isbn})")

    def _crear_libro(self) -> None:
        """Crea un nuevo libro."""
        try:
            isbn = self._pedir_texto("ISBN: ")
            titulo = self._pedir_texto("Título: ")
            autor = self._pedir_texto("Autor: ")
            anio = self._pedir_entero("Año de publicación: ", minimo=0)
            id_editorial = self._pedir_entero("ID de editorial: ", minimo=1)
            generos_ids = self._pedir_texto("IDs de géneros (separados por coma): ")
            generos_lista = [int(x.strip()) for x in generos_ids.split(",") if x.strip()]
            descripcion = self._pedir_texto("Descripción: ", obligatorio=False)

            libro = Libro(
                id=0,
                isbn=isbn,
                titulo=titulo,
                autor=autor,
                anio_publicacion=anio,
                editorial_id=id_editorial,
                generos_ids=generos_lista,
                descripcion=descripcion,
            )
            self._servicio_libro.crear(libro)
            print(f"\nLibro '{titulo}' creado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _modificar_libro(self) -> None:
        """Modifica un libro existente."""
        try:
            id_libro = self._pedir_entero("ID del libro a modificar: ", minimo=1)
            libro = self._servicio_libro.leer_por_id(id_libro)
            if libro is None:
                print(f"\nNo existe un libro con el ID {id_libro}.")
                return

            print(f"\nISBN actual: {libro.isbn}")
            isbn = self._pedir_texto("Nuevo ISBN: ")
            print(f"Título actual: {libro.titulo}")
            titulo = self._pedir_texto("Nuevo título: ")
            print(f"Autor actual: {libro.autor}")
            autor = self._pedir_texto("Nuevo autor: ")
            print(f"Año actual: {libro.anio_publicacion}")
            anio = self._pedir_entero("Nuevo año: ", minimo=0)
            print(f"ID editorial actual: {libro.editorial_id}")
            id_editorial = self._pedir_entero("Nuevo ID de editorial: ", minimo=1)
            print(f"Géneros actuales: {libro.generos_ids}")
            generos_ids = self._pedir_texto("Nuevos IDs de géneros (separados por coma): ")
            generos_lista = [int(x.strip()) for x in generos_ids.split(",") if x.strip()]
            print(f"Descripción actual: {libro.descripcion}")
            descripcion = self._pedir_texto("Nueva descripción: ", obligatorio=False)

            libro.isbn = isbn
            libro.titulo = titulo
            libro.autor = autor
            libro.anio_publicacion = anio
            libro.editorial_id = id_editorial
            libro.generos_ids = generos_lista
            libro.descripcion = descripcion
            self._servicio_libro.actualizar(libro)
            print(f"\nLibro modificado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _eliminar_libro(self) -> None:
        """Elimina un libro."""
        try:
            id_libro = self._pedir_entero("ID del libro a eliminar: ", minimo=1)
            if self._confirmar("¿Está seguro de eliminar este libro?"):
                if self._servicio_libro.eliminar(id_libro):
                    print("\nLibro eliminado exitosamente.")
                else:
                    print(f"\nNo existe un libro con el ID {id_libro}.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _dar_de_baja_libro(self) -> None:
        """Da de baja un libro."""
        try:
            id_libro = self._pedir_entero("ID del libro a dar de baja: ", minimo=1)
            self._servicio_libro.dar_de_baja(id_libro)
            print("\nLibro dado de baja exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _dar_de_alta_libro(self) -> None:
        """Da de alta un libro."""
        try:
            id_libro = self._pedir_entero("ID del libro a dar de alta: ", minimo=1)
            self._servicio_libro.dar_de_alta(id_libro)
            print("\nLibro dado de alta exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    # ------------------------------------------------------------------
    # Gestión de Precios
    # ------------------------------------------------------------------

    def _menu_precios(self) -> None:
        """Menú de gestión de precios."""
        self._mostrar_titulo("GESTIÓN DE PRECIOS")
        print("  1. Listar precios")
        print("  2. Ver precios de un libro")
        print("  3. Crear precio")
        print("  4. Modificar precio")
        print("  5. Eliminar precio")
        print("  6. Cotizar precio de libro")
        print("  0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            self._listar_precios()
        elif opcion == "2":
            self._ver_precios_libro()
        elif opcion == "3":
            self._crear_precio()
        elif opcion == "4":
            self._modificar_precio()
        elif opcion == "5":
            self._eliminar_precio()
        elif opcion == "6":
            self._cotizar_precio()

    def _listar_precios(self) -> None:
        """Lista todos los precios."""
        precios = self._servicio_precio.leer_todos()
        self._mostrar_lista(precios, lambda p: f"[{p.id}] Libro {p.libro_id} - Moneda {p.moneda_id}: {p.valor} ({p.fecha})")

    def _ver_precios_libro(self) -> None:
        """Muestra los precios de un libro."""
        id_libro = self._pedir_entero("ID del libro: ", minimo=1)
        precios = self._servicio_precio.leer_por_libro(id_libro)
        self._mostrar_lista(precios, lambda p: f"[{p.id}] Moneda {p.moneda_id}: {p.valor} ({p.fecha})")

    def _crear_precio(self) -> None:
        """Crea un nuevo precio."""
        try:
            id_libro = self._pedir_entero("ID del libro: ", minimo=1)
            id_moneda = self._pedir_entero("ID de la moneda: ", minimo=1)
            valor = self._pedir_decimal("Valor del precio: ")
            fecha = self._pedir_fecha("Fecha (YYYY-MM-DD, Enter para hoy): ")

            precio = Precio(
                id=0,
                libro_id=id_libro,
                moneda_id=id_moneda,
                valor=valor,
                fecha=fecha or date.today(),
            )
            self._servicio_precio.crear(precio)
            print("\nPrecio creado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _modificar_precio(self) -> None:
        """Modifica un precio existente."""
        try:
            id_precio = self._pedir_entero("ID del precio a modificar: ", minimo=1)
            precio = self._servicio_precio.leer_por_id(id_precio)
            if precio is None:
                print(f"\nNo existe un precio con el ID {id_precio}.")
                return

            print(f"\nLibro actual: {precio.libro_id}")
            id_libro = self._pedir_entero("Nuevo ID de libro: ", minimo=1)
            print(f"Moneda actual: {precio.moneda_id}")
            id_moneda = self._pedir_entero("Nuevo ID de moneda: ", minimo=1)
            print(f"Valor actual: {precio.valor}")
            valor = self._pedir_decimal("Nuevo valor: ")
            print(f"Fecha actual: {precio.fecha}")
            fecha = self._pedir_fecha("Nueva fecha (YYYY-MM-DD, Enter para hoy): ")

            precio.libro_id = id_libro
            precio.moneda_id = id_moneda
            precio.valor = valor
            precio.fecha = fecha or date.today()
            self._servicio_precio.actualizar(precio)
            print("\nPrecio modificado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _eliminar_precio(self) -> None:
        """Elimina un precio."""
        try:
            id_precio = self._pedir_entero("ID del precio a eliminar: ", minimo=1)
            if self._confirmar("¿Está seguro de eliminar este precio?"):
                if self._servicio_precio.eliminar(id_precio):
                    print("\nPrecio eliminado exitosamente.")
                else:
                    print(f"\nNo existe un precio con el ID {id_precio}.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _cotizar_precio(self) -> None:
        """Cotiza el precio de un libro en otra moneda."""
        try:
            id_libro = self._pedir_entero("ID del libro: ", minimo=1)
            id_moneda_origen = self._pedir_entero("ID moneda origen: ", minimo=1)
            id_moneda_destino = self._pedir_entero("ID moneda destino: ", minimo=1)
            id_tipo_cotizacion = self._pedir_entero("ID tipo de cotización: ", minimo=1)
            fecha = self._pedir_fecha("Fecha (YYYY-MM-DD, Enter para más reciente): ")

            resultado = self._servicio_precio.cotizar(
                id_libro, id_moneda_origen, id_moneda_destino, id_tipo_cotizacion, fecha
            )
            if resultado is None:
                print("\nEl libro no tiene precio cargado en la moneda de origen.")
            else:
                print(f"\nPrecio cotizado: {resultado}")
        except ValueError as e:
            print(f"\nError: {e}")

    # ------------------------------------------------------------------
    # Gestión de Stock
    # ------------------------------------------------------------------

    def _menu_stock(self) -> None:
        """Menú de gestión de stock."""
        self._mostrar_titulo("GESTIÓN DE STOCK")
        print("  1. Listar stock")
        print("  2. Ver stock de un libro")
        print("  3. Ingresar stock")
        print("  4. Egresar stock")
        print("  5. Modificar stock")
        print("  6. Eliminar stock")
        print("  7. Stock sin disponibilidad")
        print("  8. Stock bajo")
        print("  9. Valor del inventario")
        print("  0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            self._listar_stock()
        elif opcion == "2":
            self._ver_stock_libro()
        elif opcion == "3":
            self._ingresar_stock()
        elif opcion == "4":
            self._egresar_stock()
        elif opcion == "5":
            self._modificar_stock()
        elif opcion == "6":
            self._eliminar_stock()
        elif opcion == "7":
            self._stock_sin_disponibilidad()
        elif opcion == "8":
            self._stock_bajo()
        elif opcion == "9":
            self._valor_inventario()

    def _listar_stock(self) -> None:
        """Lista todo el stock."""
        stock = self._servicio_stock.leer_todos()
        self._mostrar_lista(stock, lambda s: f"[{s.id}] Libro {s.libro_id}: {s.cantidad} unidades")

    def _ver_stock_libro(self) -> None:
        """Muestra el stock de un libro."""
        id_libro = self._pedir_entero("ID del libro: ", minimo=1)
        registro = self._servicio_stock.leer_por_libro(id_libro)
        if registro is None:
            print(f"\nNo hay stock registrado para el libro {id_libro}.")
        else:
            print(f"\nStock del libro {id_libro}: {registro.cantidad} unidades")

    def _ingresar_stock(self) -> None:
        """Ingresa stock a un libro."""
        try:
            id_libro = self._pedir_entero("ID del libro: ", minimo=1)
            cantidad = self._pedir_entero("Cantidad a ingresar: ", minimo=1)
            self._servicio_stock.ingresar(id_libro, cantidad)
            print(f"\nStock ingresado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _egresar_stock(self) -> None:
        """Egresa stock de un libro."""
        try:
            id_libro = self._pedir_entero("ID del libro: ", minimo=1)
            cantidad = self._pedir_entero("Cantidad a egresar: ", minimo=1)
            self._servicio_stock.egresar(id_libro, cantidad)
            print(f"\nStock egresado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _modificar_stock(self) -> None:
        """Modifica el stock de un libro."""
        try:
            id_libro = self._pedir_entero("ID del libro: ", minimo=1)
            cantidad = self._pedir_entero("Nueva cantidad: ", minimo=0)
            stock = Stock(id=0, libro_id=id_libro, cantidad=cantidad)
            self._servicio_stock.actualizar(stock)
            print("\nStock modificado exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _eliminar_stock(self) -> None:
        """Elimina el stock de un libro."""
        try:
            id_libro = self._pedir_entero("ID del libro: ", minimo=1)
            if self._confirmar("¿Está seguro de eliminar el stock?"):
                if self._servicio_stock.eliminar(id_libro):
                    print("\nStock eliminado exitosamente.")
                else:
                    print(f"\nNo existe stock para el libro {id_libro}.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _stock_sin_disponibilidad(self) -> None:
        """Muestra el stock sin disponibilidad."""
        stock = self._servicio_stock.sin_disponibilidad()
        self._mostrar_lista(stock, lambda s: f"[{s.id}] Libro {s.libro_id}: {s.cantidad} unidades")

    def _stock_bajo(self) -> None:
        """Muestra el stock bajo."""
        minimo = self._pedir_entero("Cantidad mínima: ", minimo=0)
        stock = self._servicio_stock.con_stock_bajo(minimo)
        self._mostrar_lista(stock, lambda s: f"[{s.id}] Libro {s.libro_id}: {s.cantidad} unidades")

    def _valor_inventario(self) -> None:
        """Calcula el valor del inventario."""
        try:
            id_moneda_origen = self._pedir_entero("ID moneda origen: ", minimo=1)
            id_moneda_destino = self._pedir_entero("ID moneda destino: ", minimo=1)
            id_tipo_cotizacion = self._pedir_entero("ID tipo de cotización: ", minimo=1)
            fecha = self._pedir_fecha("Fecha (YYYY-MM-DD, Enter para más reciente): ")

            valor = self._servicio_stock.valor_inventario(
                id_moneda_origen, id_moneda_destino, id_tipo_cotizacion, fecha
            )
            print(f"\nValor del inventario: {valor}")
        except ValueError as e:
            print(f"\nError: {e}")

    # ------------------------------------------------------------------
    # Gestión de Cotizaciones del Dólar
    # ------------------------------------------------------------------

    def _menu_cotizaciones(self) -> None:
        """Menú de gestión de cotizaciones del dólar."""
        self._mostrar_titulo("GESTIÓN DE COTIZACIONES DEL DÓLAR")
        print("  1. Listar cotizaciones")
        print("  2. Ver cotización por tipo y fecha")
        print("  3. Ver histórico por tipo")
        print("  4. Crear cotización")
        print("  5. Modificar cotización")
        print("  6. Eliminar cotización")
        print("  7. Convertir moneda")
        print("  0. Volver")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            self._listar_cotizaciones()
        elif opcion == "2":
            self._ver_cotizacion()
        elif opcion == "3":
            self._ver_historico_cotizaciones()
        elif opcion == "4":
            self._crear_cotizacion()
        elif opcion == "5":
            self._modificar_cotizacion()
        elif opcion == "6":
            self._eliminar_cotizacion()
        elif opcion == "7":
            self._convertir_moneda()

    def _listar_cotizaciones(self) -> None:
        """Lista todas las cotizaciones."""
        cotizaciones = self._servicio_cotizacion.leer_todos()
        self._mostrar_lista(
            cotizaciones,
            lambda c: f"[{c.id}] Tipo {c.tipo_id} - {c.fecha}: Compra {c.valor_compra} / Venta {c.valor_venta}",
        )

    def _ver_cotizacion(self) -> None:
        """Muestra una cotización por tipo y fecha."""
        id_tipo = self._pedir_entero("ID del tipo de cotización: ", minimo=1)
        fecha = self._pedir_fecha("Fecha (YYYY-MM-DD): ")
        if fecha is None:
            print("La fecha es obligatoria para esta consulta.")
            return

        cotizacion = self._servicio_cotizacion.leer_por_tipo_y_fecha(id_tipo, fecha)
        if cotizacion is None:
            print(f"\nNo existe cotización para el tipo {id_tipo} en la fecha {fecha}.")
        else:
            print(f"\nCotización - Tipo {cotizacion.tipo_id} - {cotizacion.fecha}")
            print(f"  Valor de compra: {cotizacion.valor_compra}")
            print(f"  Valor de venta: {cotizacion.valor_venta}")
            print(f"  Spread: {cotizacion.spread}")

    def _ver_historico_cotizaciones(self) -> None:
        """Muestra el histórico de cotizaciones de un tipo."""
        id_tipo = self._pedir_entero("ID del tipo de cotización: ", minimo=1)
        cotizaciones = self._servicio_cotizacion.leer_historico_por_tipo(id_tipo)
        self._mostrar_lista(
            cotizaciones,
            lambda c: f"[{c.id}] {c.fecha}: Compra {c.valor_compra} / Venta {c.valor_venta}",
        )

    def _crear_cotizacion(self) -> None:
        """Crea una nueva cotización."""
        try:
            id_tipo = self._pedir_entero("ID del tipo de cotización: ", minimo=1)
            fecha = self._pedir_fecha("Fecha (YYYY-MM-DD): ")
            if fecha is None:
                print("La fecha es obligatoria.")
                return
            valor_compra = self._pedir_decimal("Valor de compra: ")
            valor_venta = self._pedir_decimal("Valor de venta: ")

            cotizacion = CotizacionDolar(
                id=0,
                tipo_id=id_tipo,
                fecha=fecha,
                valor_compra=valor_compra,
                valor_venta=valor_venta,
            )
            self._servicio_cotizacion.crear(cotizacion)
            print("\nCotización creada exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _modificar_cotizacion(self) -> None:
        """Modifica una cotización existente."""
        try:
            id_tipo = self._pedir_entero("ID del tipo de cotización: ", minimo=1)
            fecha = self._pedir_fecha("Fecha (YYYY-MM-DD): ")
            if fecha is None:
                print("La fecha es obligatoria.")
                return

            cotizacion = self._servicio_cotizacion.leer_por_tipo_y_fecha(id_tipo, fecha)
            if cotizacion is None:
                print(f"\nNo existe cotización para el tipo {id_tipo} en la fecha {fecha}.")
                return

            print(f"\nValor de compra actual: {cotizacion.valor_compra}")
            valor_compra = self._pedir_decimal("Nuevo valor de compra: ")
            print(f"Valor de venta actual: {cotizacion.valor_venta}")
            valor_venta = self._pedir_decimal("Nuevo valor de venta: ")

            cotizacion.valor_compra = valor_compra
            cotizacion.valor_venta = valor_venta
            self._servicio_cotizacion.actualizar(cotizacion)
            print("\nCotización modificada exitosamente.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _eliminar_cotizacion(self) -> None:
        """Elimina una cotización."""
        try:
            id_tipo = self._pedir_entero("ID del tipo de cotización: ", minimo=1)
            fecha = self._pedir_fecha("Fecha (YYYY-MM-DD): ")
            if fecha is None:
                print("La fecha es obligatoria.")
                return

            if self._confirmar("¿Está seguro de eliminar esta cotización?"):
                if self._servicio_cotizacion.eliminar(id_tipo, fecha):
                    print("\nCotización eliminada exitosamente.")
                else:
                    print(f"\nNo existe cotización para el tipo {id_tipo} en la fecha {fecha}.")
        except ValueError as e:
            print(f"\nError: {e}")

    def _convertir_moneda(self) -> None:
        """Convierte un valor entre monedas."""
        try:
            valor = self._pedir_decimal("Valor a convertir: ")
            moneda_origen = self._pedir_texto("Código moneda origen (ej: USD): ").upper()
            moneda_destino = self._pedir_texto("Código moneda destino (ej: ARS): ").upper()
            id_tipo_cotizacion = self._pedir_entero("ID tipo de cotización: ", minimo=1)
            fecha = self._pedir_fecha("Fecha (YYYY-MM-DD, Enter para más reciente): ")

            resultado = self._servicio_cotizacion.convertir(
                valor, moneda_origen, moneda_destino, id_tipo_cotizacion, fecha
            )
            print(f"\n{valor} {moneda_origen} = {resultado} {moneda_destino}")
        except ValueError as e:
            print(f"\nError: {e}")
