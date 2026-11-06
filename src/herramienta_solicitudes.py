
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class ArgumentosConsultaSolicitud(BaseModel):
    """Define los argumentos para consultar una solicitud municipal."""

    numero_solicitud: str = Field(
        description=(
            "Identificador de la solicitud municipal, "
            "por ejemplo: SOL-12345."
        ),
        min_length=1,
    )

    incluir_historial: bool = Field(
        default=False,
        description=(
            "Si es True, incluye el historial completo "
            "de estados de la solicitud. "
            "Si es False, muestra solamente el estado actual."
        ),
    )

SOLICITUDES = {
    "SOL-12345": {
        "actual": "En revisión por la unidad municipal.",
        "historial": [
            "Solicitud recibida.",
            "Documentación validada.",
            "En revisión por la unidad municipal.",
        ],
    },
}


@tool(
    "consultar_estado_solicitud",
    args_schema=ArgumentosConsultaSolicitud,
)

def consultar_estado_solicitud(
    numero_solicitud: str,
    incluir_historial: bool = False,
) -> str:
    """Consulta el estado de una solicitud municipal simulada."""
    solicitud = SOLICITUDES.get(numero_solicitud)

    if solicitud is None:
        return (
            f"No se encontró la solicitud {numero_solicitud} "
            "en los datos de prueba."
        )

    if not incluir_historial:
        return solicitud["actual"]

    historial = ", ".join(solicitud["historial"])

    return f"{solicitud['actual']} (historial: {historial})"
