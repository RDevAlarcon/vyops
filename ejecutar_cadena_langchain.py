"""Ejecuta la cadena de tres etapas de LangChain con Gemini.

Bloque 18 de SkillNest.
"""

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from src.cadena_langchain import construir_cadena


def main() -> None:
    """Configura Gemini y procesa un informe de evaluación."""

    load_dotenv()

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("No se encontró GEMINI_API_KEY.")

    # Este modelo utiliza parámetros de muestreo fijos.
    # No admite controlar la temperatura desde esta integración.
    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        max_retries=0,
    )

    cadena = construir_cadena(modelo)

    informe = (
        "Se evaluó un modelo de inteligencia artificial con "
        "20 preguntas sobre programación Python. "
        "Respondió correctamente 16 preguntas y cometió "
        "4 errores. Dos errores fueron sobre diccionarios "
        "y otros dos sobre manejo de excepciones. "
        "El porcentaje de respuestas correctas fue del 80%."
    )

    print("Ejecutando cadena de tres etapas con Gemini...")

    resultado = cadena.invoke({"texto": informe})

    print("\nRESULTADO FINAL:")
    print(resultado)


if __name__ == "__main__":
    main()