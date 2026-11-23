
"""Pruebas unitarias de las métricas de recuperación documental de VyOps.

Este módulo verifica las funciones implementadas en
metricas_recuperacion.py para evaluar los resultados
de recuperación de documentos del sistema RAG.

Las métricas evaluadas son:

    Precision@K:
        Proporción de documentos recuperados que
        corresponden a documentos relevantes.

    Recall@K:
        Proporción de documentos relevantes que
        aparecen entre los documentos recuperados.

    F1:
        Media armónica entre precisión y cobertura,
        utilizada para equilibrar ambas métricas.

Las pruebas cubren siete escenarios:

    1. Precisión con un documento relevante recuperado.
    2. Precisión sin documentos recuperados.
    3. Cobertura completa de los documentos relevantes.
    4. Cobertura cuando no existen documentos relevantes.
    5. Cálculo de F1 con precisión y cobertura diferentes.
    6. Cálculo de F1 cuando ambas métricas son cero.
    7. Tratamiento de identificadores duplicados en Recall@K.

Se utiliza pytest.approx() para comparar resultados
de punto flotante cuando corresponde.

Estas pruebas trabajan con identificadores de documentos
simulados y no realizan consultas reales a ChromaDB,
Gemini ni otros servicios externos.

Su objetivo es verificar las fórmulas de evaluación,
no la calidad semántica de los documentos recuperados.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework utilizado para ejecutar las pruebas
# y comparar resultados numéricos aproximados.
import pytest

# Funciones responsables de calcular las métricas
# de recuperación documental.
from metricas_recuperacion import (
    precision_at_k,
    recall_at_k,
    f1,
)


# ============================================================
# 2. PRECISIÓN DE LA RECUPERACIÓN
# ============================================================

def test_precision_con_un_acierto():
    """Comprueba Precision@K cuando existe un único acierto.

    Simula la recuperación de tres documentos,
    de los cuales solamente uno es relevante.

    Documentos recuperados:
        - doc2
        - doc0
        - doc4

    Documento relevante:
        - doc0

    Verificación:
        - La precisión corresponde a 1/3.

    Esta prueba comprueba que la precisión considere
    tanto los documentos relevantes recuperados
    como los documentos no relevantes incluidos
    entre los resultados.
    """

    # Define los documentos recuperados por el sistema.
    recuperados = ["doc2", "doc0", "doc4"]

    # Define el conjunto de documentos considerados relevantes.
    relevantes = {"doc0"}

    # Solo uno de los tres documentos recuperados es relevante.
    #
    # Se utiliza pytest.approx() para evitar problemas
    # de comparación exacta entre números de punto flotante.
    assert precision_at_k(recuperados, relevantes) == pytest.approx(1 / 3)


def test_precision_sin_documentos():
    """Comprueba Precision@K cuando no se recuperan documentos.

    Evalúa una lista de resultados vacía frente
    a un conjunto que contiene un documento relevante.

    Verificación:
        - La precisión devuelta es 0.0.

    Este escenario comprueba el manejo de una recuperación
    sin resultados, evitando una división entre cero.
    """

    # No existen documentos recuperados,
    # aunque hay un documento relevante conocido.
    assert precision_at_k([], {"doc0"}) == 0.0


# ============================================================
# 3. COBERTURA DE DOCUMENTOS RELEVANTES
# ============================================================

def test_recall_completo():
    """Comprueba Recall@K cuando se recuperan todos los relevantes.

    Simula tres documentos recuperados y un único
    documento relevante.

    Como doc0 está presente entre los recuperados,
    se alcanza una cobertura completa.

    Verificación:
        - Recall@K devuelve 1.0.

    Esta prueba demuestra que recuperar documentos
    adicionales no relevantes no impide alcanzar
    una cobertura del 100 % cuando todos
    los documentos relevantes están presentes.
    """

    # Define tres documentos recuperados.
    recuperados = ["doc2", "doc0", "doc4"]

    # Solo doc0 pertenece al conjunto de relevantes.
    relevantes = {"doc0"}

    # El único documento relevante fue recuperado.
    assert recall_at_k(recuperados, relevantes) == 1.0


def test_recall_sin_relevantes():
    """Comprueba Recall@K cuando no existen documentos relevantes.

    Evalúa una recuperación que contiene doc0,
    pero utiliza un conjunto de relevantes vacío.

    Verificación:
        - La función devuelve None.

    Este comportamiento distingue un escenario
    sin documentos relevantes conocidos de otro
    en el que existen relevantes, pero ninguno
    fue recuperado.

    La prueba conserva la convención definida
    por la implementación de VyOps.
    """

    # No existe un conjunto de documentos relevantes
    # contra el cual calcular la cobertura.
    assert recall_at_k(["doc0"], set()) is None


# ============================================================
# 4. MÉTRICA F1
# ============================================================

def test_f1_equilibrado():
    """Comprueba el cálculo de F1 con precisión y cobertura distintas.

    Utiliza los valores:

        - Precisión: 1/3.
        - Cobertura: 1.0.

    La media armónica de ambas métricas es 0.5.

    Verificación:
        - F1 devuelve aproximadamente 0.5.

    Esta prueba comprueba que F1 combine ambas
    métricas mediante su media armónica,
    en lugar de utilizar un promedio aritmético.
    """

    # Calcula F1 a partir de una precisión de 1/3
    # y una cobertura completa.
    assert f1(1 / 3, 1.0) == pytest.approx(0.5)


def test_f1_sin_aciertos():
    """Comprueba el cálculo de F1 cuando ambas métricas son cero.

    Evalúa una precisión y una cobertura iguales a 0.0.

    Verificación:
        - F1 devuelve 0.0.

    Este escenario comprueba que la función gestione
    el caso en que la suma de precisión y cobertura
    es cero, sin producir una división inválida.
    """

    # No existen aciertos reflejados en las métricas.
    assert f1(0.0, 0.0) == 0.0


# ============================================================
# 5. TRATAMIENTO DE DOCUMENTOS DUPLICADOS
# ============================================================

def test_recall_no_duplica_fuentes_relevantes():
    """Comprueba que Recall@K no duplique los documentos relevantes.

    Evalúa una recuperación que contiene varias
    apariciones del mismo identificador documental.

    Primer escenario:
        - doc_a aparece tres veces entre los recuperados.
        - doc_b aparece una vez.
        - Los relevantes son doc_a y doc_c.
        - Solo uno de los dos relevantes está presente.

    Segundo escenario:
        - doc_a aparece cinco veces entre los recuperados.
        - doc_a es el único documento relevante.
        - La cobertura debe permanecer en 1.0.

    Verificaciones:
        - Las repeticiones de doc_a no aumentan
          artificialmente la cobertura.
        - Recuperar varias veces el único documento
          relevante no produce un valor superior a 1.0.

    Esta prueba es importante cuando el recuperador
    devuelve múltiples fragmentos asociados
    a una misma fuente documental.
    """

    # Importa la función utilizada en esta prueba.
    #
    # Se conserva este import local tal como aparece
    # en el archivo original.
    from metricas_recuperacion import recall_at_k

    # Simula una recuperación con identificadores repetidos.
    recuperados = ["doc_a", "doc_a", "doc_a", "doc_b"]

    # Define dos documentos relevantes distintos.
    relevantes = {"doc_a", "doc_c"}

    # Solo doc_a está presente entre los recuperados.
    #
    # Sus tres apariciones deben contabilizarse
    # como un único documento relevante recuperado.
    assert recall_at_k(recuperados, relevantes) == 0.5

    # Comprueba que recuperar cinco veces doc_a
    # no aumente la cobertura por encima del 100 %.
    assert recall_at_k(["doc_a"] * 5, {"doc_a"}) == 1.0
