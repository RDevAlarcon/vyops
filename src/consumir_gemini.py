
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
import time
import math 
import json
import re
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env del proyecto.
# Las credenciales reales no deben almacenarse en Git.
load_dotenv()

# Configuración del proveedor de inteligencia artificial.
# Se centraliza para facilitar futuros cambios de modelo.
MODELO = "gemini-3.5-flash-lite"

# tarifas para el modelo gemini-3.5-flash-lite segun gemini pricing: https://ai.google.dev/gemini-api/docs/pricing?utm_source=chatgpt.com&hl=es-419#standard_7
PRECIO_ENTRADA_MILLON = 0.30
PRECIO_SALIDA_MILLON = 2.50

#MODELO = "gemini-3.6-flash"

# tarifas para el modelo gemini-3.6-flash segun gemini pricing: https://ai.google.dev/gemini-api/docs/pricing?utm_source=chatgpt.com&hl=es-419#gemini-3.6-flash
#PRECIO_ENTRADA_MILLON = 0.75
#PRECIO_SALIDA_MILLON = 3.75

# Tarifas ficticias por millón de tokens para fines académicos.
#PRECIO_ENTRADA_MILLON = 0.50
#PRECIO_SALIDA_MILLON = 2.00
URL_GEMINI = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODELO}:generateContent"
)
MAX_INTENTOS = 3

def armar_peticion(
    pregunta: str,
    system_instruction: str | None = None,
    response_schema: dict | None = None,
) -> tuple[str, dict, dict]:
    """Valida los datos y prepara una solicitud para Gemini.

    Args:
        pregunta: Mensaje concreto del usuario.
        system_instruction: Instrucciones permanentes del asistente.
        response_schema: Esquema JSON esperado para la respuesta.

    Returns:
        Tupla con la URL, los encabezados HTTP y el cuerpo JSON.

    Raises:
        ValueError: Si los datos de entrada o la API key son inválidos.
    """
    # Validamos la pregunta antes de consultar al proveedor.
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise ValueError("La pregunta debe contener texto válido.")

    if system_instruction is not None:
        if (
            not isinstance(system_instruction, str)
            or not system_instruction.strip()
        ):
            raise ValueError(
                "La instrucción de sistema debe contener texto válido."
            )

    if response_schema is not None:
        if not isinstance(response_schema, dict) or not response_schema:
            raise ValueError(
                "El esquema de respuesta debe ser un diccionario válido."
            )

    # La credencial permanece fuera del código fuente.
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or not api_key.strip():
        raise ValueError(
            "Falta configurar GEMINI_API_KEY en el archivo .env."
        )

    encabezados = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    # El mensaje del usuario cambia en cada solicitud.
    cuerpo = {
        "contents": [
            {
                "parts": [
                    {"text": pregunta.strip()}
                ]
            }
        ]
    }

    # Las instrucciones permanentes van separadas del mensaje.
    if system_instruction is not None:
        cuerpo["systemInstruction"] = {
            "parts": [
                {"text": system_instruction.strip()}
            ]
        }

    # Cuando se solicita JSON, aplicamos el esquema desde la API.
    if response_schema is not None:
        cuerpo["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
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
        # Reintentamos hasta tres veces cuando Gemini responde
        # con HTTP 429, HTTP 503 o supera el tiempo de espera.
        for intento in range(MAX_INTENTOS):
            try:
                respuesta = requests.post(
                    url,
                    headers=encabezados,
                    json=cuerpo,
                    timeout=30,
                )

                # Si la respuesta es correcta, terminamos el ciclo.
                respuesta.raise_for_status()
                break

            except requests.exceptions.Timeout:
                if intento == MAX_INTENTOS - 1:
                    raise

                espera = 2 ** (intento + 1)

                print(
                    f"Gemini tardó demasiado en responder. "
                    f"Reintentando en {espera} segundos "
                    f"(intento {intento + 2}/{MAX_INTENTOS})."
                )

                time.sleep(espera)

            except requests.exceptions.HTTPError as error:
                codigo = error.response.status_code

                # Solo reintentamos ante límites de solicitudes
                # o indisponibilidad temporal del proveedor.
                if codigo not in (429, 503):
                    raise

                # Si agotamos los intentos, el error pasa
                # al manejador HTTP que ya tenemos.
                if intento == MAX_INTENTOS - 1:
                    raise

                # Espera exponencial: 2 segundos y luego 4.
                espera = 2 ** (intento + 1)

                # Si Gemini indica Retry-After en segundos,
                # respetamos ese valor cuando sea mayor.
                retry_after = error.response.headers.get("Retry-After")

                if retry_after:
                    try:
                        espera = max(espera, float(retry_after))
                    except ValueError:
                        pass

                # Evitamos esperas indefinidas.
                espera = min(espera, 60)

                print(
                    f"Gemini respondió HTTP {codigo}. "
                    f"Reintentando en {espera:g} segundos "
                    f"(intento {intento + 2}/{MAX_INTENTOS})."
                )

                time.sleep(espera)


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
        if codigo == 400:
            mensaje = (
                "La solicitud enviada a Gemini no es válida. "
                "Revisa los parámetros y el formato de los datos."
            )
        elif codigo in (401, 403):
            mensaje = "La API rechazó la autenticación o el acceso."
        elif codigo == 404:
            mensaje = (
                "El modelo o recurso solicitado no está disponible "
                "en el endpoint configurado."
            )
        elif codigo == 429:
            mensaje = "El servicio alcanzó su límite de solicitudes."
        elif codigo == 503:
            detalle = error.response.text[:1000]
            mensaje = (
                "El servicio de IA respondió HTTP 503. "
                f"Detalle del proveedor: {detalle}"
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


def parsear_respuesta_json(
    texto: str,
    claves_esperadas: list[str] | None = None,
) -> dict:
    """Convierte una respuesta del modelo en un diccionario validado.

    Args:
        texto: Respuesta textual generada por Gemini.
        claves_esperadas: Claves obligatorias del resultado.

    Returns:
        Diccionario con los datos interpretados.

    Raises:
        ValueError: Si la respuesta no es JSON válido o no
            contiene la estructura esperada.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("La respuesta del modelo está vacía.")

    # Eliminamos espacios y delimitadores Markdown opcionales.
    texto_limpio = texto.strip()
    texto_limpio = re.sub(
        r"^```(?:json)?\s*",
        "",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    texto_limpio = re.sub(
        r"\s*```$",
        "",
        texto_limpio,
    )

    # Interpretamos el texto como JSON.
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError as error:
        raise ValueError(
            "La respuesta del modelo no contiene JSON válido."
        ) from error

    # Para esta actividad esperamos un objeto JSON.
    if not isinstance(datos, dict):
        raise ValueError(
            "La respuesta JSON debe contener un objeto."
        )

    # Verificamos las claves requeridas.
    if claves_esperadas is not None:
        if not isinstance(claves_esperadas, list) or not all(
            isinstance(clave, str) and clave
            for clave in claves_esperadas
        ):
            raise ValueError("La lista de claves esperadas es inválida.")

        faltantes = [
            clave
            for clave in claves_esperadas
            if clave not in datos
        ]

        if faltantes:
            raise ValueError(
                f"La respuesta no contiene las claves: {faltantes}"
            )

    return datos


def extraer_uso_tokens(datos: dict) -> dict:
    """Extrae las métricas de consumo de tokens de Gemini.
       Distingue los tokens de respuesta visible de los tokens
       utilizados para el razonamiento interno del modelo.

    Args:
        datos: Respuesta JSON del proveedor.

    Returns:
        Diccionario con los tokens de entrada, salida y totales.

    Nota:
        Si Gemini no incluye usageMetadata, los valores
        se mantienen como None para evitar inventar consumo.
    """
    metadata = datos.get("usageMetadata") or {}

    return {
        "tokens_entrada": metadata.get("promptTokenCount"),
        "tokens_salida": metadata.get("candidatesTokenCount"),
        "tokens_razonamiento": metadata.get("thoughtsTokenCount"),
        "tokens_totales": metadata.get("totalTokenCount"),
    }


def obtener_dato_de_prueba(pregunta: str) -> dict:
    """Coordina el proceso completo de consulta a Gemini.

    Args:
        pregunta: Consulta que se enviará al modelo.

    Returns:
        devuelve un diccionario con respuesta, consumo, tiempo y costo estimado.

    Diseño:
        Esta función orquesta las demás sin duplicar su lógica.
        Cada función conserva una responsabilidad específica.

    Nota:
        El tiempo medido corresponde a la comunicación
        con Gemini, incluyendo la espera de su respuesta.
        No representa exclusivamente el procesamiento
        interno del modelo.
    """
    # Paso 1: validar y construir la petición.
    url, encabezados, cuerpo = armar_peticion(pregunta)
    # Medimos el tiempo de la petición al proveedor.
    inicio = time.perf_counter()

    # Paso 2: comunicarse con el proveedor.
    datos = enviar_peticion(url, encabezados, cuerpo)

    duracion = time.perf_counter() - inicio

    # Paso 3: recuperar el texto generado.
    return {
        "respuesta": extraer_texto(datos),
        "uso_tokens": extraer_uso_tokens(datos),
        "tiempo_respuesta_segundos": round(duracion, 3),
        "costo_estimado_usd": calcular_costo(
            datos,
            PRECIO_ENTRADA_MILLON,
            PRECIO_SALIDA_MILLON,
        ),
    }



def calcular_costo(
    datos: dict,
    precio_entrada: float,
    precio_salida: float,
) -> float:
    """Calcula el costo estimado de una consulta a Gemini.

    Args:
        datos: Respuesta JSON del proveedor.
        precio_entrada: Precio USD por millón de tokens de entrada.
        precio_salida: Precio USD por millón de tokens de salida.

    Returns:
        Costo estimado en USD según las tarifas proporcionadas.

    Raises:
        ValueError: Si los precios no son válidos.
        RuntimeError: Si faltan las métricas necesarias.
    """

    # Verificamos que las tarifas sean números válidos.
    if any(
        isinstance(precio, bool)
        or not isinstance(precio, (int, float))
        or not math.isfinite(precio)
        or precio < 0
        for precio in (precio_entrada, precio_salida)
    ):
        raise ValueError(
            "Los precios deben ser números finitos no negativos."
        )

    # Recuperamos los tokens informados por Gemini.
    uso = extraer_uso_tokens(datos)

    tokens_entrada = uso["tokens_entrada"]
    tokens_salida = uso["tokens_salida"]
    tokens_razonamiento = uso["tokens_razonamiento"]

    # No calculamos costos con métricas inexistentes o inválidas.
    if any(
        type(tokens) is not int or tokens < 0
        for tokens in (tokens_entrada, tokens_salida)
    ):
        raise RuntimeError(
            "No se encontraron métricas válidas para calcular el costo."
        )
    # Algunos modelos no utilizan razonamiento interno.
    if tokens_razonamiento is None:
        tokens_razonamiento = 0

    if type(tokens_razonamiento) is not int or tokens_razonamiento < 0:
        raise RuntimeError(
            "El consumo de tokens de razonamiento no es válido."
        )

    # Los tokens de razonamiento se facturan como salida.
    tokens_salida_facturables = tokens_salida + tokens_razonamiento

    # Las tarifas se expresan por millón de tokens.
    costo_entrada = tokens_entrada * (precio_entrada / 1_000_000)
    costo_salida = tokens_salida_facturables * (precio_salida / 1_000_000)

    return costo_entrada + costo_salida

    

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

        print("\nRespuesta de Gemini:")
        print(resultado["respuesta"])

        print("\nConsumo de tokens:")
        for nombre, cantidad in resultado["uso_tokens"].items():
            print(f"  {nombre}: {cantidad}")

        print(
            "\nTiempo de respuesta: "
            f"{resultado['tiempo_respuesta_segundos']:.3f} segundos"
        )
        # Mostramos el costo calculado con tarifas oficiales de referencia.
        print(
            "\nCosto estimado (tarifas oficiales de referencia): "
            f"USD {resultado['costo_estimado_usd']:.8f}"
        )

    except (ValueError, RuntimeError) as error:
        # Mostramos un mensaje claro sin detener el programa
        # con un traceback para los errores previstos.
        print(f"No se pudo completar la operación: {error}")
