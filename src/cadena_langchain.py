"""Orquestación de tres etapas con LangChain para VyOps."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from src.plantillas_langchain import (
    crear_plantilla_extraccion,
    crear_plantilla_simplificacion,
    crear_plantilla_formato,
)


def construir_cadena(modelo: Runnable) -> Runnable:
    """Conecta extracción, simplificación y formato en una cadena."""

    cadena = (
        crear_plantilla_extraccion()
        | modelo
        | StrOutputParser()
        | (lambda puntos: {"puntos": puntos})
        | crear_plantilla_simplificacion()
        | modelo
        | StrOutputParser()
        | (lambda texto_simple: {"texto_simple": texto_simple})
        | crear_plantilla_formato()
        | modelo
        | StrOutputParser()
    )

    return cadena