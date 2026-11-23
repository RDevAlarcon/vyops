
"""Herramienta de consulta de solicitudes municipales simuladas.

Este módulo implementa una herramienta compatible con LangChain
para consultar información ficticia sobre solicitudes municipales.

La herramienta permite recuperar:

    1. El estado actual de una solicitud.
    2. El estado actual junto con su historial.
    3. Un mensaje informativo cuando la solicitud no existe.

Componentes principales:

    ArgumentosConsultaSolicitud:
        Modelo Pydantic que define y valida
        los argumentos recibidos por la herramienta.

    SOLICITUDES:
        Diccionario en memoria que contiene
        los datos municipales simulados.

    consultar_estado_solicitud:
        Herramienta registrada mediante el decorador
        @tool de LangChain.

Flujo general:

    Agente LangChain
        |
        v
    Validación de argumentos con Pydantic
        |
        v
    Búsqueda en SOLICITUDES
        |
        v
    Verificación de existencia
        |
        v
    Consulta del estado o historial
        |
        v
    Respuesta de texto

IMPORTANTE:
    Los datos utilizados son ficticios.

    Este módulo no consulta sistemas municipales reales,
    bases de datos externas ni servicios administrativos.

    La herramienta es de solo lectura y no modifica
    los estados de las solicitudes almacenadas.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# BaseModel permite definir un esquema de argumentos.
# Field establece restricciones, valores predeterminados
# y descripciones de los campos.
from pydantic import BaseModel, Field

# El decorador tool permite registrar una función
# como herramienta ejecutable por LangChain.
from langchain_core.tools import tool


# ============================================================
# 2. ESQUEMA DE ARGUMENTOS DE CONSULTA
# ============================================================

class ArgumentosConsultaSolicitud(BaseModel):
    """Define los argumentos para consultar una solicitud municipal.

    Este modelo Pydantic establece los parámetros
    que puede proporcionar un agente al utilizar
    la herramienta de consulta.

    Attributes:
        numero_solicitud:
            Identificador de la solicitud municipal
            que se desea consultar.

            Debe contener al menos un carácter.

        incluir_historial:
            Indicador que determina el nivel
            de detalle de la respuesta.

            False:
                Devuelve únicamente el estado actual.

            True:
                Devuelve el estado actual
                acompañado del historial registrado.

    El esquema permite validar la estructura
    de entrada antes de ejecutar la herramienta.

    No realiza consultas ni modifica datos.
    """

    # --------------------------------------------------------
    # 2.1. IDENTIFICADOR DE LA SOLICITUD
    # --------------------------------------------------------

    # Define el número de solicitud que debe recibir
    # la herramienta.
    #
    # min_length=1 impide proporcionar una cadena vacía.
    #
    # La descripción ofrece al agente un ejemplo
    # del formato utilizado en los datos de prueba.
    numero_solicitud: str = Field(
        description=(
            "Identificador de la solicitud municipal, "
            "por ejemplo: SOL-12345."
        ),
        min_length=1,
    )

    # --------------------------------------------------------
    # 2.2. OPCIÓN DE CONSULTA DEL HISTORIAL
    # --------------------------------------------------------

    # Permite solicitar el historial de estados.
    #
    # El valor predeterminado False mantiene
    # la respuesta limitada al estado actual.
    #
    # Cuando se proporciona True, la herramienta
    # incorpora también los estados anteriores
    # registrados en los datos simulados.
    incluir_historial: bool = Field(
        default=False,
        description=(
            "Si es True, incluye el historial completo "
            "de estados de la solicitud. "
            "Si es False, muestra solamente el estado actual."
        ),
    )


# ============================================================
# 3. DATOS MUNICIPALES SIMULADOS
# ============================================================

# Diccionario utilizado como fuente local de información.
#
# Cada clave representa un número de solicitud.
#
# Cada solicitud contiene:
#
#     actual:
#         Descripción del estado vigente.
#
#     historial:
#         Lista de estados registrados
#         durante el proceso ficticio.
#
# Estos datos permiten demostrar la consulta
# sin depender de servicios municipales externos.
SOLICITUDES = {
    "SOL-12345": {
        "actual": "En revisión por la unidad municipal.",
        "historial": [
            "Solicitud recibida.",
            "Documentación validada.",
            "En revisión por la unidad municipal.",
        ],
    },
}


# ============================================================
# 4. HERRAMIENTA DE CONSULTA DE SOLICITUDES
# ============================================================

# Registra la función como herramienta LangChain.
#
# El nombre consultar_estado_solicitud identifica
# la operación disponible para el agente.
#
# args_schema vincula la herramienta con el modelo
# Pydantic definido anteriormente.
@tool(
    "consultar_estado_solicitud",
    args_schema=ArgumentosConsultaSolicitud,
)
def consultar_estado_solicitud(
    numero_solicitud: str,
    incluir_historial: bool = False,
) -> str:
    """Consulta el estado de una solicitud municipal simulada.

    Busca una solicitud dentro del diccionario SOLICITUDES
    y devuelve información según los argumentos recibidos.

    Args:
        numero_solicitud:
            Identificador de la solicitud que se desea
            consultar en los datos ficticios.

        incluir_historial:
            Determina si la respuesta debe incluir
            el historial completo de estados.

            Su valor predeterminado es False.

    Returns:
        str:
            Respuesta textual con uno de estos resultados:

            - Solicitud inexistente:
              Mensaje indicando que no se encontró
              el identificador en los datos de prueba.

            - Solicitud existente sin historial:
              Descripción del estado actual.

            - Solicitud existente con historial:
              Estado actual seguido de los estados
              registrados en el historial.

    La búsqueda utiliza coincidencia exacta
    con las claves del diccionario SOLICITUDES.

    La función no modifica los datos almacenados
    ni realiza llamadas a servicios externos.
    """

    # --------------------------------------------------------
    # 4.1. BÚSQUEDA DE LA SOLICITUD
    # --------------------------------------------------------

    # Recupera los datos asociados al identificador.
    #
    # get() devuelve None cuando la clave
    # no existe en el diccionario.
    solicitud = SOLICITUDES.get(numero_solicitud)

    # --------------------------------------------------------
    # 4.2. SOLICITUD NO ENCONTRADA
    # --------------------------------------------------------

    # Si no existen datos para el identificador,
    # devuelve un mensaje informativo.
    #
    # No intenta consultar fuentes adicionales
    # ni genera información ficticia nueva.
    if solicitud is None:
        return (
            f"No se encontró la solicitud {numero_solicitud} "
            "en los datos de prueba."
        )

    # --------------------------------------------------------
    # 4.3. CONSULTA DEL ESTADO ACTUAL
    # --------------------------------------------------------

    # Cuando no se solicita el historial,
    # devuelve exclusivamente el estado vigente.
    #
    # Esta es la modalidad predeterminada.
    if not incluir_historial:
        return solicitud["actual"]

    # --------------------------------------------------------
    # 4.4. PREPARACIÓN DEL HISTORIAL
    # --------------------------------------------------------

    # Une los estados registrados en una cadena.
    #
    # Cada elemento queda separado por una coma
    # y un espacio para facilitar su lectura.
    #
    # El orden de los estados se conserva
    # tal como aparece en la lista original.
    historial = ", ".join(solicitud["historial"])

    # --------------------------------------------------------
    # 4.5. RESPUESTA CON ESTADO E HISTORIAL
    # --------------------------------------------------------

    # Devuelve el estado actual y el historial
    # dentro de una única respuesta textual.
    #
    # No modifica el registro consultado.
    return f"{solicitud['actual']} (historial: {historial})"
