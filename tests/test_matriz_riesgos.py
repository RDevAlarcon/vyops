
import pytest

from matriz_riesgos import (
    RIESGOS,
    clasificar_riesgo,
    esta_en_el_limite,
)


@pytest.mark.parametrize(
    "probabilidad, impacto, puntaje, categoria",
    [
        (4, 4, 16, "CRÍTICO"),
        (3, 3, 9, "ALTO"),
        (2, 2, 4, "MEDIO"),
        (1, 2, 2, "BAJO"),
    ],
)
def test_clasificacion_de_riesgos(
    probabilidad, impacto, puntaje, categoria
):
    assert clasificar_riesgo(
        probabilidad, impacto
    ) == (puntaje, categoria)


@pytest.mark.parametrize(
    "probabilidad, impacto",
    [
        (0, 3),
        (6, 3),
        (3, 0),
        (3, 6),
    ],
)
def test_rechaza_valores_fuera_de_escala(
    probabilidad, impacto
):
    with pytest.raises(ValueError):
        clasificar_riesgo(probabilidad, impacto)


def test_existen_cinco_riesgos_documentados():
    assert len(RIESGOS) >= 5

    for riesgo in RIESGOS:
        assert riesgo["riesgo"]
        assert riesgo["mitigacion"]
        assert 1 <= riesgo["probabilidad"] <= 5
        assert 1 <= riesgo["impacto"] <= 5


def test_existe_al_menos_un_riesgo_alto_o_critico():
    categorias = [
        clasificar_riesgo(
            riesgo["probabilidad"],
            riesgo["impacto"],
        )[1]
        for riesgo in RIESGOS
    ]

    assert any(
        categoria in ("ALTO", "CRÍTICO")
        for categoria in categorias
    )


@pytest.mark.parametrize(
    "probabilidad, impacto, esperado",
    [
        (3, 3, True),
        (4, 4, True),
        (5, 5, False),
    ],
)
def test_deteccion_de_casos_limite(
    probabilidad, impacto, esperado
):
    assert esta_en_el_limite(
        probabilidad, impacto
    ) is esperado


def test_matriz_contiene_casos_limite():
    assert any(
        esta_en_el_limite(
            riesgo["probabilidad"],
            riesgo["impacto"],
        )
        for riesgo in RIESGOS
    )
