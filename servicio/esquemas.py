"""Contratos de entrada y salida de la API HTTP de VyOps."""

from pydantic import BaseModel, ConfigDict, Field


class Salud(BaseModel):
    """Estado operativo y configuración de la API."""

    estado: str = Field(
        description="Estado operativo del servicio.",
        examples=["ok"],
    )

    entorno: str = Field(
        description="Entorno de ejecución del servicio.",
        examples=["desarrollo", "produccion"],
    )

    modelo: str = Field(
        description="Disponibilidad de la clave del modelo.",
        examples=["configurado", "sin clave"],
    )


class Consulta(BaseModel):
    """Solicitud validada de consulta documental municipal."""

    # Elimina los espacios exteriores antes de validar
    # la longitud de la pregunta.
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    pregunta: str = Field(
        min_length=3,
        max_length=500,
        description=(
            "Pregunta del usuario en lenguaje natural. "
            "Debe contener entre 3 y 500 caracteres."
        ),
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

class DetalleError(BaseModel):
    """Detalle individual de un error de validación."""

    campo: str = Field(
        description="Campo o ubicación donde se produjo el error."
    )

    mensaje: str = Field(
        description="Descripción segura del error detectado."
    )


class ErrorRespuesta(BaseModel):
    """Contrato uniforme de errores HTTP de VyOps."""

    codigo: str = Field(
        description="Código identificador del error.",
        examples=["VALIDACION_ERROR"],
    )

    mensaje: str = Field(
        description="Descripción general del error.",
        examples=["La solicitud contiene datos inválidos."],
    )

    detalles: list[DetalleError] = Field(
        default_factory=list,
        description="Detalles adicionales del error, cuando corresponda.",
    )