"""Integración entre la API HTTP y el servicio RAG de VyOps."""

from threading import Lock


# La captura de auditoría existente requiere consultas serializadas.
_bloqueo_consultas = Lock()


def obtener_salud() -> dict[str, str]:
    """Comprueba la disponibilidad de la capa de servicio."""
    return {"estado": "ok"}


def responder(pregunta: str) -> dict:
    """Ejecuta una consulta documental mediante el RAG existente."""

    # Importación diferida: permite arrancar la API y consultar
    # su documentación sin inicializar Gemini ni ChromaDB.
    with _bloqueo_consultas:
        from servicio_vyops_rag import ejecutar_consulta

        resultado = ejecutar_consulta(pregunta)

        return {
            "trace_id": resultado["trace_id"],
            "respuesta": resultado["respuesta"],
            "fuentes": resultado["fuentes"],
            "estado": resultado["estado"],
        }