
"""Cliente HTTP de Google Gemini para el proyecto VyOps.

Unidad U1.3 — Especialización en Desarrollo con IA Generativa.

Responsabilidades del módulo:
    1. Validar las preguntas y preparar solicitudes HTTP.
    2. Comunicarse con la API de Google Gemini.
    3. Procesar las respuestas JSON del proveedor.
    4. Gestionar errores previsibles con mensajes comprensibles.

Arquitectura:
    Este módulo representa una primera integración con un proveedor
    de inteligencia artificial. En futuras unidades podrá integrarse
    al núcleo multiempresa de VyOps.

Seguridad:
    La credencial se obtiene desde variables de entorno y se envía
    mediante un encabezado HTTP, nunca como parámetro de la URL.
"""

import os
import requests
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env del proyecto.
# Las credenciales reales no deben almacenarse en Git.
load_dotenv()

# Configuración del proveedor de inteligencia artificial.
# Se centraliza para facilitar futuros cambios de modelo.
MODELO = "gemini-3.5-flash-lite"

URL_GEMINI = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODELO}:generateContent"
)

def armar_peticion(pregunta: str) -> tuple[str, dict, dict]:
    """Valida la entrada y prepara una solicitud para Gemini.

    Args:
        pregunta: Texto que el usuario desea enviar al modelo.

    Returns:
        Tupla con la URL, los encabezados HTTP y el cuerpo JSON.

    Raises:
        ValueError: Si la pregunta es inválida o falta la API key.

    Nota:
        La validación se realiza antes de llamar al proveedor para
        evitar solicitudes innecesarias.
    """
    # Una pregunta debe ser texto y contener caracteres distintos
    # de espacios en blanco.
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise ValueError("La pregunta debe contener texto válido.")

    # Obtiene la credencial desde el entorno local.
    # Nunca se incluye directamente en el código fuente.
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or not api_key.strip():
        raise ValueError(
            "Falta configurar GEMINI_API_KEY en el archivo .env."
        )

    # La autenticación se realiza mediante el encabezado HTTP.
    encabezados = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    # Construye el cuerpo con la estructura requerida por Gemini.
    cuerpo = {
        "contents": [
            {
                "parts": [
                    {"text": pregunta.strip()}
                ]
            }
        ]
    }

    return URL_GEMINI, encabezados, cuerpo


def enviar_peticion(
    url: str,
    encabezados: dict,
    cuerpo: dict,
) -> dict:
    """Envía la solicitud HTTP y procesa la respuesta JSON.

    Args:
        url: Endpoint del proveedor de IA.
        encabezados: Configuración HTTP y autenticación.
        cuerpo: Datos que se enviarán al modelo.

    Returns:
        Diccionario con la respuesta JSON del proveedor.

    Raises:
        RuntimeError: Si falla la conexión, se supera el tiempo
            de espera, ocurre un error HTTP o el JSON es inválido.

    Seguridad:
        No se imprimen credenciales ni encabezados de autenticación.
    """
    try:
        # timeout evita que una solicitud quede esperando
        # indefinidamente si el servicio no responde.
        respuesta = requests.post(
            url,
            headers=encabezados,
            json=cuerpo,
            timeout=30,
        )

        # Convierte respuestas HTTP en excepciones.
        respuesta.raise_for_status()

    except requests.exceptions.Timeout as error:
        raise RuntimeError(
            "El servicio tardó demasiado en responder."
        ) from error

    except requests.exceptions.ConnectionError as error:
        raise RuntimeError(
            "No se pudo conectar con el servicio de IA."
        ) from error

    except requests.exceptions.HTTPError as error:
        # Clasificamos los errores HTTP más relevantes para
        # entregar mensajes comprensibles al usuario.
        codigo = error.response.status_code

        if codigo in (401, 403):
            mensaje = "La API rechazó la autenticación o el acceso."
        elif codigo == 429:
            mensaje = "El servicio alcanzó su límite de solicitudes."
        elif codigo == 503:
            mensaje = (
                "El servicio de IA no está disponible temporalmente."
            )
        else:
            mensaje = (
                f"El servicio respondió con un error HTTP {codigo}."
            )
        # Conservamos la causa original para facilitar
        # el diagnóstico durante el desarrollo.
        raise RuntimeError(mensaje) from error

    except requests.exceptions.RequestException as error:
        # Captura otros errores de requests no contemplados arriba.
        raise RuntimeError(
            "Ocurrió un problema al enviar la solicitud."
        ) from error

    try:
        # Convierte la respuesta HTTP en un objeto Python.
        return respuesta.json()

    except requests.exceptions.JSONDecodeError as error:
        raise RuntimeError(
            "La respuesta del servicio no contiene JSON válido."
        ) from error


def extraer_texto(datos: dict) -> str:
    """Obtiene el texto generado desde la respuesta de Gemini.

    Args:
        datos: Diccionario JSON devuelto por el proveedor.

    Returns:
        Texto generado por el modelo de inteligencia artificial.

    Raises:
        RuntimeError: Si faltan campos, la estructura es incorrecta
            o el texto generado está vacío.

    Nota:
        Gemini puede devolver respuestas diferentes ante errores,
        bloqueos o resultados sin contenido generado.
    """
    try:
        # Ruta esperada dentro del JSON de Gemini:
        # candidates -> content -> parts -> text.
        texto = datos["candidates"][0]["content"]["parts"][0]["text"]

    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(
            "La respuesta no contiene texto generado "
            "en el formato esperado."
        ) from error

    # También validamos el contenido, no solo la estructura.
    if not isinstance(texto, str) or not texto.strip():
        raise RuntimeError(
            "El servicio devolvió una respuesta sin texto."
        )

    return texto


def obtener_dato_de_prueba(pregunta: str) -> str:
    """Coordina el proceso completo de consulta a Gemini.

    Args:
        pregunta: Consulta que se enviará al modelo.

    Returns:
        Respuesta del modelo como texto.

    Diseño:
        Esta función orquesta las demás sin duplicar su lógica.
        Cada función conserva una responsabilidad específica.
    """
    # Paso 1: validar y construir la petición.
    url, encabezados, cuerpo = armar_peticion(pregunta)

    # Paso 2: comunicarse con el proveedor.
    datos = enviar_peticion(url, encabezados, cuerpo)

    # Paso 3: recuperar el texto generado.
    return extraer_texto(datos)


if __name__ == "__main__":
    # Punto de entrada para ejecutar el módulo directamente.
    # Este bloque no se ejecuta cuando otro módulo importa
    # las funciones de este archivo.

    pregunta = (
        "Explica en una frase qué es un asistente "
        "de inteligencia artificial."
    )

    try:
        resultado = obtener_dato_de_prueba(pregunta)
        print(resultado)

    except (ValueError, RuntimeError) as error:
        # Mostramos un mensaje claro sin detener el programa
        # con un traceback para los errores previstos.
        print(f"No se pudo completar la operación: {error}")
