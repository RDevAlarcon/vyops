"""Cliente HTTP de Google Gemini para el proyecto VyOps.

Proyecto académico — Especialización en Desarrollo con IA Generativa.
Unidad 1: Integración de modelos y evaluación de respuestas.

Responsabilidades:
    1. Validar preguntas, instrucciones de sistema y esquemas JSON.
    2. Construir solicitudes HTTP autenticadas para Google Gemini.
    3. Enviar peticiones y gestionar errores de conexión y HTTP.
    4. Reintentar solicitudes ante fallos transitorios del proveedor.
    5. Extraer y validar respuestas de texto y JSON estructurado.
    6. Obtener métricas de tokens, tiempo y costo estimado.

Arquitectura:
    El módulo separa la construcción de solicitudes, la comunicación
    HTTP y el procesamiento de respuestas en funciones independientes.

    Esta implementación constituye la base inicial de integración
    con modelos de IA para la futura arquitectura multiempresa de VyOps.

Seguridad:
    La clave GEMINI_API_KEY se obtiene desde variables de entorno.
    Se envía mediante un encabezado HTTP y nunca se incorpora
    directamente al código fuente ni a los parámetros de la URL.
"""
import json
import math
import os
import re
import time

import requests
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env del proyecto.
# Las credenciales reales no deben almacenarse en Git.
load_dotenv()

# Modelo seleccionado para las consultas actuales de VyOps.
# La evaluación comparativa se encuentra en docs/evaluacion_modelos.md.
MODELO = "gemini-3.5-flash-lite"

# Tarifas de referencia en USD por millón de tokens.
# Se utilizan exclusivamente para estimar el costo de las consultas.
# Fuente: https://ai.google.dev/gemini-api/docs/pricing
# Estas tarifas deben revisarse si el proveedor modifica sus precios.
PRECIO_ENTRADA_MILLON = 0.30
PRECIO_SALIDA_MILLON = 2.50

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------
# MODELO = "gemini-3.6-flash"
#
# tarifas para el modelo gemini-3.6-flash segun gemini pricing: https://ai.google.dev/gemini-api/docs/pricing?utm_source=chatgpt.com&hl=es-419#gemini-3.6-flash
# PRECIO_ENTRADA_MILLON = 0.75
# PRECIO_SALIDA_MILLON = 3.75
#
# Tarifas ficticias por millón de tokens para fines académicos.
# PRECIO_ENTRADA_MILLON = 0.50
# PRECIO_SALIDA_MILLON = 2.00
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Endpoint REST de Gemini.
# Se construye dinámicamente para utilizar el modelo configurado.
URL_GEMINI = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODELO}:generateContent"
)
# Número máximo de intentos para errores transitorios.
# Incluye la solicitud inicial y hasta dos reintentos.
MAX_INTENTOS = 3

def armar_peticion(
    pregunta: str,
    system_instruction: str | None = None,
    response_schema: dict | None = None,
) -> tuple[str, dict, dict]:
    """Valida los parámetros y construye una solicitud HTTP para Gemini.

    Comprueba que la pregunta sea válida y que exista una clave API.
    Permite agregar instrucciones de sistema y solicitar respuestas
    JSON estructuradas mediante un esquema opcional.

    Args:
        pregunta: Texto de la consulta que realizará el usuario.
        system_instruction: Instrucciones de comportamiento para
            el modelo. Es opcional.
        response_schema: Diccionario que define la estructura JSON
            esperada. Es opcional.

    Returns:
        Tupla con tres elementos:
            - URL del endpoint REST de Gemini.
            - Encabezados HTTP con autenticación y tipo de contenido.
            - Cuerpo de la solicitud en formato de diccionario.

    Raises:
        ValueError: Si la pregunta, las instrucciones de sistema
            o el esquema son inválidos, o si falta GEMINI_API_KEY.

    Seguridad:
        La clave API se obtiene desde el entorno y se incorpora
        exclusivamente al encabezado x-goog-api-key.
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
    """Envía una solicitud HTTP a Gemini y devuelve su respuesta JSON.

    Realiza una petición POST al endpoint configurado, utilizando
    los encabezados de autenticación y el cuerpo proporcionados.

    Cada intento tiene un tiempo de espera máximo de 30 segundos.
    Ante errores HTTP 429, 500, 502 y 503, o tiempos de espera
    agotados, realiza hasta dos reintentos adicionales.

    Los reintentos utilizan una espera exponencial de 2 y 4 segundos.
    Cuando el proveedor devuelve Retry-After en segundos, se considera
    ese valor para calcular la espera, con un límite de 60 segundos.

    Args:
        url: Dirección del endpoint REST de Gemini.
        encabezados: Diccionario con los encabezados HTTP,
            incluida la clave de autenticación.
        cuerpo: Diccionario con el contenido de la solicitud.

    Returns:
        Diccionario obtenido al interpretar la respuesta JSON
        enviada por Google Gemini.

    Raises:
        RuntimeError: Si ocurre un error de conexión, se agota
            el tiempo de espera, falla la petición HTTP o la
            respuesta del proveedor no contiene JSON válido.

    Seguridad:
        La función no imprime la clave API ni los encabezados
        utilizados para autenticar las solicitudes.
    """

    try:
        # Reintentamos hasta tres veces cuando Gemini responde
        # con HTTP 429, 500, 502 o 503, o supera el tiempo de espera.
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

                # Reintentamos ante límites de solicitudes (429),
                # errores internos o de intermediarios (500, 502)
                # e indisponibilidad temporal del proveedor (503).
                if codigo not in (429, 500, 502, 503):
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
            # Gemini puede devolver HTTP 400 tanto por parámetros
            # incorrectos como por una API key inválida.
            # Evitamos mostrar credenciales o detalles sensibles.
            mensaje = (
                "Gemini rechazó la solicitud (HTTP 400). "
                "Verifica que la API key sea válida y que "
                "los parámetros enviados sean correctos."
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
    """Extrae y valida el texto generado por Google Gemini.

    Accede al primer candidato de la respuesta y obtiene
    el texto contenido en su primera parte.

    La estructura JSON esperada es:
        candidates[0] -> content -> parts[0] -> text

    Args:
        datos: Diccionario con la respuesta JSON de Gemini.

    Returns:
        Cadena de texto generada por el modelo.

    Raises:
        RuntimeError: Si faltan campos en la respuesta, la
            estructura no corresponde al formato esperado
            o el contenido generado está vacío.

    Nota:
        Esta implementación procesa el primer candidato y
        su primera parte. No combina múltiples candidatos
        ni fragmentos de texto.
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

    """Convierte una respuesta textual de Gemini en un objeto JSON validado.

    Comprueba que el texto recibido no esté vacío y elimina los
    delimitadores Markdown opcionales, como ```json y ```.

    Después interpreta el contenido mediante json.loads() y verifica
    que el resultado sea un diccionario de Python.

    Cuando se proporciona una lista de claves esperadas, comprueba
    que todas estén presentes en el objeto JSON.

    Args:
        texto: Cadena de texto devuelta por el modelo.
        claves_esperadas: Lista opcional de claves obligatorias
            que debe contener la respuesta JSON.

    Returns:
        Diccionario con los datos JSON interpretados.

    Raises:
        ValueError: Si el texto está vacío, contiene JSON inválido,
            el resultado no es un objeto JSON, la lista de claves
            esperadas es inválida o falta alguna clave obligatoria.

    Nota:
        Esta función valida el formato JSON y la presencia de claves.
        La comprobación de tipos, valores enumerados y límites
        numéricos se realiza mediante validar_estructura(),
        definida en prompts/test_consistencia.py.
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

    """Extrae las métricas de consumo de tokens de Google Gemini.

    Consulta el objeto usageMetadata de la respuesta del proveedor
    y recupera los contadores de tokens disponibles.

    Args:
        datos: Diccionario con la respuesta JSON de Gemini.

    Returns:
        Diccionario con cuatro métricas:
            - tokens_entrada: Tokens utilizados por la solicitud.
            - tokens_salida: Tokens de la respuesta generada.
            - tokens_razonamiento: Tokens de razonamiento interno.
            - tokens_totales: Total informado por el proveedor.

        Si alguna métrica no está disponible, su valor será None.

    Nota:
        Los valores se obtienen directamente de la respuesta
        del proveedor. Esta función no calcula ni estima tokens.

        La ausencia de una métrica no significa necesariamente
        que su consumo sea cero.
    """

    metadata = datos.get("usageMetadata") or {}

    return {
        "tokens_entrada": metadata.get("promptTokenCount"),
        "tokens_salida": metadata.get("candidatesTokenCount"),
        "tokens_razonamiento": metadata.get("thoughtsTokenCount"),
        "tokens_totales": metadata.get("totalTokenCount"),
    }


def obtener_dato_de_prueba(
        pregunta: str,
        system_instruction: str | None = None) -> dict:

    """Ejecuta una consulta de prueba y reúne sus resultados.

    Coordina las funciones del cliente HTTP para preparar la
    solicitud, consultar a Gemini y procesar la respuesta.

    Utiliza perf_counter() para medir el tiempo transcurrido
    durante la comunicación con el proveedor, incluyendo
    posibles reintentos y sus tiempos de espera.

    Args:
        pregunta: Texto de la consulta que se enviará a Gemini.
        system_instruction: Instrucción de sistema opcional para Gemini.
    Returns:
        Diccionario con los siguientes campos:
            - respuesta: Texto generado por el modelo.
            - uso_tokens: Métricas informadas por Gemini.
            - tiempo_respuesta_segundos: Duración de la consulta.
            - costo_estimado_usd: Costo estimado en dólares.

    Raises:
        ValueError: Si la pregunta o la configuración son inválidas.
        RuntimeError: Si falla la petición, la respuesta no tiene
            el formato esperado o no se puede calcular el costo.

    Diseño:
        Esta función actúa como coordinadora y reutiliza las
        funciones especializadas del módulo, evitando duplicar
        la lógica de comunicación y procesamiento.
    """

    # Paso 1: validar y construir la petición.
    url, encabezados, cuerpo = armar_peticion(pregunta, system_instruction=system_instruction,)
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

    """Calcula el costo estimado de una consulta a Google Gemini.

    Utiliza las métricas de tokens informadas por el proveedor
    y las tarifas configuradas en USD por millón de tokens.

    Valida que las tarifas sean números finitos y no negativos,
    y que los contadores de tokens tengan valores válidos.

    Args:
        datos: Diccionario con la respuesta JSON de Gemini.
        precio_entrada: Tarifa en USD por millón de tokens de entrada.
        precio_salida: Tarifa en USD por millón de tokens de salida.

    Returns:
        Costo estimado de la consulta, expresado en dólares
        estadounidenses (USD).

    Raises:
        ValueError: Si las tarifas o los contadores de tokens
            tienen valores inválidos.
        RuntimeError: Si faltan las métricas necesarias
            para calcular el costo estimado.

    Nota:
        El cálculo utiliza los contadores de tokens disponibles
        y las tarifas de referencia configuradas.

        Es una estimación académica y no sustituye los importes
        de facturación oficiales del proveedor.

        La fórmula de cálculo debe revisarse cuando cambien
        las reglas de contabilización o las tarifas del modelo.
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


# ---------------------------------------------------------------------------
# Punto de entrada: prueba manual de integración con Google Gemini.
#
# Este bloque se ejecuta únicamente cuando el archivo se inicia directamente.
# No se ejecuta cuando sus funciones son importadas desde otros módulos.
#
# Flujo de la prueba:
#   1. Define una pregunta de ejemplo.
#   2. Envía la consulta a Gemini mediante obtener_dato_de_prueba().
#   3. Muestra la respuesta generada y las métricas de consumo.
#   4. Presenta el tiempo de ejecución y el costo estimado.
#   5. Captura errores previsibles para informar el motivo del fallo.
#
# Permite verificar la integración real con la API durante el Gate 1.
# ---------------------------------------------------------------------------

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
