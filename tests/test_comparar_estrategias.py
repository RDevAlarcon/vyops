from comparar_estrategias import (
    recomendar_estrategia,
    generar_esqueleto_decision,
)


def test_generar_esqueleto_decision_vyops():
    problema = (
        "VyOps necesita responder consultas municipales "
        "con información actualizada y verificable."
    )

    puntos = {
        "RAG": 5,
        "Fine-tuning completo": 0,
        "PEFT": 1,
    }

    ganadoras = ["RAG"]

    documento = generar_esqueleto_decision(
        problema,
        puntos,
        ganadoras,
    )

    assert "## 1. El problema" in documento
    assert "## 2. Resultado del método de decisión" in documento
    assert "## 3. Técnica elegida y por qué" in documento
    assert "## 4. Qué necesitarías para ejecutarla" in documento

    assert problema in documento
    assert "- RAG: 5 puntos" in documento
    assert "- PEFT: 1 punto" in documento
    assert "- Fine-tuning completo: 0 puntos" in documento

    assert "justificar por qué RAG" in documento


def test_recomienda_rag_para_vyops():
    respuestas = {
        "informacion_cambia_seguido": True,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    }

    puntos, ganadoras = recomendar_estrategia(respuestas)

    assert puntos == {
        "RAG": 5,
        "Fine-tuning completo": 0,
        "PEFT": 1,
    }
    assert ganadoras == ["RAG"]


def test_detecta_empate_entre_fine_tuning_y_peft():
    respuestas = {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": True,
        "dataset_grande_y_de_calidad": True,
        "presupuesto_limitado_o_iterar_rapido": False,
        "necesita_multiples_variantes": False,
    }

    puntos, ganadoras = recomendar_estrategia(respuestas)

    assert puntos["Fine-tuning completo"] == 3
    assert puntos["PEFT"] == 3
    assert set(ganadoras) == {"Fine-tuning completo", "PEFT"}


def test_sensibilidad_vyops_mantiene_rag():
    respuestas = {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    }

    puntos, ganadoras = recomendar_estrategia(respuestas)

    assert puntos == {
        "RAG": 2,
        "Fine-tuning completo": 0,
        "PEFT": 1,
    }
    assert ganadoras == ["RAG"]