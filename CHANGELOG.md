# Registro de Cambios (Changelog)

## Dia 30/09/2026
## [Ejercicio 07]
- Creación del archivo main.py como punto de entrada del sistema.
- Funciones privadas para componer el sistema: _crear_repositorios y _crear_servicios.
- Inyección de los repositorios en los servicios y armado de la Consola.
- Función main(import_default_data: bool = True) con carga opcional de la precarga CSV.
- Bloque if __name__ == "__main__" para permitir la ejecución directa del sistema.
- Documentación en el README de los comandos de ejecución local del sistema.

## Dia 29/09/2026
## [Ejercicio 06]
- Creación de la interfaz de consola (console.py) con menús interactivos para todas las entidades.
- Implementación del menú principal con acceso a los 8 módulos de gestión.
- CRUD completo para Géneros, Editoriales, Monedas y Tipos de Cotización.
- CRUD completo para Libros con funcionalidades adicionales: búsqueda, alta/baja lógica.
- CRUD completo para Precios con cotización cruzada entre monedas.
- CRUD completo para Stock con ingresos/egresos, consultas de stock bajo y valor de inventario.
- CRUD completo para Cotizaciones del Dólar con conversión de moneda.
- Validación de datos de entrada y manejo de errores con mensajes al usuario.
- Navegación por menús con confirmaciones para operaciones destructivas.

## Dia 28/09/2026
## [Ejercicio 05]
- Creación de archivos CSV en migrations/csv con datos de precarga para todas las entidades del sistema.
- Archivos generados: generos.csv, editoriales.csv, monedas.csv, tipos_cotizacion.csv, libros.csv, precios.csv, stock.csv y cotizaciones_dolar.csv.
- Cada entidad cuenta con un mínimo de 10 registros (12 registros por entidad, 20 precios).
- Implementación del módulo preload_data.py con funciones de carga para cada entidad.
- Función principal cargar_todos_los_datos que orquesta la importación completa desde los CSV hacia los repositorios.
- Manejo de tipos de datos: parseo de fechas ISO, valores decimales y listas de IDs separados por comas.
- Verificación exitosa de la precarga: todos los registros se cargaron correctamente en los repositorios.

## Dia 27/09/2026
## [Ejercicio 04]
- Definición de la interfaz abstracta IServicio[T] con el contrato CRUD de los servicios de catálogo.
- Creación de la clase base ServicioBase con el CRUD genérico y puntos de extensión (_validar_creacion, _validar_actualizacion, _validar_eliminacion y campos únicos declarativos) para evitar duplicar el CRUD en cada servicio.
- Implementación de los servicios ServicioGenero, ServicioEditorial, ServicioMoneda, ServicioTipoCotizacion, ServicioLibro, ServicioPrecio, ServicioStock y ServicioCotizacionDolar.
- Inyección de dependencias de los repositorios en cada servicio para mantener la separación entre la lógica de negocio y la persistencia.
- Validación de las relaciones entre entidades: existencia de editorial, géneros, libro, moneda y tipo de cotización referenciados.
- Validación de unicidad de nombres de género, editorial, tipo de cotización y de código y nombre de moneda, sin distinguir mayúsculas.
- Protección de la integridad referencial al eliminar: se bloquea la baja de géneros, editoriales y tipos de cotización en uso, y de libros con precios o stock asociado.
- Validación de unicidad del ISBN de los libros y de baja lógica del catálogo mediante dar_de_baja y dar_de_alta.
- Gestión de ingresos y egresos de unidades de stock, control de stock bajo y sin disponibilidad.
- Lógica de conversión de moneda a partir de la cotización del dólar (USD/ARS) y cálculo del valor del inventario según el tipo de cotización y la fecha indicados.
- Type hints y docstrings en todas las clases y métodos públicos.

## Dia 26/09/2026
## [Ejercicio 03]
- Definición de las interfaces abstractas IRepositorio[T], IRepositorioStock e IRepositorioCotizacionDolar con sus respectivos contratos CRUD.
- Implementación de RepositorioGenero, RepositorioEditorial, RepositorioMoneda, RepositorioTipoCotizacion, RepositorioLibro y RepositorioPrecio con CRUD completo en memoria.
- Implementación de RepositorioStock con acceso especializado por libro_id.
- Implementación de RepositorioCotizacionDolar con acceso por tipo_id + fecha y lectura histórica por tipo.
- Aplicación de encapsulamiento mediante atributos privados (_datos) y métodos controlados para todas las operaciones.
- Validación de duplicados, manejo de errores con ValueError y type hints en todos los métodos.

## Dia 24/09/2026
## [Ejercicio 02]
- Definición de las clases entidad del sistema: Libro, Genero, Editorial, Moneda, TipoCotizacion, Precio, Stock y CotizacionDolar.
- Implementación de los modelos con Pydantic para la validación automática de datos (tipos, restricciones y reglas de negocio).
- Creación de la clase base EntidadBase con el identificador común para todas las entidades.
- Uso de atributos privados, propiedades de solo lectura y métodos controlados para aplicar encapsulación.
- Instalación de Pydantic en el entorno virtual y actualización de requirements.txt.

## Dia 21/09/2026
## [Ejercicio 01]
- Inicialización y configuración de la herramienta de versionado.
- Creación de la estructura de directorios del proyecto.
- Configuración del entorno virtual local aislando dependencias.
- Definición de archivos base, README.md y estructura del Changelog.
