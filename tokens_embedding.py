
from dotenv import load_dotenv
from google import genai

from recuperacion import BASE_DIR


def contar_tokens_embedding(texto):
    """Consulta el conteo de tokens del modelo de embeddings."""

    load_dotenv(dotenv_path=BASE_DIR / ".env")

    cliente = genai.Client()

    respuesta = cliente.models.count_tokens(
        model="gemini-embedding-001",
        contents=texto,
    )

    return respuesta.total_tokens


if __name__ == "__main__":
    pregunta = (
        "¿Se puede cancelar una solicitud municipal "
        "sin autorización humana?"
    )

    try:
        tokens = contar_tokens_embedding(pregunta)

        print("Modelo: gemini-embedding-001")
        print(f"Tokens de la pregunta: {tokens}")

    except Exception as error:
        print("El conteo de tokens no pudo completarse.")
        print(f"Tipo de error: {type(error).__name__}")
        print(f"Detalle: {error}")
