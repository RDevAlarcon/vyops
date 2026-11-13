
import json
from datetime import datetime, timezone
from pathlib import Path

from recuperacion import BASE_DIR


def guardar_registro_jsonl(resultado, ruta=None):
    """Guarda las métricas de una ejecución RAG en JSONL."""

    if ruta is None:
        ruta = BASE_DIR / "resultados_rag.jsonl"

    ruta = Path(ruta)
    tiempos = resultado["tiempos"]

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modelo_generacion": resultado["modelo_generacion"],
        "modelo_embedding": resultado["modelo_embedding"],
        "pregunta": resultado["pregunta"],
        "fuentes": resultado["fuentes"],
        "latencia_rag_segundos": tiempos["total_rag"],
        "latencia_completa_segundos": tiempos["total_completo"],
        "latencia_por_etapa": tiempos,
        "tokens_entrada": resultado["tokens_entrada"],
        "tokens_salida": resultado["tokens_salida"],
        "tokens_totales": resultado["tokens_totales"],
        "tokens_razonamiento": resultado["tokens_razonamiento"],
        "tokens_cache": resultado["tokens_cache"],
        "tokens_embedding": resultado["tokens_embedding"],
        "uso_original": resultado["uso_original"],
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
