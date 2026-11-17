import pytest

from costos_personalizacion import estimar_costo_de_etiquetar


def test_costo_etiquetado_base():
    horas, costo = estimar_costo_de_etiquetar(500, 4, 20)

    assert horas == pytest.approx(33.333333)
    assert costo == pytest.approx(666.666667)


def test_costo_segunda_revision():
    horas, costo = estimar_costo_de_etiquetar(100, 2, 20)

    assert horas == pytest.approx(3.333333)
    assert costo == pytest.approx(66.666667)


def test_costo_sin_ejemplos():
    horas, costo = estimar_costo_de_etiquetar(0, 4, 20)

    assert horas == 0
    assert costo == 0


def test_costo_con_tarifa_cero():
    horas, costo = estimar_costo_de_etiquetar(60, 1, 0)

    assert horas == 1
    assert costo == 0