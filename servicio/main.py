"""Aplicación FastAPI y endpoints públicos de VyOps."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from servicio import config, logica
from servicio.errores import (
    manejar_validacion,
    manejar_error_http,
    manejar_error_interno,
    proteger_errores_internos,
)

from servicio.esquemas import (
    Consulta,
    Respuesta,
    Salud,
    ErrorRespuesta,
)


app = FastAPI(
    title="VyOps API",
    version="0.1.0",
    description=(
        "Asistente documental municipal basado en RAG, "
        "con fuentes verificables y trazabilidad operacional."
    ),
)


# Registro centralizado de los manejadores de excepciones.
app.add_exception_handler(
    RequestValidationError,
    manejar_validacion,
)

app.add_exception_handler(
    HTTPException,
    manejar_error_http,
)

app.add_exception_handler(
    Exception,
    manejar_error_interno,
)

# Protege los registros del servidor ante excepciones
# inesperadas durante el procesamiento de solicitudes.
app.middleware("http")(proteger_errores_internos)

@app.get(
    "/salud",
    response_model=Salud,
    tags=["sistema"],
    summary="Comprobar el servicio",
    responses={
        500: {
            "model": ErrorRespuesta,
            "description": "Error interno del servicio.",
        },
    },
)
def salud() -> Salud:
    """Comprueba el estado operativo y la configuración del servicio."""
    return Salud(
        **logica.obtener_salud(),
        entorno=config.entorno(),
        modelo=(
            "configurado"
            if config.modelo_configurado()
            else "sin clave"
        ),
    )


@app.post(
    "/consultas",
    response_model=Respuesta,
    tags=["consultas"],
    summary="Consultar el corpus documental municipal",
    responses={
        422: {
            "model": ErrorRespuesta,
            "description": "La solicitud contiene datos inválidos.",
        },
        500: {
            "model": ErrorRespuesta,
            "description": "Error interno durante el procesamiento.",
        },
    },
)
def consultar(consulta: Consulta) -> Respuesta:
    """Responde una pregunta documental e identifica sus fuentes."""
    return Respuesta(**logica.responder(consulta.pregunta))