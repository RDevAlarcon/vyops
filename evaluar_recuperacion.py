
from conjunto_evaluacion import CASOS_EVALUACION
from metricas_recuperacion import (
    precision_at_k,
    recall_at_k,
    f1,
)
from recuperacion import recuperar_documentos
from pathlib import Path

def evaluar_caso(caso, k=3):
    """Evalúa la recuperación para una pregunta."""

    documentos = recuperar_documentos(
        caso["pregunta"],
        k=k,
    )

    fuentes_recuperadas = [
        documento.metadata.get("fuente", "desconocida")
        for documento in documentos
    ]

    relevantes = caso["relevantes"]

    precision = precision_at_k(
        fuentes_recuperadas,
        relevantes,
    )

    recall = recall_at_k(
        fuentes_recuperadas,
        relevantes,
    )

    f1_resultado = f1(precision, recall)

    return {
        "pregunta": caso["pregunta"],
        "recuperados": fuentes_recuperadas,
        "precision": precision,
        "recall": recall,
        "f1": f1_resultado,
    }




if __name__ == "__main__":
    lineas = [
        "BLOQUE 27 - EVALUACIÓN DE RECUPERACIÓN RAG",
        "Corpus: municipal ficticio VyOps",
        f"Casos evaluados: {len(CASOS_EVALUACION)}",
        "",
    ]

    for k in [1, 3, 5]:
        resultados = [
            evaluar_caso(caso, k=k)
            for caso in CASOS_EVALUACION
        ]

        total = len(resultados)

        precision_media = sum(
            resultado["precision"] for resultado in resultados
        ) / total

        recall_medio = sum(
            resultado["recall"] for resultado in resultados
        ) / total

        f1_medio = sum(
            resultado["f1"] for resultado in resultados
        ) / total

        lineas.extend([
            f"--- EVALUACIÓN K={k} ---",
            f"Precisión media: {precision_media:.3f}",
            f"Recall medio: {recall_medio:.3f}",
            f"F1 medio: {f1_medio:.3f}",
            "",
        ])

    contenido = "\n".join(lineas)

    ruta = Path(__file__).resolve().parent / "resultados_evaluacion.txt"
    ruta.write_text(contenido, encoding="utf-8")

    print(contenido)
    print(f"Resultados guardados en: {ruta}")
