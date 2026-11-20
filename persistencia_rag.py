
import json
from datetime import datetime, timezone
from pathlib import Path

from recuperacion import BASE_DIR

from traza_contexto import trace_id_var
import hashlib
import math


def sanitizar_uso_original(uso):
    """Conserva únicamente contadores de tokens autorizados."""

    campos_permitidos = (
        "input_tokens",
        "output_tokens",
        "total_tokens",
    )

    if not isinstance(uso, dict):
        return {}

    return {
        campo: uso[campo]
        for campo in campos_permitidos
        if type(uso.get(campo)) is int and uso[campo] >= 0
    }


def sanitizar_fuentes(fuentes):
    """Sustituye nombres externos por identificadores opacos."""

    if not isinstance(fuentes, list):
        return []

    resultado = []

    for fuente in fuentes:
        if not isinstance(fuente, str):
            continue

        identificador = hashlib.sha256(
            fuente.encode("utf-8")
        ).hexdigest()[:16]

        resultado.append(f"fuente-{identificador}")

    return resultado

def guardar_registro_jsonl(resultado, ruta=None):
    """Guarda las métricas de una ejecución RAG en JSONL."""

    if ruta is None:
        ruta = BASE_DIR / "resultados_rag.jsonl"

    ruta = Path(ruta)
    tiempos = resultado["tiempos"]

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": resultado.get("trace_id") or trace_id_var.get(),
        "modelo_generacion": resultado["modelo_generacion"],
        "modelo_embedding": resultado["modelo_embedding"],
        "pregunta_longitud": len(resultado["pregunta"]),
        "fuentes": sanitizar_fuentes(resultado["fuentes"]),
        "latencia_rag_segundos": tiempos["total_rag"],
        "latencia_completa_segundos": tiempos["total_completo"],
        "latencia_por_etapa": tiempos,
        "tokens_entrada": resultado["tokens_entrada"],
        "tokens_salida": resultado["tokens_salida"],
        "tokens_totales": resultado["tokens_totales"],
        "tokens_razonamiento": resultado["tokens_razonamiento"],
        "tokens_cache": resultado["tokens_cache"],
        "tokens_embedding": resultado["tokens_embedding"],
        "uso_original": sanitizar_uso_original(
            resultado["uso_original"]
        ),
        "costo_generacion_usd": resultado["costo_generacion_usd"],
        "costo_embedding_usd": resultado["costo_embedding_usd"],
        "costo_total_usd": resultado["costo_total_usd"],
        "validacion_citas": resultado["validacion_citas"],
    }

    with ruta.open("a", encoding="utf-8") as archivo:
        archivo.write(
            json.dumps(registro, ensure_ascii=False) + "\n"
        )

    return ruta
