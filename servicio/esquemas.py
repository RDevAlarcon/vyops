"""Contratos de entrada y salida de la API HTTP de VyOps."""

from pydantic import BaseModel, Field


class Salud(BaseModel):
    """Estado de disponibilidad de la API."""

    estado: str = Field(
        description="Estado operativo del servicio.",
        examples=["ok"],
    )


class Consulta(BaseModel):
    """Solicitud de consulta documental municipal."""

    pregunta: str = Field(
        description="Pregunta del usuario en lenguaje natural.",
        examples=[
            "¿Cuál es el horario de atención presencial los viernes?"
        ],
    )


class Respuesta(BaseModel):
    """Respuesta documental con fuentes y trazabilidad."""

    trace_id: str = Field(
        description="Identificador único de trazabilidad de la consulta."
    )

    respuesta: str = Field(
        description="Respuesta generada a partir del corpus documental."
    )

    fuentes: list[str] = Field(
        description=(
            "Documentos que respaldan la respuesta. "
            "Lista vacía cuando no existe evidencia suficiente."
        )
    )

    estado: str = Field(
        description="Estado del procesamiento de la consulta.",
        examples=["respuesta_generada", "abstencion_segura"],
    )