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
    PRECIO_ENTRADA_MILLON,
    PRECIO_SALIDA_MILLON,
    armar_peticion,
    calcular_costo,
    enviar_peticion,
    extraer_texto,
)

from src.registro_costos import RegistroCostosSesion


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


def consultar_modelo_con_costos(
    pregunta: str,
    registro: RegistroCostosSesion,
    system_instruction: str | None = None,
) -> str:
    """Consulta Gemini y registra el costo estimado de la operación.

    Args:
        pregunta: Consulta que se enviará al modelo.
        registro: Registro de costos de la sesión correspondiente.
        system_instruction: Instrucción de sistema opcional.

    Returns:
        Texto generado por Gemini.

    Raises:
        ValueError: Si los parámetros son inválidos.
        RuntimeError: Si falla la consulta o el cálculo del costo.

    Nota:
        El costo se registra una sola vez por consulta exitosa,
        independientemente de los reintentos internos del cliente HTTP.
    """
    # Construimos y enviamos la solicitud mediante el cliente existente.
    url, encabezados, cuerpo = armar_peticion(
        pregunta,
        system_instruction,
    )

    datos = enviar_peticion(
        url,
        encabezados,
        cuerpo,
    )

    # Extraemos el texto y calculamos el costo de la respuesta.
    texto = extraer_texto(datos)

    costo = calcular_costo(
        datos,
        PRECIO_ENTRADA_MILLON,
        PRECIO_SALIDA_MILLON,
    )

    # Registramos el costo únicamente después de procesar la respuesta.
    registro.registrar_operacion(costo)

    return texto


if __name__ == "__main__":
    try:
        # Creamos un registro independiente para esta sesión.
        registro = RegistroCostosSesion()
        respuesta = consultar_modelo_con_costos("¿Cuál es la capital de Noruega?", registro,)
        # Mostramos la respuesta generada.
        print(f"Respuesta de Gemini: {respuesta}")
        # Consultamos el costo acumulado de la sesión.
        costo_total_sesion = registro.obtener_total()
        print(
            f"Costo acumulado de la sesión: "
            f"USD {costo_total_sesion:.8f}"
        )

    except ValueError as error:
        print(f"Error de configuración: {error}")

    except RuntimeError as error:
        print(f"Error al consultar Gemini: {error}")
