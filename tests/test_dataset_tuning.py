import json
from unittest.mock import Mock, patch

from google.genai import types

from dataset_tuning import (
    ejemplos,
    ejemplos_raw,
    chequear_balance,
    validar_dataset,
    esperar_a_que_termine,
)


def test_dataset_tiene_12_ejemplos():
    assert len(ejemplos) == 12


def test_dataset_esta_equilibrado():
    balance = chequear_balance(ejemplos_raw)

    assert len(balance) == 4
    assert all(cantidad == 3 for cantidad in balance.values())


def test_dataset_original_es_valido():
    assert validar_dataset(ejemplos) == []


def test_detecta_entrada_vacia():
    datos = [
        types.TuningExample(
            text_input="",
            output=json.dumps({
                "intencion": "reclamo",
                "prioridad": "alta",
            }),
        )
    ]

    problemas = validar_dataset(datos)

    assert any("text_input vacío" in p for p in problemas)


def test_detecta_entrada_duplicada():
    datos = [
        types.TuningExample(
            text_input="Solicitud repetida",
            output='{"intencion": "reclamo", "prioridad": "alta"}',
        ),
        types.TuningExample(
            text_input="Solicitud repetida",
            output='{"intencion": "reclamo", "prioridad": "baja"}',
        ),
    ]

    problemas = validar_dataset(datos)

    assert any("duplicado" in p for p in problemas)


def test_detecta_json_invalido():
    datos = [
        types.TuningExample(
            text_input="Quiero consultar mi solicitud",
            output="No es JSON",
        )
    ]

    problemas = validar_dataset(datos)

    assert any("JSON válido" in p for p in problemas)


def test_detecta_campo_faltante():
    datos = [
        types.TuningExample(
            text_input="Quiero ingresar un reclamo",
            output='{"intencion": "reclamo"}',
        )
    ]

    problemas = validar_dataset(datos)

    assert any("prioridad" in p for p in problemas)


def test_detecta_intencion_no_permitida():
    datos = [
        types.TuningExample(
            text_input="Necesito información municipal",
            output=json.dumps({
                "intencion": "desconocida",
                "prioridad": "baja",
            }),
        )
    ]

    problemas = validar_dataset(datos)

    assert any("intención no permitida" in p for p in problemas)


def test_detecta_prioridad_no_permitida():
    datos = [
        types.TuningExample(
            text_input="Quiero presentar una solicitud",
            output=json.dumps({
                "intencion": "nueva_solicitud",
                "prioridad": "urgente_maxima",
            }),
        )
    ]

    problemas = validar_dataset(datos)

    assert any("prioridad no permitida" in p for p in problemas)

def test_esperar_a_que_termine():
    cliente = Mock()

    trabajo_en_progreso = Mock()
    trabajo_en_progreso.state = types.JobState.JOB_STATE_RUNNING

    trabajo_finalizado = Mock()
    trabajo_finalizado.state = types.JobState.JOB_STATE_SUCCEEDED

    cliente.tunings.get.side_effect = [
        trabajo_en_progreso,
        trabajo_finalizado,
    ]

    with patch("dataset_tuning.time.sleep") as dormir:
        resultado = esperar_a_que_termine(
            client=cliente,
            nombre_trabajo="tunings/prueba-simulada",
            intervalo_segundos=1,
        )

    assert resultado.state == types.JobState.JOB_STATE_SUCCEEDED
    assert cliente.tunings.get.call_count == 2
    dormir.assert_called_once_with(1)

import pytest


@pytest.mark.parametrize(
    "estado_final",
    [
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    ],
)
def test_seguimiento_termina_en_estado_final(
    estado_final,
    monkeypatch,
):
    class ClienteSimulado:
        def __init__(self):
            self.consultas = 0
            self.tunings = self

        def get(self, name):
            self.consultas += 1
            return types.TuningJob(
                name=name,
                state=estado_final,
            )

    cliente = ClienteSimulado()

    def no_debe_dormir(segundos):
        raise AssertionError(
            "No debe esperar después de un estado final"
        )

    monkeypatch.setattr(
        "dataset_tuning.time.sleep",
        no_debe_dormir,
    )

    resultado = esperar_a_que_termine(
        client=cliente,
        nombre_trabajo="tunings/prueba-simulada",
        intervalo_segundos=1,
    )

    assert resultado.state == estado_final
    assert cliente.consultas == 1