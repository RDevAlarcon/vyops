"""Pruebas automatizadas del contrato HTTP de VyOps.

Reutiliza la matriz compartida con el cliente externo y
ejecuta las solicitudes mediante TestClient, sin necesidad
de iniciar Uvicorn ni consumir servicios externos.
"""
import logging
from uuid import UUID

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from casos import (
    CASOS,
    FUENTE_ESPERADA,
    PREGUNTA_DOCUMENTAL,
    PREGUNTA_NEGATIVA,
    ejecutar_caso,
)

from servidor_pruebas import responder_simulado
from servicio.main import app


@pytest.fixture
def cliente():
    """Proporciona un cliente con lógica documental controlada."""

    # Sustituye exclusivamente la lógica documental.
    # La validación, los endpoints y los errores son reales.
    with patch(
        "servicio.logica.responder",
        side_effect=responder_simulado,
    ):
        with TestClient(
            app,
            raise_server_exceptions=False,
        ) as cliente_pruebas:
            yield cliente_pruebas


@pytest.mark.parametrize(
    "caso",
    CASOS,
    ids=[caso["id"] for caso in CASOS],
)
def test_caso(cliente, caso):
    """Comprueba el estado HTTP y el contenido esperado."""

    ok, estado, _ = ejecutar_caso(cliente, caso)

    assert ok, (
        f"{caso['id']}: esperado HTTP {caso['estado']} "
        f"con {caso['contiene']!r}; "
        f"obtenido HTTP {estado}. "
        "No se cumplió el contrato esperado."
    )

def test_contrato_respuesta(cliente):
    """CT-01: verifica la estructura y tipos de la respuesta."""

    respuesta = cliente.post(
        "/consultas",
        json={"pregunta": PREGUNTA_DOCUMENTAL},
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert set(datos) == {
        "trace_id",
        "respuesta",
        "fuentes",
        "estado",
    }

    assert isinstance(datos["trace_id"], str)
    assert isinstance(datos["respuesta"], str)
    assert isinstance(datos["fuentes"], list)
    assert isinstance(datos["estado"], str)

    assert datos["trace_id"].strip()
    assert datos["respuesta"].strip()

    assert all(
        isinstance(fuente, str)
        for fuente in datos["fuentes"]
    )


def test_horario_y_fuente(cliente):
    """CT-02: comprueba el horario y la fuente esperados."""

    respuesta = cliente.post(
        "/consultas",
        json={"pregunta": PREGUNTA_DOCUMENTAL},
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["estado"] == "respuesta_generada"
    assert "08:30" in datos["respuesta"]
    assert "13:00" in datos["respuesta"]
    assert FUENTE_ESPERADA in datos["fuentes"]


def test_abstencion_segura(cliente):
    """CT-03: verifica la respuesta sin evidencia documental."""

    respuesta = cliente.post(
        "/consultas",
        json={"pregunta": PREGUNTA_NEGATIVA},
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["estado"] == "abstencion_segura"
    assert datos["fuentes"] == []
    assert datos["respuesta"].strip()


def test_trazas_independientes(cliente):
    """CT-04: comprueba identificadores simulados únicos."""

    trazas = []

    for _ in range(10):
        respuesta = cliente.post(
            "/consultas",
            json={"pregunta": PREGUNTA_DOCUMENTAL},
        )

        assert respuesta.status_code == 200

        trace_id = respuesta.json()["trace_id"]

        # Comprueba que el identificador tiene formato UUID.
        UUID(trace_id)

        trazas.append(trace_id)

    assert len(set(trazas)) == 10


@pytest.mark.parametrize(
    "longitud",
    [3, 500],
    ids=["CT-05", "CT-06"],
)
def test_limites_validos(cliente, longitud):
    """Comprueba que ambos límites de longitud son inclusivos."""

    respuesta = cliente.post(
        "/consultas",
        json={"pregunta": "a" * longitud},
    )

    assert respuesta.status_code == 200


def test_normalizacion_espacios(cliente):
    """CT-07: comprueba la normalización antes de la lógica."""

    with patch(
        "servicio.logica.responder",
        side_effect=responder_simulado,
    ) as responder:

        respuesta = cliente.post(
            "/consultas",
            json={
                "pregunta": f"   {PREGUNTA_DOCUMENTAL}   "
            },
        )

        assert respuesta.status_code == 200

        responder.assert_called_once_with(
            PREGUNTA_DOCUMENTAL
        )


@pytest.mark.parametrize(
    "metodo,ruta,cuerpo,estado,codigo",
    [
        (
            "POST",
            "/consultas",
            {"pregunta": ""},
            422,
            "VALIDACION_ERROR",
        ),
        (
            "GET",
            "/inexistente",
            None,
            404,
            "NO_ENCONTRADO",
        ),
        (
            "GET",
            "/consultas",
            None,
            405,
            "METODO_NO_PERMITIDO",
        ),
    ],
    ids=["CT-08", "CT-09", "CT-10"],
)

def test_contrato_error(
    cliente,
    metodo,
    ruta,
    cuerpo,
    estado,
    codigo,
):
    """Comprueba el formato común de los errores HTTP."""

    respuesta = cliente.request(
        metodo,
        ruta,
        json=cuerpo,
    )

    assert respuesta.status_code == estado

    assert respuesta.headers["content-type"].startswith(
        "application/json"
    )

    datos = respuesta.json()

    assert set(datos) == {
        "codigo",
        "mensaje",
        "detalles",
    }

    assert datos["codigo"] == codigo
    assert isinstance(datos["mensaje"], str)
    assert datos["mensaje"].strip()
    assert isinstance(datos["detalles"], list)

    if estado == 422:
        assert datos["detalles"]

        for detalle in datos["detalles"]:
            assert set(detalle) == {"campo", "mensaje"}
            assert isinstance(detalle["campo"], str)
            assert isinstance(detalle["mensaje"], str)

    else:
        assert datos["detalles"] == []

    if estado == 405:
        metodos = {
            metodo.strip()
            for metodo in respuesta.headers["allow"].split(",")
        }

        assert "POST" in metodos

def test_entradas_invalidas_no_invocan_logica(cliente):
    """SEG-01: rechaza entradas inválidas antes de la lógica."""

    casos_invalidos = [
        caso for caso in CASOS
        if caso["estado"] == 422
    ]

    with patch("servicio.logica.responder") as responder:

        for caso in casos_invalidos:
            ok, estado, _ = ejecutar_caso(cliente, caso)

            assert ok, f"Incumplimiento en {caso['id']}"
            assert estado == 422

        responder.assert_not_called()


def test_validacion_no_expone_datos(cliente, caplog):
    """SEG-02: evita devolver datos sensibles de la entrada."""

    marcador = "VYOPS_SECRETO_FICTICIO_422"

    pregunta = marcador + ("a" * 600)

    with caplog.at_level(logging.INFO):
        respuesta = cliente.post(
            "/consultas",
            json={"pregunta": pregunta},
        )

    assert respuesta.status_code == 422
    assert marcador not in respuesta.text
    assert marcador not in caplog.text

    datos = respuesta.json()

    assert datos["codigo"] == "VALIDACION_ERROR"

    assert "input" not in datos

    for detalle in datos["detalles"]:
        assert set(detalle) == {"campo", "mensaje"}


def test_error_interno_no_expone_datos(cliente, caplog):
    """SEG-03: protege respuestas y registros ante fallos internos."""

    marcador = "VYOPS_SECRETO_FICTICIO_500"

    with caplog.at_level(logging.ERROR):

        with patch(
            "servicio.logica.responder",
            side_effect=RuntimeError(marcador),
        ):

            respuesta = cliente.post(
                "/consultas",
                json={"pregunta": PREGUNTA_DOCUMENTAL},
            )

    assert respuesta.status_code == 500

    assert respuesta.json() == {
        "codigo": "ERROR_INTERNO",
        "mensaje": "Ocurrió un error interno en el servicio.",
        "detalles": [],
    }

    assert marcador not in respuesta.text
    assert marcador not in caplog.text
    assert "Traceback" not in caplog.text

    # El incidente debe registrarse sin revelar su causa sensible.
    assert (
        "Error interno durante el procesamiento HTTP."
        in caplog.text
    )

    assert all(
        registro.exc_info is None
        for registro in caplog.records
        if registro.name == "servicio.errores"
    )