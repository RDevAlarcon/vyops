"""Pruebas de la cadena LangChain de tres etapas."""

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.cadena_langchain import construir_cadena


def test_cadena_ejecuta_tres_etapas_en_orden() -> None:
    """Verifica que cada etapa reciba el resultado de la anterior."""

    respuestas = MagicMock(
        side_effect=[
            AIMessage(content="HALLAZGOS_ETAPA_1"),
            AIMessage(content="SIMPLIFICACION_ETAPA_2"),
            AIMessage(content="- RESULTADO_FINAL"),
        ]
    )

    modelo_simulado = RunnableLambda(respuestas)
    cadena = construir_cadena(modelo_simulado)

    resultado = cadena.invoke({"texto": "INFORME_ORIGINAL"})

    prompts = [
        llamada.args[0].to_string()
        for llamada in respuestas.call_args_list
    ]

    assert respuestas.call_count == 3

    assert "INFORME_ORIGINAL" in prompts[0]
    assert "HALLAZGOS_ETAPA_1" in prompts[1]
    assert "SIMPLIFICACION_ETAPA_2" in prompts[2]

    assert resultado == "- RESULTADO_FINAL"