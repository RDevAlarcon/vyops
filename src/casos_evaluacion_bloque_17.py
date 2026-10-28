"""Banco de casos para la evaluación cualitativa del Bloque 17.

Este módulo define las consultas y referencias utilizadas
para evaluar respuestas de Gemini.

Los casos incluyen preguntas factuales, matemáticas,
conceptuales y relacionadas con programación.

El banco es independiente del Bloque 16 para conservar
la evidencia y los resultados de las evaluaciones anteriores.
"""

# Importamos los tres casos originales del Bloque 16.
# No modificamos su contenido ni sus referencias.
from evaluar_respuestas import CASOS_EVALUACION_BLOQUE_16


# Creamos una copia de los casos existentes.
# Cada diccionario se copia para evitar que modificaciones
# posteriores afecten a los casos originales.
CASOS_EVALUACION_BLOQUE_17: list[dict[str, str]] = [
    caso.copy()
    for caso in CASOS_EVALUACION_BLOQUE_16
]

# Incorporamos 20 casos adicionales para el Bloque 17.
#
# Las referencias son respuestas breves con información
# verificable. No representan todas las respuestas válidas.
#
# Las preguntas se distribuyen entre programación,
# matemáticas, ciencias y conocimientos generales.
#
# Esta lista no realiza consultas a Gemini.
CASOS_EVALUACION_BLOQUE_17.extend(
    [
        # Caso 4: fecha histórica.
        {
            "consulta": "¿En qué año llegó el ser humano a la Luna?",
            "referencia": (
                "El ser humano llegó a la Luna en 1969."
            ),
        },

        # Caso 5: capital de un país.
        {
            "consulta": "¿Cuál es la capital de Chile?",
            "referencia": (
                "La capital de Chile es Santiago."
            ),
        },

        # Caso 6: cálculo matemático.
        {
            "consulta": "¿Cuánto es 15 multiplicado por 8?",
            "referencia": (
                "15 multiplicado por 8 es 120."
            ),
        },

        # Caso 7: concepto de programación.
        {
            "consulta": "¿Qué es una variable en programación?",
            "referencia": (
                "Una variable es un nombre asociado a un valor."
            ),
        },

        # Caso 8: negación.
        {
            "consulta": "¿Python exige declarar el tipo de cada variable?",
            "referencia": (
                "No, Python no exige declarar el tipo de cada variable."
            ),
        },

        # Caso 9: dato numérico.
        {
            "consulta": "¿Cuántos días tiene una semana?",
            "referencia": (
                "Una semana tiene siete días."
            ),
        },

        # Caso 10: concepto científico.
        {
            "consulta": "¿Qué es la fotosíntesis?",
            "referencia": (
                "La fotosíntesis permite convertir energía luminosa "
                "en energía química."
            ),
        },

        # Caso 11: fecha de un acontecimiento.
        {
            "consulta": "¿En qué año comenzó la Segunda Guerra Mundial?",
            "referencia": (
                "La Segunda Guerra Mundial comenzó en 1939."
            ),
        },

        # Caso 12: tipo de dato.
        {
            "consulta": "¿Qué representa un booleano en Python?",
            "referencia": (
                "Un booleano representa verdadero o falso."
            ),
        },

        # Caso 13: operación matemática.
        {
            "consulta": "¿Cuál es la raíz cuadrada de 144?",
            "referencia": (
                "La raíz cuadrada principal de 144 es 12."
            ),
        },

        # Caso 14: concepto de bases de datos.
        {
            "consulta": "¿Qué es una clave primaria en una base de datos?",
            "referencia": (
                "Una clave primaria identifica de forma única "
                "cada registro de una tabla."
            ),
        },

        # Caso 15: negación factual.
        {
            "consulta": "¿El Sol es un planeta?",
            "referencia": (
                "No, el Sol es una estrella."
            ),
        },

        # Caso 16: dato geográfico.
        {
            "consulta": "¿Cuál es el océano más grande de la Tierra?",
            "referencia": (
                "El océano Pacífico es el más grande de la Tierra."
            ),
        },

        # Caso 17: estructura de datos.
        {
            "consulta": "¿Qué es un diccionario en Python?",
            "referencia": (
                "Un diccionario almacena asociaciones entre claves y valores."
            ),
        },

        # Caso 18: operación matemática.
        {
            "consulta": "¿Cuánto es 100 dividido por 4?",
            "referencia": (
                "100 dividido por 4 es 25."
            ),
        },

        # Caso 19: concepto de redes.
        {
            "consulta": "¿Qué significa HTTP?",
            "referencia": (
                "HTTP significa Protocolo de Transferencia "
                "de Hipertexto."
            ),
        },

        # Caso 20: conocimiento científico.
        {
            "consulta": "¿Cuál es la fórmula química del agua?",
            "referencia": (
                "La fórmula química del agua es H2O."
            ),
        },

        # Caso 21: concepto de programación.
        {
            "consulta": "¿Qué hace la función len() en Python?",
            "referencia": (
                "La función len devuelve la cantidad "
                "de elementos de un objeto."
            ),
        },

        # Caso 22: dato histórico.
        {
            "consulta": "¿En qué año se declaró la independencia de Chile?",
            "referencia": (
                "La independencia de Chile se declaró en 1818."
            ),
        },

        # Caso 23: concepto de inteligencia artificial.
        {
            "consulta": "¿Qué es el aprendizaje supervisado?",
            "referencia": (
                "El aprendizaje supervisado entrena modelos "
                "utilizando ejemplos etiquetados."
            ),
        },
    ]
)