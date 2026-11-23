
"""Banco de casos para la evaluación cualitativa del Bloque 17.

Este módulo define las consultas y referencias utilizadas
para evaluar respuestas de Gemini en el proyecto VyOps.

El banco de evaluación reúne preguntas de distintas áreas:

    - Historia y geografía.
    - Matemáticas y operaciones numéricas.
    - Ciencias naturales.
    - Conceptos de programación.
    - Bases de datos y redes.
    - Inteligencia artificial.
    - Preguntas que requieren reconocer una negación.

La construcción del conjunto se realiza en dos etapas:

    1. Reutilizar los tres casos originales del Bloque 16.
    2. Incorporar veinte casos adicionales del Bloque 17.

Cada caso se representa mediante un diccionario
con dos campos:

    consulta:
        Pregunta que se utilizará para evaluar el modelo.

    referencia:
        Respuesta esperada que sirve como criterio
        de comparación durante la evaluación.

Las referencias contienen respuestas breves
con información verificable.

No representan necesariamente todas las formulaciones
correctas que podría generar un modelo de lenguaje.

INDEPENDENCIA ENTRE BLOQUES:

    Los casos del Bloque 16 se copian individualmente
    mediante dict.copy().

    Esto permite modificar los diccionarios del nuevo
    conjunto sin alterar los originales.

    La copia es superficial, suficiente para los campos
    de texto utilizados en los casos actuales.

    El banco del Bloque 17 conserva así una estructura
    independiente para sus evaluaciones.

Este módulo únicamente define datos de evaluación.

No realiza consultas a Gemini, no calcula métricas
y no modifica resultados de evaluaciones anteriores.
"""

# ============================================================
# 1. IMPORTACIÓN DE CASOS DEL BLOQUE 16
# ============================================================

# Importamos los tres casos originales del Bloque 16.
# No modificamos su contenido ni sus referencias.
#
# Estos casos constituyen la base del conjunto ampliado
# utilizado para las evaluaciones del Bloque 17.
from evaluar_respuestas import CASOS_EVALUACION_BLOQUE_16


# ============================================================
# 2. CREACIÓN DEL BANCO DE EVALUACIÓN DEL BLOQUE 17
# ============================================================

# Creamos una copia de los casos existentes.
# Cada diccionario se copia para evitar que modificaciones
# posteriores afecten a los casos originales.
#
# Se utiliza una comprensión de lista para generar
# nuevos diccionarios a partir de los casos anteriores.
#
# La anotación indica que cada caso contiene
# claves y valores de tipo str.
CASOS_EVALUACION_BLOQUE_17: list[dict[str, str]] = [
    caso.copy()
    for caso in CASOS_EVALUACION_BLOQUE_16
]


# ============================================================
# 3. INCORPORACIÓN DE CASOS ADICIONALES
# ============================================================

# Incorporamos 20 casos adicionales para el Bloque 17.
#
# Las referencias son respuestas breves con información
# verificable. No representan todas las respuestas válidas.
#
# Las preguntas se distribuyen entre programación,
# matemáticas, ciencias y conocimientos generales.
#
# Esta lista no realiza consultas a Gemini.
#
# extend() incorpora los nuevos diccionarios al conjunto
# creado anteriormente, conservando los casos heredados
# del Bloque 16.
CASOS_EVALUACION_BLOQUE_17.extend(
    [
        # ----------------------------------------------------
        # CASO 4: HISTORIA — LLEGADA A LA LUNA
        # ----------------------------------------------------

        # Caso 4: fecha histórica.
        #
        # Evalúa la identificación de un año asociado
        # a un acontecimiento histórico.
        {
            "consulta": "¿En qué año llegó el ser humano a la Luna?",
            "referencia": (
                "El ser humano llegó a la Luna en 1969."
            ),
        },

        # ----------------------------------------------------
        # CASO 5: GEOGRAFÍA — CAPITAL DE CHILE
        # ----------------------------------------------------

        # Caso 5: capital de un país.
        #
        # Evalúa la recuperación de un dato geográfico.
        {
            "consulta": "¿Cuál es la capital de Chile?",
            "referencia": (
                "La capital de Chile es Santiago."
            ),
        },

        # ----------------------------------------------------
        # CASO 6: MATEMÁTICAS — MULTIPLICACIÓN
        # ----------------------------------------------------

        # Caso 6: cálculo matemático.
        #
        # Evalúa una multiplicación de números enteros.
        {
            "consulta": "¿Cuánto es 15 multiplicado por 8?",
            "referencia": (
                "15 multiplicado por 8 es 120."
            ),
        },

        # ----------------------------------------------------
        # CASO 7: PROGRAMACIÓN — VARIABLES
        # ----------------------------------------------------

        # Caso 7: concepto de programación.
        #
        # Evalúa la comprensión básica del concepto
        # de variable en programación.
        {
            "consulta": "¿Qué es una variable en programación?",
            "referencia": (
                "Una variable es un nombre asociado a un valor."
            ),
        },

        # ----------------------------------------------------
        # CASO 8: PYTHON — DECLARACIÓN DE TIPOS
        # ----------------------------------------------------

        # Caso 8: negación.
        #
        # Evalúa la capacidad de responder correctamente
        # una pregunta cuya respuesta requiere negar
        # una afirmación sobre Python.
        {
            "consulta": "¿Python exige declarar el tipo de cada variable?",
            "referencia": (
                "No, Python no exige declarar el tipo de cada variable."
            ),
        },

        # ----------------------------------------------------
        # CASO 9: CONOCIMIENTO GENERAL — DÍAS DE LA SEMANA
        # ----------------------------------------------------

        # Caso 9: dato numérico.
        #
        # Evalúa la recuperación de una cantidad conocida.
        {
            "consulta": "¿Cuántos días tiene una semana?",
            "referencia": (
                "Una semana tiene siete días."
            ),
        },

        # ----------------------------------------------------
        # CASO 10: CIENCIAS — FOTOSÍNTESIS
        # ----------------------------------------------------

        # Caso 10: concepto científico.
        #
        # Evalúa la comprensión de un proceso biológico
        # relacionado con la transformación de energía.
        {
            "consulta": "¿Qué es la fotosíntesis?",
            "referencia": (
                "La fotosíntesis permite convertir energía luminosa "
                "en energía química."
            ),
        },

        # ----------------------------------------------------
        # CASO 11: HISTORIA — SEGUNDA GUERRA MUNDIAL
        # ----------------------------------------------------

        # Caso 11: fecha de un acontecimiento.
        #
        # Evalúa la identificación del año de inicio
        # de un acontecimiento histórico.
        {
            "consulta": "¿En qué año comenzó la Segunda Guerra Mundial?",
            "referencia": (
                "La Segunda Guerra Mundial comenzó en 1939."
            ),
        },

        # ----------------------------------------------------
        # CASO 12: PYTHON — VALORES BOOLEANOS
        # ----------------------------------------------------

        # Caso 12: tipo de dato.
        #
        # Evalúa la comprensión del tipo booleano
        # utilizado para representar valores lógicos.
        {
            "consulta": "¿Qué representa un booleano en Python?",
            "referencia": (
                "Un booleano representa verdadero o falso."
            ),
        },

        # ----------------------------------------------------
        # CASO 13: MATEMÁTICAS — RAÍZ CUADRADA
        # ----------------------------------------------------

        # Caso 13: operación matemática.
        #
        # Evalúa el cálculo de una raíz cuadrada principal.
        {
            "consulta": "¿Cuál es la raíz cuadrada de 144?",
            "referencia": (
                "La raíz cuadrada principal de 144 es 12."
            ),
        },

        # ----------------------------------------------------
        # CASO 14: BASES DE DATOS — CLAVE PRIMARIA
        # ----------------------------------------------------

        # Caso 14: concepto de bases de datos.
        #
        # Evalúa la comprensión de la identificación
        # única de registros dentro de una tabla.
        {
            "consulta": "¿Qué es una clave primaria en una base de datos?",
            "referencia": (
                "Una clave primaria identifica de forma única "
                "cada registro de una tabla."
            ),
        },

        # ----------------------------------------------------
        # CASO 15: CIENCIAS — CLASIFICACIÓN DEL SOL
        # ----------------------------------------------------

        # Caso 15: negación factual.
        #
        # Evalúa la capacidad de corregir una premisa
        # incorrecta mediante una respuesta negativa.
        {
            "consulta": "¿El Sol es un planeta?",
            "referencia": (
                "No, el Sol es una estrella."
            ),
        },

        # ----------------------------------------------------
        # CASO 16: GEOGRAFÍA — OCÉANOS
        # ----------------------------------------------------

        # Caso 16: dato geográfico.
        #
        # Evalúa la identificación del océano
        # de mayor extensión.
        {
            "consulta": "¿Cuál es el océano más grande de la Tierra?",
            "referencia": (
                "El océano Pacífico es el más grande de la Tierra."
            ),
        },

        # ----------------------------------------------------
        # CASO 17: PYTHON — DICCIONARIOS
        # ----------------------------------------------------

        # Caso 17: estructura de datos.
        #
        # Evalúa la comprensión de las asociaciones
        # entre claves y valores.
        {
            "consulta": "¿Qué es un diccionario en Python?",
            "referencia": (
                "Un diccionario almacena asociaciones entre claves y valores."
            ),
        },

        # ----------------------------------------------------
        # CASO 18: MATEMÁTICAS — DIVISIÓN
        # ----------------------------------------------------

        # Caso 18: operación matemática.
        #
        # Evalúa una división entre números enteros.
        {
            "consulta": "¿Cuánto es 100 dividido por 4?",
            "referencia": (
                "100 dividido por 4 es 25."
            ),
        },

        # ----------------------------------------------------
        # CASO 19: REDES — PROTOCOLO HTTP
        # ----------------------------------------------------

        # Caso 19: concepto de redes.
        #
        # Evalúa el reconocimiento del significado
        # de una sigla utilizada en comunicaciones web.
        {
            "consulta": "¿Qué significa HTTP?",
            "referencia": (
                "HTTP significa Protocolo de Transferencia "
                "de Hipertexto."
            ),
        },

        # ----------------------------------------------------
        # CASO 20: QUÍMICA — FÓRMULA DEL AGUA
        # ----------------------------------------------------

        # Caso 20: conocimiento científico.
        #
        # Evalúa la identificación de una fórmula química.
        {
            "consulta": "¿Cuál es la fórmula química del agua?",
            "referencia": (
                "La fórmula química del agua es H2O."
            ),
        },

        # ----------------------------------------------------
        # CASO 21: PYTHON — FUNCIÓN LEN
        # ----------------------------------------------------

        # Caso 21: concepto de programación.
        #
        # Evalúa la comprensión de la función integrada
        # utilizada para obtener la longitud de un objeto.
        {
            "consulta": "¿Qué hace la función len() en Python?",
            "referencia": (
                "La función len devuelve la cantidad "
                "de elementos de un objeto."
            ),
        },

        # ----------------------------------------------------
        # CASO 22: HISTORIA DE CHILE — INDEPENDENCIA
        # ----------------------------------------------------

        # Caso 22: dato histórico.
        #
        # Evalúa la identificación del año indicado
        # en la referencia histórica del conjunto.
        {
            "consulta": "¿En qué año se declaró la independencia de Chile?",
            "referencia": (
                "La independencia de Chile se declaró en 1818."
            ),
        },

        # ----------------------------------------------------
        # CASO 23: IA — APRENDIZAJE SUPERVISADO
        # ----------------------------------------------------

        # Caso 23: concepto de inteligencia artificial.
        #
        # Evalúa la comprensión del aprendizaje supervisado
        # mediante ejemplos etiquetados.
        {
            "consulta": "¿Qué es el aprendizaje supervisado?",
            "referencia": (
                "El aprendizaje supervisado entrena modelos "
                "utilizando ejemplos etiquetados."
            ),
        },
    ]
)
