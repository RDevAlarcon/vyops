
"""Define el conjunto de evaluación de recuperación RAG de VyOps.

Este módulo contiene preguntas de referencia y sus
documentos relevantes dentro del corpus municipal ficticio.

Los casos permiten evaluar la capacidad del recuperador
para identificar fuentes documentales relacionadas
con una consulta ciudadana.

Cada caso contiene dos campos:

    pregunta:
        Consulta utilizada para recuperar documentos
        desde el índice vectorial.

    relevantes:
        Conjunto de identificadores de fuentes
        consideradas correctas para la pregunta.

El conjunto contempla cinco áreas de evaluación:

    1. Registro de solicitudes municipales.
    2. Estados y transiciones de solicitudes.
    3. Seguimiento de solicitudes.
    4. Cancelación y autorización humana.
    5. Auditoría y trazabilidad de decisiones.

Las fuentes relevantes utilizan rutas relativas
dentro del corpus documental municipal de VyOps.

Este conjunto puede utilizarse junto con el módulo
evaluar_recuperacion.py para calcular métricas
de recuperación como precisión, recall y F1.

El archivo no ejecuta consultas al modelo Gemini,
no genera embeddings y no modifica el índice vectorial.

Su ejecución directa únicamente muestra
los casos configurados en la terminal.
"""


# ============================================================
# 1. CASOS DE EVALUACIÓN DOCUMENTAL
# ============================================================

# Conjunto de preguntas utilizado para comprobar
# la recuperación de documentos municipales.
#
# Cada elemento contiene:
#
#     pregunta (str):
#         Consulta que debe procesar el recuperador.
#
#     relevantes (set[str]):
#         Conjunto de rutas documentales consideradas
#         relevantes para responder la pregunta.
#
# Se utiliza un conjunto (set) para representar
# los identificadores de fuentes relevantes.
#
# Las rutas deben corresponder con los identificadores
# almacenados en el metadato "fuente" de los documentos
# recuperados para que la comparación sea correcta.

CASOS_EVALUACION = [
    # --------------------------------------------------------
    # CASO 1. INGRESO DE SOLICITUDES
    # --------------------------------------------------------
    #
    # Evalúa si el recuperador identifica el documento
    # que explica el procedimiento de registro
    # de una solicitud municipal.
    {
        "pregunta": "¿Cómo se registra una solicitud municipal?",
        "relevantes": {"atencion_ciudadana/ingreso_solicitudes.md"},
    },

    # --------------------------------------------------------
    # CASO 2. ESTADOS DE UNA SOLICITUD
    # --------------------------------------------------------
    #
    # Comprueba la recuperación del documento que describe
    # los estados y las transiciones de las solicitudes.
    {
        "pregunta": "¿Cuáles son los estados de una solicitud?",
        "relevantes": {"gestion_solicitudes/estados_transiciones.md"},
    },

    # --------------------------------------------------------
    # CASO 3. SEGUIMIENTO DE SOLICITUDES
    # --------------------------------------------------------
    #
    # Evalúa la identificación de la fuente documental
    # relacionada con la consulta y el seguimiento
    # de una solicitud municipal.
    {
        "pregunta": "¿Qué necesito para consultar una solicitud?",
        "relevantes": {"atencion_ciudadana/seguimiento_solicitudes.md"},
    },

    # --------------------------------------------------------
    # CASO 4. CANCELACIÓN Y SUPERVISIÓN HUMANA
    # --------------------------------------------------------
    #
    # Comprueba la recuperación del procedimiento
    # documental relacionado con la cancelación
    # de solicitudes y la autorización humana.
    {
        "pregunta": "¿Puedo cancelar una solicitud sin autorización humana?",
        "relevantes": {"gestion_solicitudes/cancelacion_solicitudes.md"},
    },

    # --------------------------------------------------------
    # CASO 5. AUDITORÍA Y TRAZABILIDAD
    # --------------------------------------------------------
    #
    # Evalúa si el recuperador encuentra la documentación
    # que explica el registro y la trazabilidad
    # de las decisiones del asistente.
    {
        "pregunta": "¿Para qué se registran las decisiones del asistente?",
        "relevantes": {"procedimientos_internos/auditoria_trazabilidad.md"},
    },
]


# ============================================================
# 2. VISUALIZACIÓN DEL CONJUNTO DE EVALUACIÓN
# ============================================================

if __name__ == "__main__":
    # Este bloque se ejecuta únicamente cuando
    # el archivo se inicia directamente.
    #
    # Permite inspeccionar las preguntas y sus
    # fuentes relevantes sin realizar consultas RAG.

    # Muestra la cantidad total de casos configurados.
    print(f"Casos de evaluación: {len(CASOS_EVALUACION)}")

    # Recorre los casos utilizando una numeración
    # que comienza en uno para facilitar su lectura.
    for numero, caso in enumerate(CASOS_EVALUACION, start=1):

        # Presenta la pregunta asociada al caso.
        print(f"\nCaso {numero}: {caso['pregunta']}")

        # Presenta el conjunto de documentos
        # considerados relevantes para esa pregunta.
        print(f"Documentos relevantes: {caso['relevantes']}")
