
import pytest

from registro_prompts import (
    RegistroDePrompts,
    calcular_huella,
    obtener_prompt_historico,
    registrar_version,
)


def test_versiones_historicas_tienen_huellas_distintas():
    v1 = registrar_version("v1")
    v2 = registrar_version("v2")

    assert v1["sha256"] != v2["sha256"]
    assert v1["version"] == "v1"
    assert v2["version"] == "v2"


def test_huellas_corresponden_al_contenido():
    for version, commit in [
        ("v1", "7c3c204"),
        ("v2", "04706ff"),
    ]:
        registro = registrar_version(version)
        prompt = obtener_prompt_historico(commit)

        assert registro["sha256"] == calcular_huella(prompt)


def test_ultima_version_es_v2():
    registro = RegistroDePrompts()

    registro.agregar(registrar_version("v1"))
    registro.agregar(registrar_version("v2"))

    assert registro.ultima()["version"] == "v2"


def test_no_permite_versiones_duplicadas():
    registro = RegistroDePrompts()
    registro.agregar(registrar_version("v1"))

    with pytest.raises(ValueError, match="ya está registrada"):
        registro.agregar(registrar_version("v1"))


def test_registro_vacio_no_tiene_ultima_version():
    registro = RegistroDePrompts()

    with pytest.raises(ValueError, match="No existen versiones"):
        registro.ultima()
