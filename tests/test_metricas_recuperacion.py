
import pytest

from metricas_recuperacion import (
    precision_at_k,
    recall_at_k,
    f1,
)


def test_precision_con_un_acierto():
    recuperados = ["doc2", "doc0", "doc4"]
    relevantes = {"doc0"}

    assert precision_at_k(recuperados, relevantes) == pytest.approx(1 / 3)


def test_precision_sin_documentos():
    assert precision_at_k([], {"doc0"}) == 0.0


def test_recall_completo():
    recuperados = ["doc2", "doc0", "doc4"]
    relevantes = {"doc0"}

    assert recall_at_k(recuperados, relevantes) == 1.0


def test_recall_sin_relevantes():
    assert recall_at_k(["doc0"], set()) is None


def test_f1_equilibrado():
    assert f1(1 / 3, 1.0) == pytest.approx(0.5)


def test_f1_sin_aciertos():
    assert f1(0.0, 0.0) == 0.0
