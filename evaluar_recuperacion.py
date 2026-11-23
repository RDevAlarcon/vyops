
"""Evalúa la calidad de recuperación documental del RAG de VyOps.

Bloque 27 — SkillNest.

Este módulo permite medir el rendimiento del sistema
de recuperación documental utilizando un conjunto
de preguntas y fuentes relevantes conocidas.

Para cada pregunta:
    1. Recupera documentos desde el sistema RAG.
    2. Extrae los identificadores de sus fuentes.
    3. Compara las fuentes con las referencias esperadas.
    4. Calcula precisión, recall y F1.

La evaluación se ejecuta para tres valores de K:
    - K=1: Primer documento recuperado.
    - K=3: Primeros tres documentos recuperados.
    - K=5: Primeros cinco documentos recuperados.

Los resultados individuales se utilizan para calcular
promedios de las métricas correspondientes a cada K.

El informe final se guarda en:
    resultados_evaluacion.txt

La evaluación utiliza el mecanismo de recuperación
existente en VyOps y el corpus municipal ficticio.

Este módulo no genera respuestas mediante Gemini.
Su objetivo es evaluar la recuperación de fuentes,
no la calidad del texto generado por el modelo.

La ejecución puede consultar el índice vectorial
mediante recuperar_documentos(), pero no incorpora
ni elimina documentos del índice.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Casos de evaluación con preguntas y fuentes relevantes.
from conjunto_evaluacion import CASOS_EVALUACION

# Métricas utilizadas para evaluar los documentos recuperados.
from metricas_recuperacion import (
    precision_at_k,
    recall_at_k,
    f1,
)

# Función de recuperación documental del sistema RAG.
from recuperacion import recuperar_documentos

# Permite construir la ruta del informe de resultados.
from pathlib import Path


# ============================================================
# 2. EVALUACIÓN DE UN CASO
# ============================================================

def evaluar_caso(caso, k=5):
    """Evalúa la recuperación documental para una pregunta.

    Recupera hasta K documentos utilizando la pregunta
    del caso y compara sus fuentes con las referencias
    consideradas relevantes.

    Args:
        caso (dict): Caso de evaluación con las claves:
            - pregunta: Consulta utilizada para recuperar
              documentos desde el sistema RAG.
            - relevantes: Colección de identificadores
              de fuentes consideradas relevantes.

        k (int): Cantidad de documentos solicitados
            al recuperador. Su valor predeterminado es 5.

    Returns:
        dict: Resultado de evaluación con los campos:
            - pregunta: Consulta original.
            - recuperados: Fuentes de los documentos obtenidos.
            - precision: Proporción de fuentes recuperadas
              que son relevantes.
            - recall: Proporción de fuentes relevantes
              diferentes que fueron recuperadas.
            - f1: Media armónica de precisión y recall.

    Notes:
        La evaluación compara los valores del metadato
        "fuente" de los documentos recuperados.

        Cuando un documento no contiene ese metadato,
        se utiliza el identificador "desconocida".

        Las métricas se calculan mediante las funciones
        existentes en metricas_recuperacion.py.

        La función no modifica los documentos recuperados
        ni guarda resultados en archivos.

        Los errores producidos por el recuperador
        pueden propagarse al código que la invoca.
    """

    # Recupera documentos relacionados con la pregunta.
    #
    # El parámetro K determina la cantidad solicitada
    # al mecanismo de recuperación de VyOps.
    documentos = recuperar_documentos(
        caso["pregunta"],
        k=k,
    )

    # Extrae los identificadores de fuente desde
    # los metadatos de cada documento recuperado.
    #
    # Si el metadato no está disponible, utiliza
    # el valor predeterminado "desconocida".
    fuentes_recuperadas = [
        documento.metadata.get("fuente", "desconocida")
        for documento in documentos
    ]

    # Obtiene las fuentes relevantes definidas
    # previamente para este caso de evaluación.
    relevantes = caso["relevantes"]

    # Calcula la proporción de resultados recuperados
    # cuyas fuentes pertenecen a las referencias.
    precision = precision_at_k(
        fuentes_recuperadas,
        relevantes,
    )

    # Calcula la proporción de fuentes relevantes
    # diferentes encontradas en la recuperación.
    recall = recall_at_k(
        fuentes_recuperadas,
        relevantes,
    )

    # Combina precisión y recall mediante
    # la media armónica F1.
    f1_resultado = f1(precision, recall)

    # Devuelve las métricas y las fuentes recuperadas
    # para su posterior análisis.
    return {
        "pregunta": caso["pregunta"],
        "recuperados": fuentes_recuperadas,
        "precision": precision,
        "recall": recall,
        "f1": f1_resultado,
    }


# ============================================================
# 3. EJECUCIÓN DE LA EVALUACIÓN — BLOQUE 27
# ============================================================

if __name__ == "__main__":
    # Inicializa las líneas que conformarán
    # el informe de evaluación.
    #
    # Se incluye la identificación del bloque,
    # el corpus evaluado y la cantidad de casos.
    lineas = [
        "BLOQUE 27 - EVALUACIÓN DE RECUPERACIÓN RAG",
        "Corpus: municipal ficticio VyOps",
        f"Casos evaluados: {len(CASOS_EVALUACION)}",
        "",
    ]

    # Evalúa el recuperador utilizando tres valores de K.
    #
    # Esto permite observar cómo varían las métricas
    # al considerar más documentos recuperados.
    for k in [1, 3, 5]:

        # Ejecuta todos los casos para el valor
        # de K correspondiente a esta iteración.
        resultados = [
            evaluar_caso(caso, k=k)
            for caso in CASOS_EVALUACION
        ]

        # Determina la cantidad de casos evaluados.
        total = len(resultados)

        # Calcula el promedio aritmético de precisión
        # considerando todos los casos con el mismo peso.
        precision_media = sum(
            resultado["precision"] for resultado in resultados
        ) / total

        # Calcula el promedio de recall.
        recall_medio = sum(
            resultado["recall"] for resultado in resultados
        ) / total

        # Calcula el promedio de F1.
        f1_medio = sum(
            resultado["f1"] for resultado in resultados
        ) / total

        # Agrega los resultados agregados de este K
        # al informe que se guardará posteriormente.
        lineas.extend([
            f"--- EVALUACIÓN K={k} ---",
            f"Precisión media: {precision_media:.3f}",
            f"Recall medio: {recall_medio:.3f}",
            f"F1 medio: {f1_medio:.3f}",
            "",
        ])

    # Une las líneas del informe utilizando
    # saltos de línea como separadores.
    contenido = "\n".join(lineas)

    # Construye la ruta del archivo de resultados.
    #
    # El informe se guarda en el mismo directorio
    # donde se encuentra evaluar_recuperacion.py,
    # independientemente del directorio de ejecución.
    ruta = Path(__file__).resolve().parent / "resultados_evaluacion.txt"

    # Guarda el informe en UTF-8.
    #
    # write_text() reemplaza el contenido anterior
    # si el archivo ya existe.
    ruta.write_text(contenido, encoding="utf-8")

    # Presenta el informe en consola y comunica
    # la ubicación del archivo generado.
    print(contenido)
    print(f"Resultados guardados en: {ruta}")
