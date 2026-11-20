"""Preparacion local del corpus documental de VyOps.

Esta version NO genera embeddings ni modifica ChromaDB.
"""

from collections import Counter
from hashlib import sha256

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.corpus_municipal import obtener_corpus_municipal


CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

SEPARADORES = ["\n\n", "\n", ". ", " ", ""]


def preparar_documentos() -> tuple[list[Document], list[str]]:
    """Prepara fragmentos con identificadores estables."""

    documentos = obtener_corpus_municipal()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARADORES,
    )

    fragmentos = []
    identificadores = []

    for documento in documentos:
        partes = splitter.split_documents([documento])

        for posicion, fragmento in enumerate(partes, start=1):
            huella = sha256(
                fragmento.page_content.encode("utf-8")
            ).hexdigest()

            identificador = (
                f"{documento.metadata['id']}"
                f":{posicion:04d}"
                f":{huella}"
            )

            fragmento.metadata["chunk_id"] = identificador
            fragmento.metadata["chunk_index"] = posicion
            fragmento.metadata["content_sha256"] = huella

            fragmentos.append(fragmento)
            identificadores.append(identificador)

    return fragmentos, identificadores


def main() -> None:
    """Valida la preparacion documental sin indexar."""

    documentos = obtener_corpus_municipal()
    fragmentos, identificadores = preparar_documentos()

    duplicados = [
        identificador
        for identificador, cantidad in Counter(
            identificadores
        ).items()
        if cantidad > 1
    ]

    documentos_representados = {
        fragmento.metadata["id"]
        for fragmento in fragmentos
    }

    print("Documentos originales:", len(documentos))
    print("Chunks preparados:", len(fragmentos))
    print("IDs unicos:", len(set(identificadores)))
    print("Documentos representados:", len(documentos_representados))
    print("Duplicados:", len(duplicados))

    if duplicados:
        raise RuntimeError(
            "Se detectaron identificadores duplicados."
        )

    if len(documentos_representados) != len(documentos):
        raise RuntimeError(
            "No todos los documentos estan representados."
        )

    if not fragmentos:
        raise RuntimeError(
            "No se generaron fragmentos."
        )

    print("PASS: Preparacion documental completada.")
    print("ChromaDB: sin modificaciones.")
    print("Gemini: sin llamadas.")


if __name__ == "__main__":
    main()
