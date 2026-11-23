
"""Calcula métricas de evaluación de recuperación documental en VyOps.

Este módulo proporciona funciones para medir la calidad
de los documentos recuperados por un sistema RAG.

Implementa tres métricas:

    - Precision@K:
        Proporción de documentos recuperados que son relevantes.

    - Recall@K:
        Proporción de documentos relevantes que fueron recuperados.

    - F1@K:
        Media armónica entre precisión y recall.

Estas métricas permiten evaluar el comportamiento de diferentes
configuraciones de recuperación documental y comparar resultados
según la cantidad de documentos recuperados (K).

Las funciones trabajan con identificadores de documentos,
sin acceder directamente al contenido documental.

El módulo incluye una demostración local que calcula
las métricas para distintos valores de K.

No realiza llamadas a Gemini, no consulta ChromaDB
y no modifica el índice vectorial.
"""


# ============================================================
# 1. PRECISIÓN DE RECUPERACIÓN
# ============================================================

def precision_at_k(ids_recuperados, ids_relevantes):
    """Calcula la proporción de documentos recuperados relevantes.

    Evalúa cuántos identificadores presentes en la lista
    de documentos recuperados pertenecen al conjunto
    de documentos considerados relevantes.

    Args:
        ids_recuperados (list): Identificadores de documentos
            recuperados por el sistema.
        ids_relevantes (set | list): Identificadores de
            documentos considerados relevantes.

    Returns:
        float: Proporción de documentos recuperados
            que pertenecen a los relevantes.

            Devuelve 0.0 cuando no existen documentos
            recuperados.

    Formula:
        Precision@K = documentos acertados /
                      documentos recuperados

    Notes:
        La función considera cada posición de la lista
        de documentos recuperados.

        Si un identificador relevante aparece repetido,
        cada aparición se cuenta como un acierto.

        No elimina duplicados ni modifica las colecciones
        proporcionadas.
    """

    # Sin documentos recuperados no existen aciertos
    # que puedan contabilizarse.
    if not ids_recuperados:
        return 0.0

    # Selecciona los identificadores recuperados
    # que pertenecen a la colección de relevantes.
    acertados = [
        documento_id
        for documento_id in ids_recuperados
        if documento_id in ids_relevantes
    ]

    # Divide la cantidad de aciertos por el total
    # de documentos recuperados.
    return len(acertados) / len(ids_recuperados)


# ============================================================
# 2. COBERTURA DE DOCUMENTOS RELEVANTES
# ============================================================

def recall_at_k(ids_recuperados, ids_relevantes):
    """Calcula la proporción de documentos relevantes recuperados.

    Determina cuántos identificadores relevantes diferentes
    aparecen entre los documentos recuperados.

    Args:
        ids_recuperados (list): Identificadores recuperados.
        ids_relevantes (set | list): Identificadores de
            documentos considerados relevantes.

    Returns:
        float | None: Proporción de identificadores relevantes
            únicos encontrados entre los recuperados.

            Devuelve None cuando la colección de relevantes
            está vacía.

    Formula:
        Recall@K = relevantes únicos recuperados /
                   total de relevantes únicos

    Notes:
        Se utilizan conjuntos para evitar contabilizar
        varias veces un mismo identificador relevante.

        La función conserva el comportamiento original
        de devolver None cuando no existen relevantes.

        Los identificadores deben ser compatibles
        con operaciones de conjuntos de Python.
    """

    # No se define un valor de recall cuando no existe
    # una colección de documentos relevantes.
    if not ids_relevantes:
        return None

    # Identifica las coincidencias entre documentos
    # recuperados y documentos relevantes.
    acertados = [
        documento_id
        for documento_id in ids_recuperados
        if documento_id in ids_relevantes
    ]

    # Cuenta identificadores únicos para evitar
    # duplicaciones en el cálculo de cobertura.
    return len(set(acertados)) / len(set(ids_relevantes))


# ============================================================
# 3. MÉTRICA F1
# ============================================================

def f1(precision, recall):
    """Calcula la media armónica entre precisión y recall.

    Combina ambas métricas en un único valor que permite
    evaluar conjuntamente la precisión de recuperación
    y la cobertura de documentos relevantes.

    Args:
        precision (float): Valor de precisión calculado.
        recall (float | None): Valor de recall calculado.

    Returns:
        float: Media armónica entre precisión y recall.

            Devuelve 0.0 cuando recall es None
            o cuando la suma de ambas métricas es cero.

    Formula:
        F1 = 2 * precision * recall /
             (precision + recall)

    Notes:
        La función no calcula directamente las métricas
        de recuperación: recibe sus valores previamente
        calculados.

        No aplica validaciones adicionales sobre
        el intervalo de los valores recibidos.
    """

    # Evita calcular la media armónica cuando recall
    # no está definido o el denominador es cero.
    if recall is None or precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)


# ============================================================
# 4. DEMOSTRACIÓN LOCAL
# ============================================================

if __name__ == "__main__":
    # Define una recuperación ficticia de tres documentos
    # y un conjunto de referencia con un documento relevante.
    ids_recuperados = ["doc2", "doc0", "doc4"]
    ids_relevantes = {"doc0"}

    # Calcula Precision@3 para los documentos recuperados.
    resultado = precision_at_k(ids_recuperados, ids_relevantes)

    # Calcula Recall@3 utilizando la misma referencia.
    resultado_recall = recall_at_k(
        ids_recuperados,
        ids_relevantes,
    )

    # Combina las métricas de precisión y recall
    # mediante la media armónica.
    resultado_f1 = f1(
        precision_at_k(ids_recuperados, ids_relevantes),
        recall_at_k(ids_recuperados, ids_relevantes),
    )

    # Presenta las métricas correspondientes a K=3.
    print(f"F1@3: {resultado_f1}")
    print(f"recall@3: {resultado_recall}")
    print(f"precision@3: {resultado}")

    print("\n--- EVALUACIÓN SEGÚN K ---")

    # Lista ordenada de documentos recuperados.
    #
    # Cada iteración utiliza los primeros K documentos
    # para observar cómo cambian las métricas al ampliar
    # la cantidad de resultados considerados.
    ranked = ["doc2", "doc4", "doc0", "doc1", "doc3"]

    for k in range(1, 6):
        # Selecciona los primeros K documentos.
        recuperados = ranked[:k]

        # Calcula las métricas para el subconjunto actual.
        precision = precision_at_k(recuperados, ids_relevantes)
        recall = recall_at_k(recuperados, ids_relevantes)
        f1_resultado = f1(precision, recall)

        # Presenta los valores con tres decimales
        # para facilitar la comparación entre distintos K.
        print(
            f"k={k}: "
            f"precision={precision:.3f} "
            f"recall={recall:.3f} "
            f"F1={f1_resultado:.3f}"
        )
