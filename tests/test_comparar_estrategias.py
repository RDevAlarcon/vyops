
"""Pruebas unitarias del método de comparación de estrategias.

Este módulo verifica las funciones de decisión definidas
en comparar_estrategias.py.

El método compara tres alternativas:

    - RAG: recuperación de información externa para
      complementar las respuestas del modelo.

    - Fine-tuning completo: ajuste de los parámetros
      del modelo mediante datos de entrenamiento.

    - PEFT: ajuste eficiente de un subconjunto
      de parámetros del modelo.

Las pruebas comprueban:

    1. Generación de un documento de decisión para VyOps.
    2. Recomendación de RAG según los requisitos del proyecto.
    3. Detección de empates entre estrategias.
    4. Estabilidad de la recomendación ante cambios
       en una de las condiciones evaluadas.

El caso principal considera que VyOps necesita
responder consultas municipales utilizando información
actualizada y verificable.

Las puntuaciones utilizadas corresponden al método
implementado en comparar_estrategias.py.

Estas pruebas verifican la aplicación de las reglas
de decisión configuradas, no el rendimiento real
de los modelos ni de las estrategias comparadas.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Funciones que calculan las puntuaciones de las estrategias
# y generan la estructura del documento de decisión.
from comparar_estrategias import (
    recomendar_estrategia,
    generar_esqueleto_decision,
)


# ============================================================
# 2. GENERACIÓN DEL DOCUMENTO DE DECISIÓN
# ============================================================

def test_generar_esqueleto_decision_vyops():
    """Verifica la estructura del documento de decisión de VyOps.

    Define el problema del proyecto y proporciona
    puntuaciones previamente establecidas:

        - RAG: 5 puntos.
        - Fine-tuning completo: 0 puntos.
        - PEFT: 1 punto.

    La estrategia ganadora es RAG.

    Verificaciones:
        - El documento contiene sus cuatro secciones.
        - Se incluye la descripción del problema.
        - Se muestran las puntuaciones de las estrategias.
        - Se incorpora una indicación para justificar RAG.

    Esta prueba comprueba la estructura y el contenido
    mínimo del documento generado.
    """

    # Describe la necesidad de información actualizada
    # y verificable en las consultas municipales de VyOps.
    problema = (
        "VyOps necesita responder consultas municipales "
        "con información actualizada y verificable."
    )

    # Define las puntuaciones obtenidas
    # por cada estrategia de personalización.
    puntos = {
        "RAG": 5,
        "Fine-tuning completo": 0,
        "PEFT": 1,
    }

    # Identifica la estrategia ganadora.
    ganadoras = ["RAG"]

    # Genera la estructura del documento de decisión.
    documento = generar_esqueleto_decision(
        problema,
        puntos,
        ganadoras,
    )

    # Comprueba que existan las cuatro secciones
    # requeridas para documentar la decisión.
    assert "## 1. El problema" in documento
    assert "## 2. Resultado del método de decisión" in documento
    assert "## 3. Técnica elegida y por qué" in documento
    assert "## 4. Qué necesitarías para ejecutarla" in documento

    # Verifica que el documento conserve el problema
    # y las puntuaciones proporcionadas.
    assert problema in documento
    assert "- RAG: 5 puntos" in documento
    assert "- PEFT: 1 punto" in documento
    assert "- Fine-tuning completo: 0 puntos" in documento

    # Comprueba que se solicite justificar
    # la elección de la estrategia RAG.
    assert "justificar por qué RAG" in documento


# ============================================================
# 3. RECOMENDACIÓN DE RAG PARA VYOPS
# ============================================================

def test_recomienda_rag_para_vyops():
    """Verifica que el método recomiende RAG para VyOps.

    Define un escenario con las siguientes condiciones:

        - La información cambia frecuentemente.
        - No existe un problema específico de formato o tono.
        - No se dispone de un dataset grande y de calidad.
        - El presupuesto es limitado o se requiere iterar rápido.
        - No se necesitan múltiples variantes del modelo.

    Resultados esperados:
        - RAG: 5 puntos.
        - Fine-tuning completo: 0 puntos.
        - PEFT: 1 punto.

    Verificación:
        - RAG es la única estrategia ganadora.

    Esta prueba documenta el resultado esperado
    del método de decisión para el escenario definido.
    """

    # Configura las condiciones del caso principal de VyOps.
    respuestas = {
        "informacion_cambia_seguido": True,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    }

    # Calcula las puntuaciones y las estrategias ganadoras.
    puntos, ganadoras = recomendar_estrategia(respuestas)

    # Comprueba las puntuaciones esperadas.
    assert puntos == {
        "RAG": 5,
        "Fine-tuning completo": 0,
        "PEFT": 1,
    }

    # RAG debe ser la única estrategia recomendada.
    assert ganadoras == ["RAG"]


# ============================================================
# 4. DETECCIÓN DE EMPATES ENTRE ESTRATEGIAS
# ============================================================

def test_detecta_empate_entre_fine_tuning_y_peft():
    """Verifica la detección de un empate entre estrategias.

    Define un escenario donde:

        - La información no cambia frecuentemente.
        - Existe una necesidad de ajustar formato o tono.
        - Se dispone de un dataset grande y de calidad.
        - No se declara una restricción de presupuesto
          ni una necesidad de iteración rápida.
        - No se necesitan múltiples variantes del modelo.

    Resultados esperados:
        - Fine-tuning completo: 3 puntos.
        - PEFT: 3 puntos.

    Verificación:
        - Ambas estrategias aparecen como ganadoras.

    La comparación mediante conjuntos evita depender
    del orden en que se devuelvan las estrategias empatadas.
    """

    # Configura un escenario favorable al ajuste del modelo.
    respuestas = {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": True,
        "dataset_grande_y_de_calidad": True,
        "presupuesto_limitado_o_iterar_rapido": False,
        "necesita_multiples_variantes": False,
    }

    # Calcula las puntuaciones y detecta las estrategias
    # que alcanzan la puntuación máxima.
    puntos, ganadoras = recomendar_estrategia(respuestas)

    # Comprueba el empate de tres puntos.
    assert puntos["Fine-tuning completo"] == 3
    assert puntos["PEFT"] == 3

    # Verifica que ambas alternativas sean reconocidas
    # como ganadoras, independientemente de su orden.
    assert set(ganadoras) == {"Fine-tuning completo", "PEFT"}


# ============================================================
# 5. ANÁLISIS DE SENSIBILIDAD DE LA RECOMENDACIÓN
# ============================================================

def test_sensibilidad_vyops_mantiene_rag():
    """Verifica la estabilidad de la recomendación RAG.

    Modifica una condición del escenario principal:
    la información deja de considerarse frecuentemente
    cambiante.

    Se mantienen las demás condiciones:

        - No existe un problema de formato o tono.
        - No hay un dataset grande y de calidad.
        - El presupuesto es limitado o se requiere iterar rápido.
        - No se necesitan múltiples variantes.

    Resultados esperados:
        - RAG: 2 puntos.
        - Fine-tuning completo: 0 puntos.
        - PEFT: 1 punto.

    Verificación:
        - RAG continúa siendo la única estrategia ganadora.

    Esta prueba comprueba que la recomendación
    se mantenga en el escenario alternativo definido.
    """

    # Modifica la condición de actualización frecuente
    # respecto del escenario principal de VyOps.
    respuestas = {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    }

    # Vuelve a calcular las puntuaciones
    # con las condiciones modificadas.
    puntos, ganadoras = recomendar_estrategia(respuestas)

    # Comprueba que RAG conserve la puntuación más alta.
    assert puntos == {
        "RAG": 2,
        "Fine-tuning completo": 0,
        "PEFT": 1,
    }

    # La estrategia recomendada debe continuar siendo RAG.
    assert ganadoras == ["RAG"]
