
"""Manejo de errores en cadenas LangChain.

Bloque 20 de SkillNest.

Este módulo implementa mecanismos de recuperación
ante errores durante la ejecución de cadenas LangChain
dentro del proyecto VyOps.

Su propósito es proporcionar respuestas controladas
cuando una cadena falla, evitando exponer directamente
al usuario las excepciones internas del procesamiento.

Responsabilidades principales:

    1. Incorporar respuestas alternativas a cadenas.
    2. Ejecutar cadenas con captura de excepciones.
    3. Registrar errores mediante el módulo logging.
    4. Construir respuestas seguras para el enrutamiento.
    5. Integrar mecanismos de fallback con LangChain.

Componentes utilizados:

    Runnable:
        Interfaz de componentes ejecutables de LangChain.

    RunnableLambda:
        Adaptador que permite utilizar funciones Python
        como componentes ejecutables.

    with_fallbacks():
        Mecanismo de LangChain que permite ejecutar
        una cadena alternativa cuando falla la principal.

    logging:
        Sistema de registro de errores y diagnósticos.

El módulo contempla dos estrategias de recuperación:

    Recuperación general:
        Devuelve un mensaje de texto cuando
        una cadena no puede completar su ejecución.

    Recuperación de enrutamiento:
        Conserva el mensaje original y devuelve
        un diccionario con categoría de error
        y una respuesta controlada.

IMPORTANTE:
    Los fallbacks no solucionan necesariamente
    la causa que produjo el error.

    Su responsabilidad es proporcionar una salida
    alternativa cuando ocurre una excepción.

    El registro de errores permite conservar
    información útil para el diagnóstico posterior.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Módulo estándar utilizado para registrar
# errores y excepciones durante la ejecución.
import logging

# Runnable representa una cadena o componente ejecutable.
#
# RunnableLambda permite convertir funciones Python
# en componentes compatibles con LangChain.
from langchain_core.runnables import Runnable, RunnableLambda

# Constructor de la cadena de clasificación
# y enrutamiento condicional del Bloque 19.
from src.enrutamiento_langchain import construir_cadena_enrutamiento


# ============================================================
# 2. FALLBACK GENERAL PARA CADENAS LANGCHAIN
# ============================================================

def construir_cadena_con_fallback(cadena_principal: Runnable) -> Runnable:
    """Construye una cadena con respuesta alternativa ante errores.

    Args:
        cadena_principal:
            Cadena LangChain que se ejecutará inicialmente.

    Returns:
        Runnable:
            Cadena que incorpora un mecanismo de fallback.

            Si la cadena principal se ejecuta correctamente,
            devuelve su resultado original.

            Si ocurre una excepción gestionada
            por el mecanismo de fallback, ejecuta
            la respuesta alternativa.

    El fallback utiliza RunnableLambda para transformar
    una función Python en un componente de LangChain.

    La respuesta alternativa es un mensaje genérico
    que no expone detalles internos del error.

    Esta función construye la cadena, pero no la ejecuta.
    """

    # --------------------------------------------------------
    # 2.1. DEFINICIÓN DE LA RESPUESTA ALTERNATIVA
    # --------------------------------------------------------

    def respuesta_alternativa(datos: dict) -> str:
        """Devuelve un mensaje seguro cuando falla la cadena principal.

        Args:
            datos:
                Datos recibidos por el componente
                de recuperación.

        Returns:
            str:
                Mensaje genérico que informa
                que la solicitud no pudo procesarse.

        El mensaje evita incluir detalles técnicos
        sobre la excepción que originó el fallo.
        """

        # Devuelve una respuesta controlada
        # sin revelar información interna.
        return (
            "No fue posible procesar tu solicitud en este momento. "
            "Por favor, intenta nuevamente más tarde."
        )

    # --------------------------------------------------------
    # 2.2. CONSTRUCCIÓN DEL FALLBACK
    # --------------------------------------------------------

    # Convierte la función de recuperación
    # en un Runnable compatible con LangChain.
    fallback = RunnableLambda(respuesta_alternativa)

    # --------------------------------------------------------
    # 2.3. ASOCIACIÓN CON LA CADENA PRINCIPAL
    # --------------------------------------------------------

    # Registra el fallback como alternativa
    # cuando la cadena principal genera una excepción.
    return cadena_principal.with_fallbacks([fallback])


# ============================================================
# 3. EJECUCIÓN CONTROLADA DE CADENAS
# ============================================================

def ejecutar_cadena_segura(
    cadena: Runnable,
    datos: dict,
) -> str | dict:
    """Ejecuta una cadena y controla los errores inesperados.

    Args:
        cadena:
            Componente Runnable que debe ejecutarse.

        datos:
            Diccionario de entrada entregado a la cadena.

    Returns:
        str | dict:
            Resultado original de la cadena
            cuando la ejecución finaliza correctamente.

            Si ocurre una excepción, devuelve
            un mensaje genérico de error.

    Manejo de errores:
        Captura las excepciones que se produzcan
        durante la ejecución de cadena.invoke().

        Utiliza logging.exception() para registrar
        el error junto con su información de traceback.

        Posteriormente devuelve una respuesta controlada.

    La función no vuelve a intentar la operación
    ni modifica la cadena recibida.
    """

    # --------------------------------------------------------
    # 3.1. EJECUCIÓN DE LA CADENA
    # --------------------------------------------------------

    try:
        # Ejecuta la cadena con los datos proporcionados.
        #
        # Si no ocurre ningún error, devuelve
        # directamente el resultado original.
        return cadena.invoke(datos)

    # --------------------------------------------------------
    # 3.2. CAPTURA DE ERRORES INESPERADOS
    # --------------------------------------------------------

    except Exception:

        # Registra la excepción y su traceback.
        #
        # Esta información permite investigar
        # posteriormente la causa del fallo.
        logging.exception(
            "Ocurrió un error al ejecutar la cadena LangChain."
        )

        # ----------------------------------------------------
        # 3.3. RESPUESTA SEGURA AL USUARIO
        # ----------------------------------------------------

        # Devuelve un mensaje genérico en lugar
        # de propagar la excepción al llamador.
        return (
            "No fue posible completar tu solicitud. "
            "Por favor, intenta nuevamente más tarde."
        )


# ============================================================
# 4. FALLBACK ESPECIALIZADO PARA ENRUTAMIENTO
# ============================================================

def construir_fallback_enrutamiento() -> Runnable:
    """Construye una respuesta alternativa para el enrutamiento.

    Returns:
        Runnable:
            Componente que recibe los datos de entrada
            y devuelve un diccionario de recuperación.

    El resultado conserva tres campos:

        mensaje:
            Mensaje original recibido por la cadena.

        categoria:
            Valor fijo "error" que identifica
            el resultado alternativo.

        respuesta:
            Mensaje genérico que informa
            que no fue posible procesar la solicitud.

    La estructura mantiene los campos principales
    esperados del flujo de enrutamiento.

    La función construye el componente de recuperación,
    pero no lo ejecuta.
    """

    # --------------------------------------------------------
    # 4.1. DEFINICIÓN DE LA RESPUESTA SEGURA
    # --------------------------------------------------------

    def respuesta_segura(datos: dict) -> dict:
        """Conserva el mensaje y devuelve una respuesta controlada.

        Args:
            datos:
                Diccionario de entrada que debe contener
                el campo mensaje.

        Returns:
            dict:
                Diccionario con el mensaje original,
                la categoría error y una respuesta segura.

        La función no intenta reclasificar el mensaje
        ni ejecutar nuevamente la cadena principal.
        """

        # Construye una respuesta con estructura
        # compatible con el flujo de enrutamiento.
        return {
            "mensaje": datos["mensaje"],
            "categoria": "error",
            "respuesta": (
                "No fue posible procesar tu solicitud en este momento. "
                "Por favor, intenta nuevamente más tarde."
            ),
        }

    # --------------------------------------------------------
    # 4.2. CREACIÓN DEL RUNNABLE DE RECUPERACIÓN
    # --------------------------------------------------------

    # Adapta la función Python a la interfaz Runnable.
    return RunnableLambda(respuesta_segura)


# ============================================================
# 5. ENRUTAMIENTO CON RECUPERACIÓN Y REGISTRO DE ERRORES
# ============================================================

def construir_enrutamiento_seguro(modelo: Runnable) -> Runnable:
    """Construye el enrutamiento con recuperación y registro de errores.

    Args:
        modelo:
            Componente Runnable utilizado para clasificar
            mensajes y generar respuestas especializadas.

    Returns:
        Runnable:
            Cadena de enrutamiento que incorpora
            un mecanismo alternativo de recuperación.

    Flujo de construcción:

        1. Construir la cadena principal de enrutamiento.
        2. Definir una función de recuperación.
        3. Adaptarla mediante RunnableLambda.
        4. Asociarla como fallback de la cadena principal.

    Cuando falla la cadena principal, el fallback:

        - Registra un mensaje de error.
        - Ejecuta el fallback especializado.
        - Devuelve una respuesta controlada.

    El parámetro exception_key="error" configura
    la incorporación de la excepción capturada
    a los datos entregados al fallback.

    Esta función no ejecuta el modelo
    durante la construcción de la cadena.
    """

    # --------------------------------------------------------
    # 5.1. CONSTRUCCIÓN DE LA CADENA PRINCIPAL
    # --------------------------------------------------------

    # Reutiliza el enrutamiento condicional
    # definido en el Bloque 19.
    cadena_principal = construir_cadena_enrutamiento(modelo)

    # --------------------------------------------------------
    # 5.2. DEFINICIÓN DEL MECANISMO DE RECUPERACIÓN
    # --------------------------------------------------------

    def registrar_y_recuperar(datos: dict) -> dict:
        """Registra la excepción y devuelve una respuesta segura.

        Args:
            datos:
                Diccionario de entrada entregado al fallback.

                La configuración exception_key permite
                incorporar la excepción bajo la clave error.

        Returns:
            dict:
                Respuesta alternativa construida
                mediante construir_fallback_enrutamiento().

        Registra un mensaje indicando que falló
        el enrutamiento y que se activó la recuperación.

        No registra explícitamente el traceback
        de la excepción recibida.
        """

        # ----------------------------------------------------
        # 5.3. REGISTRO DEL FALLO
        # ----------------------------------------------------

        # Registra que la cadena principal falló
        # y que se utilizará la respuesta alternativa.
        logging.error(
            "Falló el enrutamiento de LangChain. "
            "Se activó la respuesta alternativa."
        )

        # ----------------------------------------------------
        # 5.4. EJECUCIÓN DEL FALLBACK ESPECIALIZADO
        # ----------------------------------------------------

        # Construye y ejecuta el componente de recuperación.
        #
        # Devuelve el mensaje original junto con
        # la categoría error y una respuesta controlada.
        return construir_fallback_enrutamiento().invoke(datos)

    # --------------------------------------------------------
    # 5.5. CONSTRUCCIÓN DEL FALLBACK
    # --------------------------------------------------------

    # Convierte la función de registro y recuperación
    # en un componente Runnable.
    fallback = RunnableLambda(registrar_y_recuperar)

    # --------------------------------------------------------
    # 5.6. ASOCIACIÓN DEL FALLBACK CON EL ENRUTAMIENTO
    # --------------------------------------------------------

    # Incorpora la recuperación a la cadena principal.
    #
    # exception_key="error" permite que la excepción
    # capturada se incluya en los datos del fallback.
    return cadena_principal.with_fallbacks(
        [fallback],
        exception_key="error",
    )
