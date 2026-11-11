
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Paso 1: Reunir el corpus de ejemplo
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

# Paso 2: Dividir los documentos en chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=150,
    chunk_overlap=20,
)

chunks = splitter.create_documents(corpus_ejemplo)

print(f"{len(chunks)} chunks generados")

for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i} ({len(chunk.page_content)} caracteres) ---")
    print(chunk.page_content)

# Paso extra: verificar la integridad de los chunks

vacios = [
    i for i, chunk in enumerate(chunks)
    if not chunk.page_content.strip()
]

textos = [chunk.page_content for chunk in chunks]
hay_duplicados = len(textos) != len(set(textos))

total_chars_chunks = sum(len(chunk.page_content) for chunk in chunks)
total_chars_corpus = sum(len(documento) for documento in corpus_ejemplo)

print("\n--- Verificación de integridad ---")
print("Chunks vacíos:", vacios)
print("Hay duplicados:", hay_duplicados)
print("Total de caracteres en los chunks:", total_chars_chunks)
print("Total de caracteres en el corpus original:", total_chars_corpus)


# Paso 3: Configurar embeddings y persistencia

import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise SystemExit(
        "Falta GEMINI_API_KEY en el archivo .env"
    )

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

PERSIST_DIR = os.path.abspath("vectorstore_ejemplo")

print("\n--- Configuración de indexación ---")
print("Modelo:", "models/gemini-embedding-001")
print("Directorio:", PERSIST_DIR)
print("Colección:", "corpus_ejemplo")
print("API key configurada:", True)

# Paso 4: Generar embeddings y persistirlos en ChromaDB

db = Chroma(
    collection_name="corpus_ejemplo",
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)

registros_existentes = db._collection.count()

if registros_existentes == 0:
    print("\nGenerando embeddings con Gemini...")
    db.add_documents(chunks)
    print("Indexación realizada correctamente.")
else:
    print("\nLa colección ya contiene registros.")
    print("Se omite la indexación para evitar duplicados.")

total_registros = db._collection.count()

print("Registros almacenados:", total_registros)

if total_registros != len(chunks):
    raise RuntimeError(
        f"Se esperaban {len(chunks)} registros, "
        f"pero se encontraron {total_registros}."
    )
