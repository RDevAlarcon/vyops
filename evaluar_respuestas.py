"""Evaluación de respuestas generadas por Gemini.

Bloque 15 — SkillNest.

Este módulo permitirá comparar respuestas generadas por
un modelo de inteligencia artificial con textos de referencia.

Se evaluará la coincidencia de vocabulario antes y después
de aplicar el pipeline de limpieza y tokenización de VyOps.
"""
from src.cliente_api import consultar_modelo
from src.pipeline_texto import calcular_coincidencia

# Definimos tres casos de evaluación.
# Cada caso contiene una pregunta para Gemini y una respuesta
# de referencia que utilizaremos para calcular coincidencias.
# Las referencias son breves y contienen información verificable.
# No representan todas las respuestas válidas posibles.

CASOS_EVALUACION = [
    {
        "pregunta": "¿Cuál es la capital de Chile? Responde brevemente.",
        "referencia": "La capital de Chile es Santiago.",
    },
    {
        "pregunta": "¿Cuánto es 5 multiplicado por 4? Responde brevemente.",
        "referencia": "Cinco multiplicado por cuatro es veinte.",
    },
    {
        "pregunta": "¿Qué lenguaje de programación utiliza la función print()? Responde brevemente.",
        "referencia": "La función print se utiliza en Python.",
    },
]

def evaluar_respuestas() -> None:
    """Evalúa tres respuestas reales generadas por Gemini.

    Recorre los casos de evaluación definidos previamente,
    consulta el modelo y compara cada respuesta con su
    correspondiente texto de referencia.

    Para cada caso calcula dos métricas:
        - Coincidencia sin normalización.
        - Coincidencia después de aplicar el pipeline.

    Los resultados se presentan en la terminal como
    porcentajes para facilitar su comparación.

    Raises:
        ValueError: Si existe un problema con los parámetros.
        RuntimeError: Si falla la comunicación con Gemini.

    Nota:
        Esta función realiza consultas reales a la API.
        No debe ejecutarse durante las pruebas unitarias.
    """

    # Recorremos los tres casos de evaluación.
    for numero, caso in enumerate(CASOS_EVALUACION, start=1):

        # Obtenemos la pregunta y su respuesta de referencia.
        pregunta = caso["pregunta"]
        referencia = caso["referencia"]

        # Consultamos Gemini utilizando el cliente modular
        # que desarrollamos en los bloques anteriores.
        respuesta = consultar_modelo(pregunta)

        # Calculamos la coincidencia conservando las
        # diferencias originales de formato.
        coincidencia_original = calcular_coincidencia(
            referencia,
            respuesta,
            normalizar=False,
        )

        # Calculamos la coincidencia después de aplicar
        # la limpieza y tokenización de nuestro pipeline.
        coincidencia_normalizada = calcular_coincidencia(
            referencia,
            respuesta,
            normalizar=True,
        )

        # Presentamos los textos utilizados en la evaluación.
        print(f"\n{'=' * 60}")
        print(f"CASO DE EVALUACIÓN {numero}")
        print(f"{'=' * 60}")
        print(f"Pregunta: {pregunta}")
        print(f"Referencia: {referencia}")
        print(f"Respuesta Gemini: {respuesta}")

        # Mostramos las métricas expresadas en porcentajes.
        print(
            f"Coincidencia original: "
            f"{coincidencia_original:.2%}"
        )
        print(
            f"Coincidencia normalizada: "
            f"{coincidencia_normalizada:.2%}"
        )

if __name__ == "__main__":
    # Este bloque se ejecuta únicamente cuando iniciamos
    # evaluar_respuestas.py directamente desde la terminal.
    # No se ejecuta al importar el módulo desde otro archivo.

    try:
        # Iniciamos la evaluación de los tres casos.
        # Cada caso realizará una consulta real a Gemini.
        evaluar_respuestas()

    except ValueError as error:
        # Informamos los errores relacionados con parámetros
        # o configuración sin mostrar información sensible.
        print(f"Error de configuración: {error}")

    except RuntimeError as error:
        # Informamos los problemas de comunicación con Gemini,
        # incluyendo fallos que persistan después de los reintentos.
        print(f"Error al consultar Gemini: {error}")