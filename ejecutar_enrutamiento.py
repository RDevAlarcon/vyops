"""Ejecuta el enrutamiento condicional de mensajes con Gemini.

Bloque 19 de SkillNest.
"""

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from src.enrutamiento_langchain import construir_cadena_enrutamiento


def main() -> None:
    """Configura Gemini y procesa un mensaje de ejemplo."""
    load_dotenv()

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("No se encontró GEMINI_API_KEY.")

    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        max_retries=0,
    )

    cadena = construir_cadena_enrutamiento(modelo)

    mensaje = (
        "¿Qué documentos necesito para solicitar "
        "una patente comercial en Chile?"
    )

    print("Ejecutando enrutamiento condicional con Gemini...")
    print(f"\nMENSAJE: {mensaje}")

    resultado = cadena.invoke({"mensaje": mensaje})

    print("\nCATEGORÍA DETECTADA:")
    print(resultado["categoria"])

    print("\nRESPUESTA FINAL:")
    print(resultado["respuesta"])


if __name__ == "__main__":
    main()