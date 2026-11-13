
def precision_at_k(ids_recuperados, ids_relevantes):
    """Calcula qué proporción de documentos recuperados es relevante."""

    if not ids_recuperados:
        return 0.0

    acertados = [
        documento_id
        for documento_id in ids_recuperados
        if documento_id in ids_relevantes
    ]

    return len(acertados) / len(ids_recuperados)

def recall_at_k(ids_recuperados, ids_relevantes):
    """Calcula qué proporción de documentos relevantes se recuperó."""

    if not ids_relevantes:
        return None

    acertados = [
        documento_id
        for documento_id in ids_recuperados
        if documento_id in ids_relevantes
    ]

    return len(acertados) / len(ids_relevantes)

def f1(precision, recall):
    """Calcula la media armónica de precisión y recall."""

    if recall is None or precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)


if __name__ == "__main__":
    ids_recuperados = ["doc2", "doc0", "doc4"]
    ids_relevantes = {"doc0"}

    resultado = precision_at_k(ids_recuperados, ids_relevantes)

    resultado_recall = recall_at_k(
        ids_recuperados,
        ids_relevantes,
    )
    resultado_f1 = f1(
        precision_at_k(ids_recuperados, ids_relevantes),
        recall_at_k(ids_recuperados, ids_relevantes),
    )

    print(f"F1@3: {resultado_f1}")
    print(f"recall@3: {resultado_recall}")
    print(f"precision@3: {resultado}")

    print("\n--- EVALUACIÓN SEGÚN K ---")

    ranked = ["doc2", "doc4", "doc0", "doc1", "doc3"]

    for k in range(1, 6):
        recuperados = ranked[:k]

        precision = precision_at_k(recuperados, ids_relevantes)
        recall = recall_at_k(recuperados, ids_relevantes)
        f1_resultado = f1(precision, recall)

        print(
            f"k={k}: "
            f"precision={precision:.3f} "
            f"recall={recall:.3f} "
            f"F1={f1_resultado:.3f}"
        )
