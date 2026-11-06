
from src.herramienta_solicitudes import consultar_estado_solicitud
import pytest
from pydantic import ValidationError

def test_consultar_solicitud_con_historial() -> None:
    """Verifica que la herramienta incluya el historial solicitado."""
    resultado = consultar_estado_solicitud.invoke(
        {
            "numero_solicitud": "SOL-12345",
            "incluir_historial": True,
        }
    )

    assert "En revisión por la unidad municipal." in resultado
    assert "historial:" in resultado
    assert "Solicitud recibida." in resultado
    assert "Documentación validada." in resultado

def test_consultar_solicitud_sin_historial() -> None:
    """Verifica el valor predeterminado del historial."""
    resultado = consultar_estado_solicitud.invoke(
        {"numero_solicitud": "SOL-12345"}
    )

    assert resultado == "En revisión por la unidad municipal."
    assert "historial:" not in resultado

def test_consultar_solicitud_inexistente() -> None:
    """Verifica la respuesta ante una solicitud desconocida."""
    resultado = consultar_estado_solicitud.invoke(
        {"numero_solicitud": "SOL-99999"}
    )

    assert "No se encontró la solicitud SOL-99999" in resultado

def test_consultar_solicitud_rechaza_historial_invalido() -> None:
    """Verifica que Pydantic rechace un booleano inválido."""
    with pytest.raises(ValidationError) as error:
        consultar_estado_solicitud.invoke(
            {
                "numero_solicitud": "SOL-12345",
                "incluir_historial": "tal vez",
            }
        )

    assert "incluir_historial" in str(error.value)
    assert "bool_parsing" in str(error.value)

def test_herramienta_tiene_nombre_y_esquema() -> None:
    """Verifica el nombre y los argumentos registrados en LangChain."""
    assert consultar_estado_solicitud.name == (
        "consultar_estado_solicitud"
    )

    esquema = consultar_estado_solicitud.args_schema

    assert esquema is not None
    assert "numero_solicitud" in esquema.model_fields
    assert "incluir_historial" in esquema.model_fields
