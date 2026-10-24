"""Cliente modular de la API de Gemini para VyOps.

Bloque 12 — SkillNest.

Proporciona una interfaz pública para consultar el modelo Gemini.
Reutiliza las funciones desarrolladas en Gate 1 para construir
solicitudes, enviarlas con manejo de errores y reintentos,
y extraer el texto de las respuestas.

Incluye una prueba manual ejecutable para verificar la comunicación
real con el servicio.
"""

from src.consumir_gemini import (
    armar_peticion,
    enviar_peticion,
    extraer_texto,
)


def consultar_modelo(
    pregunta: str,
    system_instruction: str | None = None,
) -> str:
    """Consulta Gemini mediante una única interfaz pública.

    Args:
        pregunta: Consulta que se enviará al modelo.
        system_instruction: Instrucción de sistema opcional.

    Returns:
        Texto generado por Gemini.

    Raises:
        ValueError: Si la consulta o sus parámetros son inválidos.
        RuntimeError: Si falla la comunicación, se agotan los
            reintentos o no puede procesarse la respuesta.
    """
    url, encabezados, cuerpo = armar_peticion(
        pregunta,
        system_instruction,
    )

    respuesta = enviar_peticion(
        url,
        encabezados,
        cuerpo,
    )

    return extraer_texto(respuesta)

if __name__ == "__main__":
    try:
        respuesta = consultar_modelo("¿Cuál es la capital de Noruega?")
        print(f"Respuesta de Gemini: {respuesta}")

    except ValueError as error:
        print(f"Error de configuración: {error}")

    except RuntimeError as error:
        print(f"Error al consultar Gemini: {error}")