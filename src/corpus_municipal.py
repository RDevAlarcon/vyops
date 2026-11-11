
"""Corpus ficticio para practicar RAG en VyOps."""

from langchain_core.documents import Document


def obtener_corpus_municipal() -> list[Document]:
    """Devuelve cinco documentos municipales ficticios."""
    contenidos = [
        (
            "Las solicitudes municipales se registran con un "
            "identificador único para consultar su estado."
        ),
        (
            "Una solicitud puede encontrarse pendiente, "
            "en revisión, aprobada o rechazada."
        ),
        (
            "Para consultar una solicitud, el asistente "
            "necesita conocer su identificador."
        ),
        (
            "La cancelación de una solicitud requiere "
            "autorización humana antes de ejecutarse."
        ),
        (
            "El asistente registra las decisiones relevantes "
            "para facilitar su posterior auditoría."
        ),
    ]

    return [
        Document(
            page_content=contenido,
            metadata={
                "fuente": "corpus_ficticio_vyops",
                "documento": indice,
            },
        )
        for indice, contenido in enumerate(contenidos, start=1)
    ]
