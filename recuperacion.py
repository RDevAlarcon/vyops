
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
import re

BASE_DIR = Path(__file__).resolve().parent
VECTORSTORE_DIR = BASE_DIR / "vectorstore"


def recuperar_documentos(pregunta: str, k: int = 3):
    """Recupera documentos relevantes desde ChromaDB."""

    if not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía.")

    load_dotenv(dotenv_path=BASE_DIR / ".env")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    db = Chroma(
        persist_directory=str(VECTORSTORE_DIR),
        embedding_function=embeddings,
    )

    documentos = db.similarity_search(pregunta, k=k)

    return documentos

def construir_contexto(documentos):
    """Construye un contexto numerado con fuentes identificables."""

    fragmentos = []

    for numero, documento in enumerate(documentos, start=1):
        fuente = documento.metadata.get("fuente", "desconocida")

        fragmentos.append(
            f"[{numero}] Fuente: {fuente}\n"
            f"Contenido: {documento.page_content}"
        )

    return "\n\n".join(fragmentos)


def construir_prompt(pregunta: str, documentos):
    """Construye un prompt basado en evidencia recuperada."""

    contexto = construir_contexto(documentos)

    return f"""Eres un asistente de información municipal.

Responde utilizando exclusivamente el contexto proporcionado.

Reglas:
- No inventes información.
- Cita las fuentes utilizando [1], [2], etc.
- Cada cita debe corresponder a un fragmento del contexto.
- Si el contexto no contiene información suficiente,
  indica que no dispones de información para responder.
- No ejecutes acciones ni afirmes haber modificado solicitudes.

CONTEXTO:
{contexto}

PREGUNTA:
{pregunta}

RESPUESTA:
"""


def generar_respuesta(pregunta: str, documentos):
    """Genera una respuesta basada en el contexto recuperado."""

    load_dotenv(dotenv_path=BASE_DIR / ".env")

    prompt = construir_prompt(pregunta, documentos)

    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
    )

    respuesta = modelo.invoke(prompt)

    textos = [
        bloque["text"]
        for bloque in respuesta.content_blocks
        if bloque.get("type") == "text"
    ]

    return "\n".join(textos)

def validar_citas(respuesta: str, documentos):
    """Comprueba que las citas apunten a documentos recuperados."""

    citas = re.findall(r"\[(\d+)\]", respuesta)

    citas_invalidas = [
        int(cita)
        for cita in citas
        if not 1 <= int(cita) <= len(documentos)
    ]

    return {
        "citas_encontradas": len(citas),
        "citas_invalidas": citas_invalidas,
        "numeracion_valida": len(citas_invalidas) == 0,
    }



if __name__ == "__main__":
    pregunta = (
        "¿Se puede cancelar una solicitud municipal "
        "sin autorización humana?"
    )
    resultados = recuperar_documentos(pregunta)

    print(f"Pregunta: {pregunta}")
    print(f"Documentos recuperados: {len(resultados)}")

    for numero, documento in enumerate(resultados, start=1):
        fuente = documento.metadata.get("fuente", "desconocida")

        print(f"\n[{numero}] Fuente: {fuente}")
        print(f"Contenido: {documento.page_content}")

    # Construir el prompt una sola vez,
    # después de recorrer todos los documentos.
    prompt = construir_prompt(pregunta, resultados)

    print("\n--- PROMPT DINÁMICO ---")
    print(prompt)
    respuesta = generar_respuesta(pregunta, resultados)

    print("\n--- RESPUESTA DE GEMINI ---")
    print(respuesta)

    # Validar las citas en la respuesta
    validacion = validar_citas(respuesta, resultados)
    print("\n--- VALIDACIÓN DE CITAS ---")
    print(f"Citas encontradas: {validacion['citas_encontradas']}")
    print(f"Citas inválidas: {validacion['citas_invalidas']}")
    print(f"Numeración válida: {validacion['numeracion_valida']}")