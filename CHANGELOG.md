# Registro de Cambios (Changelog)

## Dia 20/10/2026

## [Ejercicio 02]
- Implementación de la función `cargar_datos_sql` en `migrations.py` para la lectura y ejecución secuencial de sentencias SQL desde la carpeta `migrations/sql/` hacia la base de datos relacional con SQLAlchemy.
- Procesamiento y ejecución transaccional atómica con `ConexionDB.sesion()`, asegurando limpieza previa (`_vaciar_tablas`) e idempotencia en la carga.
- Implementación de la función auxiliar `_extraer_sentencias_sql` para omitir comentarios y separar comandos `INSERT` individuales delimitados por punto y coma.
- Ajuste y sincronización automática de secuencias autoincrementales (`setval`) en PostgreSQL tras la inserción con claves primarias explícitas.
- Manejo robusto de excepciones ante fallas de archivos o sintaxis SQL con mensajes descriptivos (`ValueError`) y rollback automático.
- Integración e invocación de `cargar_datos_sql` en la celda del Ejercicio 02 dentro del notebook `03_Book_Manager_Grupo_XX.ipynb`, verificando la inserción de las tablas `generos`, `editoriales`, `monedas`, `tipos_cotizacion`, `libros`, `libro_genero`, `precios`, `stock` y `cotizaciones_dolar`.

## Dia 19/10/2026

## [Ejercicio 01]
- Creación y configuración de la rama de trabajo `Sprint_3` a partir de la rama `Sprint_2`.
- Creación de los directorios `src/book_manager/scraper/` y `src/book_manager/reportes/` para incorporar la estructura requerida del scraper (Scrapy) y reportes generados.
- Incorporación de archivos `__init__.py` y `.gitkeep` para habilitar el empaquetado como módulos de Python y el versionado en Git.

## Dia 14/10/2026

## [Integración Supabase]
- Conexión de la aplicación a la base de datos relacional de Supabase (PostgreSQL) mediante SQLAlchemy, en reemplazo de SQLite local.
- `connection.py` ahora resuelve la URL según el uso: `DATABASE_URL` (pooler en modo transacción, puerto 6543) para la aplicación y `DIRECT_URL` (pooler en modo sesión, puerto 5432) para migraciones/DDL.
- Soporte de la variable `SUPABASE_DB_PASSWORD` para inyectar la contraseña en las URL que contienen el marcador `[YOUR-PASSWORD]`; la contraseña de Supabase se completa en el archivo `.env` para no dejarla en el código fuente.
- Configuración de PostgreSQL: `pool_pre_ping`, SSL (`sslmode=require`) y `NullPool` para el pooler en modo transacción (pgbouncer).
- Desactivación de las sentencias preparadas automáticas de psycopg 3 (`prepare_threshold=None`) solo cuando se usa ese driver contra el pooler de Supabase, para evitar el error `DuplicatePreparedStatement` (las conexiones de servidor se reutilizan entre clientes en modo transacción).
- `migrar_datos` inicializa la conexión con `DIRECT_URL` y reinicia las secuencias (`setval`) tras insertar IDs explícitos, para que las altas posteriores no colisionen con la clave primaria.
- Incorporación de `psycopg2-binary` a `requirements.txt` y documentación de las variables de entorno en el README.

## [Correcciones]
- Restauración del método `_crear_libro` en la consola, que había quedado fusionado con `_buscar_libro`, y de la lectura de `generos_ids`.
- Corrección en `_convertir` (`services.py`) para usar `elif`, evitando el error de conversión no soportada al pasar de dólares a pesos.
- El menú de la consola finaliza de forma limpia ante `EOFError`/`KeyboardInterrupt`, necesario para ejecutar `main(import_default_data=False)` en el notebook sin interacción (Runtime → Run all).

## [Ejercicio 08]
- Incorporación de nuevas opciones en la interfaz de consola (`console.py`) para interactuar con las cotizaciones de la API y reportes avanzados de precios.
- Implementación de la opción de menú "Obtener las cotizaciones por api" en la gestión de cotizaciones y en la gestión de precios, conectada con `ServicioCotizacionDolar.obtener_cotizaciones`.
- Implementación de la opción de menú "Ver la lista de precios bimonetaria de los libros" en la gestión de precios, permitiendo contrastar el precio en pesos (ARS) contra cualquier otra moneda secundaria seleccionada (por ejemplo USD) con cotización en tiempo real.
- Implementación de la opción de menú "Exportar los precios a archivo CSV para todos los tipos de monedas" en la gestión de precios, generando un archivo CSV con los precios vigentes directos y cotizados para todas las monedas del sistema.
- Incorporación de los métodos de lógica de negocio `lista_precios_bimonetaria` y `exportar_precios_csv` en `ServicioPrecio` (`services.py`), manteniendo el desacoplamiento entre la capa de presentación y la capa de servicios.
- Validación de datos de entrada y captura de excepciones de negocio (`ValueError` y `OSError`) con mensajes claros y descriptivos para el usuario en la consola.

## Dia 13/10/2026

## [Ejercicio 07]
- Creación y configuración del archivo `.env` en la raíz del proyecto para definir la URL del endpoint de la API (`API_URL=https://dolarapi.com/v1/dolares`) y la URL de conexión a la base de datos (`DATABASE_URL`).
- Carga de variables de entorno mediante `python-dotenv` para mantener desacoplada la configuración y evitar datos sensibles en el código fuente.
- Implementación de la función y método `obtener_cotizaciones` dentro de `ServicioCotizacionDolar` en `services.py` para consultar la API externa de Dólar Argentina (`dolarapi.com`), descargar las cotizaciones actualizadas y persistirlas en la base de datos relacional.
- Mapeo automático de los tipos de cotización devueltos por la API (`Oficial`, `Blue`, `Bolsa`, `Contado con liquidación`/`CCL`, `Tarjeta`, `Mayorista`) con las entidades de la base de datos, resolviendo sinónimos y dando de alta nuevos tipos si fuera necesario (por ejemplo `Cripto`).
- Validación de datos de cotización: parseo de fechas ISO asegurando que no sean futuras, valores numéricos de compra y venta mayores a cero, y consistencia de que el valor de venta sea mayor o igual al de compra.
- Persistencia idempotente: actualización de cotizaciones ya existentes para una misma fecha y tipo, e inserción de nuevos registros cuando no existen previamente.
- Manejo robusto de errores de red, HTTP y formato con mensajes descriptivos (`ValueError`) para el usuario.

## Dia 12/10/2026

## [Ejercicio 06]
- Modificación de todos los repositorios para que el sistema persista en la base de datos relacional mediante SQLAlchemy (ya no en memoria).
- Creación de `RepositorioBase(IRepositorio[T], Generic[T, M])` que concentra el CRUD (`crear`, `leer_por_id`, `leer_todos`, `actualizar`, `eliminar`) y la sesión de `ConexionDB`.
- Traducción automática entre entidades de dominio (Pydantic) y modelos ORM por coincidencia de columnas (`_entidad_desde_orm`, `_copiar_a_orm`).
- `RepositorioLibro` resuelve la relación muchos a muchos con géneros (`libro_genero`) y restaura el estado de alta (`activo`) al leer/escribir.
- `RepositorioStock` y `RepositorioCotizacionDolar` implementan el acceso especializado por `libro_id` y por `tipo_id` + `fecha` con consultas SQLAlchemy.
- `crear` con escritura idempotente (si el ID ya existe, actualiza), lo que permite precargar CSV sobre una base ya migrada sin duplicar registros.
- Manejo de errores de integridad: las violaciones de unicidad/restricciones se traducen a `ValueError` con mensajes claros para el usuario.
- `main` ahora crea las tablas antes de iniciar y cierra la conexión al finalizar (finally).

## Dia 11/10/2026
## [Ejercicio 05]
- Creación del módulo migrations.py con la función `migrar_datos(carpeta_csvs, carpeta_sqls)`.
- Lectura de los archivos CSV del TP1 y migración de los datos a la base de datos relacional (SQLAlchemy).
- Generación de los archivos `.sql` con las sentencias INSERT en migrations/sql (un archivo por tabla).
- Poblado de las tablas en orden respetando las claves foráneas: generos, editoriales, monedas, tipos_cotizacion, libros, libro_genero, precios, stock y cotizaciones_dolar.
- Derivación de la tabla de asociación `libro_genero` a partir de la columna `generos_ids` de libros.csv.
- Migración idempotente: las tablas se vacían (en orden inverso por FK) antes de volver a cargar los datos.
- Escape seguro de literales SQL y manejo de valores nulos, booleanos, fechas y decimales.

## [Ejercicio 04]
- Creación de los modelos ORM de SQLAlchemy en models.py con la clase base declarativa `Base`.
- Definición de las tablas del sistema con sus tipos de datos y relaciones: `generos`, `editoriales`, `monedas`, `tipos_cotizacion`, `libros`, `precios`, `stock` y `cotizaciones_dolar`.
- Tabla de asociación `libro_genero` para la relación muchos a muchos entre `Libro` y `Genero`.
- Claves foráneas con reglas de integridad referencial (`CASCADE` y `RESTRICT`) y relaciones bidireccionales con `relationship`.
- Restricción de unicidad `UniqueConstraint(tipo_id, fecha)` en `cotizaciones_dolar` (una cotización por tipo y fecha).
- Uso de tipos adecuados por columna: `String`, `Integer`, `Boolean`, `Date`, `Numeric`, incluyendo `Numeric(12, 2)` para precios y `Numeric(12, 4)` para cotizaciones.
- Tipos anotados con `Mapped`/`mapped_column` y type hints en todas las clases.

## [Ejercicio 03]
- Implementación de un context manager (`ConexionDB.sesion`) en connection.py para manejar de forma segura las transacciones de base de datos (commit, rollback automático y cierre).

## Dia 10/10/2026
## [Ejercicio 02]
- Creación de la clase ConexionDB en connection.py para el manejo de conexiones con SQLAlchemy.
- Configuración de dependencias actualizadas en requirements.txt para correr el ejercicio 2.

## Dia 09/10/2026
## [Ejercicio 01]
- Inicialización y configuración del versionado para el Sprint 2.
- Creación de las carpetas de base de datos (database), modelos (models) y scripts SQL (migrations/sql).
- Creación de la rama `Sprint_2` partiendo de `Sprint_1` y push al repositorio remoto.
- Actualización del README con el objetivo, contexto y estado del Sprint 2.
- Se respeta el formato de commits `Día X: <comentario>` y los archivos puntuales (sin `git add .`).

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
