
"""Consulta el conteo de tokens para el modelo de embeddings de VyOps.

Este módulo permite conocer cuántos tokens contiene un texto
según el modelo de embeddings utilizado por el proyecto.

El conteo se realiza mediante la API de Gemini y se utiliza
para estimar el costo de procesamiento de las consultas RAG.

Responsabilidades:
    - Cargar las variables de entorno del proyecto.
    - Inicializar el cliente oficial de Google Gen AI.
    - Solicitar el conteo de tokens de un texto.
    - Devolver la cantidad reportada por el proveedor.

El módulo no genera vectores, no modifica ChromaDB
y no persiste información en el índice documental.

La consulta de tokens requiere acceso al servicio de Gemini
y una configuración de autenticación válida.
"""

from dotenv import load_dotenv
from google import genai

from recuperacion import BASE_DIR


def contar_tokens_embedding(texto):
    """Obtiene el conteo de tokens de un texto mediante Gemini.

    Carga la configuración de entorno de VyOps, inicializa
    un cliente de Google Gen AI y consulta el número de tokens
    correspondiente al modelo gemini-embedding-001.

    Args:
        texto (str): Texto cuyo consumo de tokens se
            desea consultar.

    Returns:
        int: Cantidad total de tokens reportada por
            la API para el texto proporcionado.

    Raises:
        Exception: Propaga los errores producidos al
            inicializar el cliente o consultar el servicio,
            incluidos posibles problemas de autenticación,
            conectividad o disponibilidad.

    Notes:
        La función realiza una solicitud real a la API
        de Gemini mediante models.count_tokens().

        El conteo no genera embeddings ni modifica
        el almacenamiento vectorial.

        El identificador del modelo está definido
        directamente en esta función.

        La función devuelve únicamente el total de tokens;
        el cálculo económico se realiza en costos_rag.py.
    """

    # Carga la configuración del proyecto desde su archivo
    # .env antes de inicializar el cliente de Google Gen AI.
    load_dotenv(dotenv_path=BASE_DIR / ".env")

    cliente = genai.Client()

    # Solicita el conteo al mismo modelo de embeddings
    # utilizado por el pipeline RAG municipal.
    respuesta = cliente.models.count_tokens(
        model="gemini-embedding-001",
        contents=texto,
    )

    # Devuelve el total informado por el proveedor,
    # sin realizar estimaciones locales adicionales.
    return respuesta.total_tokens


if __name__ == "__main__":
    # Ejecución manual para consultar el conteo de tokens.
    #
    # Este bloque no se ejecuta cuando el módulo se importa.
    # Requiere credenciales válidas y acceso a la API de Gemini.
    #
    # Los errores se muestran en consola para facilitar
    # el diagnóstico de esta ejecución independiente.

    pregunta = (
        "¿Se puede cancelar una solicitud municipal "
        "sin autorización humana?"
    )

    try:
        tokens = contar_tokens_embedding(pregunta)

        print("Modelo: gemini-embedding-001")
        print(f"Tokens de la pregunta: {tokens}")

    except Exception as error:
        print("El conteo de tokens no pudo completarse.")
        print(f"Tipo de error: {type(error).__name__}")
        print(f"Detalle: {error}")
