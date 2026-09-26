# Registro de Cambios (Changelog)

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
