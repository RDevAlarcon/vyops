
"""Práctica de indexación vectorial con Gemini y ChromaDB.

Este módulo reproduce un ejemplo de preparación
e indexación de documentos para un sistema RAG.

El ejercicio utiliza un corpus ficticio
de políticas comerciales relacionadas con:

    - Cancelación de pedidos.
    - Devolución de productos.
    - Procesamiento de reembolsos.
    - Restricciones de productos en oferta.
    - Costos de envío de devoluciones.

Etapas principales:

    1. Definir el corpus de ejemplo.
    2. Dividir los documentos en fragmentos.
    3. Comprobar propiedades básicas de los chunks.
    4. Cargar la configuración de Gemini.
    5. Configurar el modelo de embeddings.
    6. Inicializar una colección persistente de ChromaDB.
    7. Indexar los documentos cuando la colección está vacía.
    8. Comprobar la cantidad de registros almacenados.

Configuración de fragmentación:

    Divisor:
        RecursiveCharacterTextSplitter.

    Tamaño objetivo:
        150 caracteres.

    Solapamiento objetivo:
        20 caracteres.

Modelo de embeddings:

    models/gemini-embedding-001

Colección vectorial:

    corpus_ejemplo

Directorio de persistencia:

    vectorstore_ejemplo

Consideraciones:

    Este archivo es un script de ejecución directa.
    Sus instrucciones se ejecutan al importar
    el módulo, ya que no utiliza una función main().

    La generación de embeddings requiere
    una clave GEMINI_API_KEY configurada.

    La indexación utiliza un servicio externo
    y puede consumir cuota de la API de Gemini.

    El script utiliza una colección persistente
    para conservar los registros entre ejecuciones.

IMPORTANTE:
    La verificación de integridad proporciona
    indicadores básicos sobre los fragmentos.

    No garantiza por sí sola que todos los datos
    originales se hayan conservado sin cambios.

    La comprobación final valida la cantidad
    de registros, no la equivalencia completa
    de su contenido.
"""

# ============================================================
# 1. DEPENDENCIA PARA FRAGMENTACIÓN DE DOCUMENTOS
# ============================================================

# RecursiveCharacterTextSplitter permite dividir textos
# en fragmentos intentando respetar separadores naturales.
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# 2. PASO 1: PREPARACIÓN DEL CORPUS
# ============================================================

# Paso 1: Reunir el corpus de ejemplo

# Corpus ficticio compuesto por cinco documentos.
#
# Cada elemento representa una política comercial
# independiente que posteriormente será fragmentada.
#
# Se conserva el contenido original de la práctica,
# incluyendo su redacción y caracteres.
corpus_ejemplo = [
    "Los pedidos se pueden cancelar dentro de las primeras 24 horas despues de "
    "realizados, sin costo adicional.",
    "Las devoluciones se aceptan hasta 30 dias despues de la entrega, siempre que "
    "el producto este sin usar.",
    "El reembolso se procesa en un plazo de 5 a 10 dias habiles despues de recibir "
    "el producto devuelto.",
    "Los productos en oferta o liquidacion no tienen devolucion, salvo defecto de "
    "fabrica.",
    "El envio de una devolucion corre por cuenta del cliente, excepto cuando el "
    "producto llego danado.",
]


# ============================================================
# 3. PASO 2: FRAGMENTACIÓN DEL CORPUS
# ============================================================

# Paso 2: Dividir los documentos en chunks

# Configura un divisor recursivo de LangChain.
#
# chunk_size=150:
#     Establece el tamaño objetivo de cada fragmento.
#
# chunk_overlap=20:
#     Establece el solapamiento objetivo entre
#     fragmentos consecutivos de un mismo documento.
#
# El resultado depende de la estructura del texto
# y de los separadores utilizados por la biblioteca.
splitter = RecursiveCharacterTextSplitter(
    chunk_size=150,
    chunk_overlap=20,
)

# Convierte los textos del corpus en documentos
# de LangChain después de aplicar la fragmentación.
#
# Cada elemento resultante contiene, entre otros
# atributos, la propiedad page_content.
chunks = splitter.create_documents(corpus_ejemplo)

# ------------------------------------------------------------
# 3.1. CANTIDAD DE FRAGMENTOS
# ------------------------------------------------------------

# Muestra el número de chunks generados.
print(f"{len(chunks)} chunks generados")

# ------------------------------------------------------------
# 3.2. INSPECCIÓN DE LOS FRAGMENTOS
# ------------------------------------------------------------

# Recorre los chunks para mostrar su contenido
# y la cantidad de caracteres de cada uno.
#
# enumerate() comienza en cero porque
# no se especifica un valor inicial diferente.
for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i} ({len(chunk.page_content)} caracteres) ---")
    print(chunk.page_content)


# ============================================================
# 4. VERIFICACIÓN BÁSICA DE INTEGRIDAD
# ============================================================

# Paso extra: verificar la integridad de los chunks

# ------------------------------------------------------------
# 4.1. IDENTIFICACIÓN DE FRAGMENTOS VACÍOS
# ------------------------------------------------------------

# Recupera los índices de los fragmentos cuyo contenido
# está vacío o contiene únicamente espacios en blanco.
#
# strip() elimina espacios y saltos de línea
# al comienzo y al final antes de comprobar el contenido.
vacios = [
    i for i, chunk in enumerate(chunks)
    if not chunk.page_content.strip()
]

# ------------------------------------------------------------
# 4.2. IDENTIFICACIÓN DE CONTENIDO DUPLICADO
# ------------------------------------------------------------

# Extrae el contenido textual de todos los fragmentos.
textos = [chunk.page_content for chunk in chunks]

# Compara la cantidad total de fragmentos
# con la cantidad de textos únicos.
#
# set(textos) elimina las cadenas duplicadas.
#
# El resultado será True si existen
# al menos dos fragmentos con contenido idéntico.
hay_duplicados = len(textos) != len(set(textos))

# ------------------------------------------------------------
# 4.3. COMPARACIÓN DE CANTIDADES DE CARACTERES
# ------------------------------------------------------------

# Suma los caracteres de todos los chunks generados.
#
# Si existen solapamientos, algunos caracteres
# podrían contabilizarse más de una vez.
total_chars_chunks = sum(len(chunk.page_content) for chunk in chunks)

# Calcula la cantidad de caracteres
# de los documentos originales.
total_chars_corpus = sum(len(documento) for documento in corpus_ejemplo)

# ------------------------------------------------------------
# 4.4. PRESENTACIÓN DE INDICADORES
# ------------------------------------------------------------

# Muestra los resultados de la revisión básica.
print("\n--- Verificación de integridad ---")
print("Chunks vacíos:", vacios)
print("Hay duplicados:", hay_duplicados)
print("Total de caracteres en los chunks:", total_chars_chunks)
print("Total de caracteres en el corpus original:", total_chars_corpus)


# ============================================================
# 5. PASO 3: CONFIGURACIÓN DE EMBEDDINGS Y PERSISTENCIA
# ============================================================

# Paso 3: Configurar embeddings y persistencia

# os permite consultar variables de entorno
# y construir rutas absolutas del sistema.
import os

# load_dotenv carga las variables definidas
# en el archivo .env del entorno.
from dotenv import load_dotenv

# Adaptador de LangChain para generar embeddings
# mediante los modelos de Google Gemini.
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Integración de ChromaDB con LangChain.
#
# Permite almacenar documentos y sus vectores
# en una colección persistente.
from langchain_chroma import Chroma

# ------------------------------------------------------------
# 5.1. CARGA DE VARIABLES DE ENTORNO
# ------------------------------------------------------------

# Busca y carga la configuración del archivo .env.
load_dotenv()

# ------------------------------------------------------------
# 5.2. VALIDACIÓN DE LA CLAVE DE GEMINI
# ------------------------------------------------------------

# Comprueba que GEMINI_API_KEY esté disponible
# y tenga un valor no vacío.
#
# Si no existe, detiene la ejecución
# antes de configurar el modelo de embeddings.
if not os.getenv("GEMINI_API_KEY"):
    raise SystemExit(
        "Falta GEMINI_API_KEY en el archivo .env"
    )

# ------------------------------------------------------------
# 5.3. CONFIGURACIÓN DEL MODELO DE EMBEDDINGS
# ------------------------------------------------------------

# Inicializa la integración de embeddings
# utilizando el modelo especificado de Gemini.
#
# La instancia se utilizará posteriormente
# para convertir los documentos en vectores.
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

# ------------------------------------------------------------
# 5.4. DIRECTORIO DE PERSISTENCIA
# ------------------------------------------------------------

# Construye la ruta absoluta del directorio
# donde ChromaDB almacenará sus datos.
#
# La ruta relativa se resuelve respecto
# al directorio de trabajo actual.
PERSIST_DIR = os.path.abspath("vectorstore_ejemplo")

# ------------------------------------------------------------
# 5.5. RESUMEN DE CONFIGURACIÓN
# ------------------------------------------------------------

# Presenta la configuración utilizada
# para la indexación del corpus.
#
# No imprime el valor de la clave API.
print("\n--- Configuración de indexación ---")
print("Modelo:", "models/gemini-embedding-001")
print("Directorio:", PERSIST_DIR)
print("Colección:", "corpus_ejemplo")
print("API key configurada:", True)


# ============================================================
# 6. PASO 4: INDEXACIÓN VECTORIAL CON CHROMADB
# ============================================================

# Paso 4: Generar embeddings y persistirlos en ChromaDB

# ------------------------------------------------------------
# 6.1. INICIALIZACIÓN DE LA COLECCIÓN
# ------------------------------------------------------------

# Inicializa la integración de ChromaDB.
#
# collection_name:
#     Identifica la colección del corpus de ejemplo.
#
# embedding_function:
#     Proporciona el modelo que generará
#     los vectores de los documentos.
#
# persist_directory:
#     Define el almacenamiento persistente.
#
# Si la colección ya existe, la integración
# puede acceder a sus registros anteriores.
db = Chroma(
    collection_name="corpus_ejemplo",
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)

# ------------------------------------------------------------
# 6.2. CONSULTA DE REGISTROS EXISTENTES
# ------------------------------------------------------------

# Obtiene la cantidad de registros
# almacenados actualmente en la colección.
#
# _collection es un atributo interno
# utilizado por la integración de Chroma.
registros_existentes = db._collection.count()

# ------------------------------------------------------------
# 6.3. INDEXACIÓN CONDICIONAL
# ------------------------------------------------------------

# Solo genera embeddings e incorpora documentos
# cuando la colección no contiene registros.
if registros_existentes == 0:

    # Informa el inicio de la generación de embeddings.
    print("\nGenerando embeddings con Gemini...")

    # Genera los embeddings de los chunks
    # y los incorpora a la colección persistente.
    #
    # Esta operación puede realizar solicitudes
    # al servicio externo de Gemini.
    db.add_documents(chunks)

    # Informa que la operación terminó
    # sin generar una excepción.
    print("Indexación realizada correctamente.")

else:

    # Si ya existen registros, evita añadir
    # nuevamente el corpus de ejemplo.
    print("\nLa colección ya contiene registros.")
    print("Se omite la indexación para evitar duplicados.")

# ------------------------------------------------------------
# 6.4. COMPROBACIÓN POSTERIOR A LA INDEXACIÓN
# ------------------------------------------------------------

# Consulta nuevamente la cantidad de registros.
#
# Esto permite comparar el estado final
# con la cantidad de chunks preparados.
total_registros = db._collection.count()

# Muestra el número de registros almacenados.
print("Registros almacenados:", total_registros)

# ------------------------------------------------------------
# 6.5. VALIDACIÓN DE LA CANTIDAD DE REGISTROS
# ------------------------------------------------------------

# Comprueba que el número de registros
# coincida con la cantidad de chunks generados.
#
# Esta validación se realiza tanto después
# de una indexación nueva como cuando
# la colección ya contenía registros.
if total_registros != len(chunks):
    raise RuntimeError(
        f"Se esperaban {len(chunks)} registros, "
        f"pero se encontraron {total_registros}."
    )
