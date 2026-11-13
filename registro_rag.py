
import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from latencia_rag import medir
from recuperacion import (
    BASE_DIR,
    recuperar_documentos,
    construir_prompt,
    validar_citas,
)
from tokens_embedding import contar_tokens_embedding
from configuracion_modelos import (
    MODELO_GENERACION,
    MODELO_EMBEDDING,
)
from costos_rag import calcular_costo_rag
from persistencia_rag import guardar_registro_jsonl

def extraer_consumo(respuesta_modelo):
    """Normaliza el consumo reportado por LangChain."""

    uso = respuesta_modelo.usage_metadata or {}

    entrada = uso.get("input_tokens")
    salida = uso.get("output_tokens")
    total = uso.get("total_tokens")

    detalles_entrada = uso.get("input_token_details") or {}
    detalles_salida = uso.get("output_token_details") or {}

    razonamiento = detalles_salida.get("reasoning")
    cache = detalles_entrada.get("cache_read")

    # El razonamiento es un desglose, no un consumo
    # adicional que debamos sumar a output_tokens.

    return {
        "tokens_entrada": entrada,
        "tokens_salida": salida,
        "tokens_totales": total,
        "tokens_razonamiento": razonamiento,
        "tokens_cache": cache,
        "razonamiento_reportado": razonamiento is not None,
        "uso_original": dict(uso),
    }

def ejecutar_rag_medido(pregunta, k=3):
    """Ejecuta el RAG y registra latencia y tokens."""

    load_dotenv(dotenv_path=BASE_DIR / ".env")

    tiempos = {}
    inicio_total = time.perf_counter()

    # Etapa 1: embedding de consulta + búsqueda vectorial
    with medir(tiempos, "recuperacion"):
        documentos = recuperar_documentos(pregunta, k=k)

    # Etapa 2: construcción del prompt
    with medir(tiempos, "prompt"):
        prompt = construir_prompt(pregunta, documentos)

    # Etapa 3: generación con Gemini
    modelo = ChatGoogleGenerativeAI(model=MODELO_GENERACION)

    with medir(tiempos, "generacion"):
        respuesta_modelo = modelo.invoke(prompt)

    tiempos["total_rag"] = time.perf_counter() - inicio_total

    textos = [
        bloque["text"]
        for bloque in respuesta_modelo.content_blocks
        if bloque.get("type") == "text"
    ]

    respuesta = "\n".join(textos)

    consumo = extraer_consumo(respuesta_modelo)
    modelo_real = respuesta_modelo.response_metadata.get("model_name")

    if modelo_real != MODELO_GENERACION:
        raise ValueError(
            f"Modelo inesperado: {modelo_real}. "
            f"Configurado: {MODELO_GENERACION}"
        )
    tokens_entrada = consumo["tokens_entrada"]
    tokens_salida = consumo["tokens_salida"]
    tokens_cache = consumo["tokens_cache"]

    # Conteo adicional de tokens, sin generar otro embedding.
    with medir(tiempos, "conteo_tokens_embedding"):
        tokens_embedding = contar_tokens_embedding(pregunta)

    costos = calcular_costo_rag(
        modelo_generacion=modelo_real,
        modelo_embedding=MODELO_EMBEDDING,
        tokens_entrada=tokens_entrada,
        tokens_salida=tokens_salida,
        tokens_embedding=tokens_embedding,
        tokens_cache=tokens_cache,
    )

    costo_generacion = costos["generacion_usd"]
    costo_embedding = costos["embedding_usd"]
    costo_total = costos["total_usd"]


    with medir(tiempos, "validacion_citas"):
        resultado_citas = validar_citas(respuesta, documentos)

    tiempos["total_completo"] = time.perf_counter() - inicio_total
    tiempos["total"] = tiempos["total_rag"]

    return {
        "pregunta": pregunta,
        "respuesta": respuesta,
        "fuentes": [
            doc.metadata.get("fuente", "desconocida")
            for doc in documentos
        ],
        "tokens_razonamiento": consumo["tokens_razonamiento"],
        "tokens_cache": consumo["tokens_cache"],
        "razonamiento_reportado": consumo["razonamiento_reportado"],
        "uso_original": consumo["uso_original"],
        "tiempos": tiempos,
        "tokens_entrada": consumo["tokens_entrada"],
        "tokens_salida": consumo["tokens_salida"],
        "tokens_totales": consumo["tokens_totales"],
        "validacion_citas": resultado_citas,
        "tokens_embedding": tokens_embedding,
        "costo_generacion_usd": costo_generacion,
        "costo_embedding_usd": costo_embedding,
        "costo_total_usd": costo_total,
        "modelo_generacion": modelo_real,
        "modelo_embedding": MODELO_EMBEDDING,
    }


if __name__ == "__main__":
    pregunta = (
        "¿Se puede cancelar una solicitud municipal "
        "sin autorización humana?"
    )

    resultado = ejecutar_rag_medido(pregunta)

    print("\n--- RESPUESTA ---")
    print(resultado["respuesta"])

    print("\n--- LATENCIA ---")
    for etapa, segundos in resultado["tiempos"].items():
        print(f"{etapa}: {segundos * 1000:.2f} ms")

    print("\n--- TOKENS ---")
    print(f"Entrada: {resultado['tokens_entrada']}")
    print(f"Salida: {resultado['tokens_salida']}")
    print(f"Total: {resultado['tokens_totales']}")

    print("\n--- CITAS ---")
    print(resultado["validacion_citas"])

    print("\n--- COSTOS ESTIMADOS ---")
    print(f"Tokens embedding: {resultado['tokens_embedding']}")
    print(
        f"Generación: "
        f"${resultado['costo_generacion_usd']:.7f} USD"
    )
    print(
        f"Embedding: "
        f"${resultado['costo_embedding_usd']:.7f} USD"
    )
    print(
        f"Total: "
        f"${resultado['costo_total_usd']:.7f} USD"
    )

    print("\n--- DESGLOSE DE TOKENS ---")

    razonamiento = resultado["tokens_razonamiento"]
    cache = resultado["tokens_cache"]

    print(
        "Razonamiento:",
        razonamiento if razonamiento is not None else "No informado",
    )

    print(
        "Caché:",
        cache if cache is not None else "No informado",
    )

    print(
        "Desglose de razonamiento disponible:",
        resultado["razonamiento_reportado"],
    )

    # Guardar métricas en JSONL
    ruta_registro = guardar_registro_jsonl(resultado)

    print("\n--- REGISTRO JSONL ---")
    print(f"Guardado en: {ruta_registro}")