
from langchain_core.documents import Document

from recuperacion import validar_citas


def crear_documentos():
    return [
        Document(page_content="Documento uno"),
        Document(page_content="Documento dos"),
        Document(page_content="Documento tres"),
    ]


def test_cita_valida():
    resultado = validar_citas(
        "La solicitud requiere autorización [1].",
        crear_documentos(),
    )

    assert resultado["numeracion_valida"] is True
    assert resultado["citas_encontradas"] == 1
    assert resultado["citas_invalidas"] == []


def test_cita_inexistente():
    resultado = validar_citas(
        "La solicitud requiere autorización [7].",
        crear_documentos(),
    )

    assert resultado["numeracion_valida"] is False
    assert resultado["citas_invalidas"] == [7]


def test_respuesta_sin_citas():
    resultado = validar_citas(
        "No dispongo de información para responder.",
        crear_documentos(),
    )

    assert resultado["citas_encontradas"] == 0
    assert resultado["citas_invalidas"] == []
