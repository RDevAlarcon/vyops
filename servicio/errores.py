"""Manejadores centralizados de errores HTTP de VyOps."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from servicio.esquemas import DetalleError, ErrorRespuesta
from collections.abc import Awaitable, Callable

from starlette.responses import Response

logger = logging.getLogger(__name__)


# Mensajes controlados para evitar exponer datos de entrada.
MENSAJES_VALIDACION = {
    "missing": "El campo es obligatorio.",
    "string_type": "El campo debe ser una cadena de texto.",
    "string_too_short": "Debe contener al menos 3 caracteres.",
    "string_too_long": "Debe contener como máximo 500 caracteres.",
    "json_invalid": "El cuerpo de la solicitud no contiene JSON válido.",
}


def construir_error(
    estado_http: int,
    codigo: str,
    mensaje: str,
    detalles: list[DetalleError] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Construye una respuesta HTTP con el contrato común."""

    error = ErrorRespuesta(
        codigo=codigo,
        mensaje=mensaje,
        detalles=detalles or [],
    )

    return JSONResponse(
        status_code=estado_http,
        content=error.model_dump(mode="json"),
        headers=headers,
    )


async def manejar_validacion(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Transforma errores de validación en respuestas seguras."""

    detalles = []

    for error in exc.errors():
        ubicacion = error.get("loc", ())

        # No reproducir ubicaciones arbitrarias ni valores recibidos.
        campo = (
            "pregunta"
            if ubicacion == ("body", "pregunta")
            else "solicitud"
        )

        mensaje = MENSAJES_VALIDACION.get(
            error.get("type"),
            "El dato proporcionado no es válido.",
        )

        detalles.append(
            DetalleError(
                campo=campo,
                mensaje=mensaje,
            )
        )

    return construir_error(
        estado_http=422,
        codigo="VALIDACION_ERROR",
        mensaje="La solicitud contiene datos inválidos.",
        detalles=detalles,
    )


async def manejar_error_http(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Normaliza los errores HTTP sin revelar detalles internos."""

    errores = {
        404: (
            "NO_ENCONTRADO",
            "El recurso solicitado no existe.",
        ),
        405: (
            "METODO_NO_PERMITIDO",
            "El método HTTP no está permitido.",
        ),
    }

    codigo, mensaje = errores.get(
        exc.status_code,
        ("ERROR_HTTP", "No fue posible procesar la solicitud."),
    )

    return construir_error(
        estado_http=exc.status_code,
        codigo=codigo,
        mensaje=mensaje,
        headers=exc.headers,
    )


async def manejar_error_interno(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Responde ante fallos inesperados sin revelar datos sensibles."""

    # No registrar el mensaje original ni el contenido de la solicitud.
    logger.error("Error interno durante el procesamiento HTTP.")

    return construir_error(
        estado_http=500,
        codigo="ERROR_INTERNO",
        mensaje="Ocurrió un error interno en el servicio.",
    )

async def proteger_errores_internos(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Intercepta fallos HTTP inesperados antes de llegar al servidor ASGI."""

    try:
        return await call_next(request)

    except Exception as exc:
        # Reutiliza el manejador centralizado sin propagar
        # la excepción original al servidor.
        return await manejar_error_interno(request, exc)