"""Manejo de errores en cadenas LangChain.

Bloque 20 de SkillNest.
"""
import logging
from langchain_core.runnables import Runnable, RunnableLambda
from src.enrutamiento_langchain import construir_cadena_enrutamiento

def construir_cadena_con_fallback(cadena_principal: Runnable) -> Runnable:
    """Construye una cadena con respuesta alternativa ante errores."""

    def respuesta_alternativa(datos: dict) -> str:
        """Devuelve un mensaje seguro cuando falla la cadena principal."""
        return (
            "No fue posible procesar tu solicitud en este momento. "
            "Por favor, intenta nuevamente más tarde."
        )

    fallback = RunnableLambda(respuesta_alternativa)

    return cadena_principal.with_fallbacks([fallback])


def ejecutar_cadena_segura(
    cadena: Runnable,
    datos: dict,
) -> str | dict:
    """Ejecuta una cadena y controla los errores inesperados."""
    try:
        return cadena.invoke(datos)

    except Exception:
        logging.exception(
            "Ocurrió un error al ejecutar la cadena LangChain."
        )

        return (
            "No fue posible completar tu solicitud. "
            "Por favor, intenta nuevamente más tarde."
        )


def construir_fallback_enrutamiento() -> Runnable:
    """Construye una respuesta alternativa para el enrutamiento."""

    def respuesta_segura(datos: dict) -> dict:
        """Conserva el mensaje y devuelve una respuesta controlada."""
        return {
            "mensaje": datos["mensaje"],
            "categoria": "error",
            "respuesta": (
                "No fue posible procesar tu solicitud en este momento. "
                "Por favor, intenta nuevamente más tarde."
            ),
        }

    return RunnableLambda(respuesta_segura)


def construir_enrutamiento_seguro(modelo: Runnable) -> Runnable:
    """Construye el enrutamiento con recuperación y registro de errores."""
    cadena_principal = construir_cadena_enrutamiento(modelo)

    def registrar_y_recuperar(datos: dict) -> dict:
        """Registra la excepción y devuelve una respuesta segura."""
        logging.error(
            "Falló el enrutamiento de LangChain. "
            "Se activó la respuesta alternativa."
        )

        return construir_fallback_enrutamiento().invoke(datos)

    fallback = RunnableLambda(registrar_y_recuperar)

    return cadena_principal.with_fallbacks(
        [fallback],
        exception_key="error",
    )
