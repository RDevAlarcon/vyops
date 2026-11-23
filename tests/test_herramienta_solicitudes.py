
"""Pruebas unitarias de la herramienta de consulta de solicitudes de VyOps.

Este módulo verifica el comportamiento de la herramienta
consultar_estado_solicitud, definida en
src.herramienta_solicitudes.

La herramienta permite consultar el estado de una solicitud
municipal utilizando su número identificador.

También admite un parámetro opcional que determina
si se debe incluir el historial de la solicitud.

Las pruebas comprueban cinco escenarios:

    1. Consulta de una solicitud incluyendo su historial.
    2. Consulta utilizando el valor predeterminado del historial.
    3. Consulta de una solicitud inexistente.
    4. Rechazo de un valor booleano inválido mediante Pydantic.
    5. Verificación del nombre y esquema de la herramienta.

Se utiliza el método invoke() para ejecutar la herramienta
mediante la interfaz proporcionada por LangChain.

Estas pruebas verifican el contrato de entrada y salida
de la herramienta para los escenarios definidos.

No realizan modificaciones sobre solicitudes municipales.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Herramienta de LangChain utilizada para consultar
# el estado y el historial de solicitudes municipales.
from src.herramienta_solicitudes import consultar_estado_solicitud

# Framework utilizado para verificar excepciones esperadas.
import pytest

# Excepción generada cuando Pydantic detecta
# errores de validación en los argumentos de entrada.
from pydantic import ValidationError


# ============================================================
# 2. CONSULTA DE SOLICITUD CON HISTORIAL
# ============================================================

def test_consultar_solicitud_con_historial() -> None:
    """Verifica que la herramienta incluya el historial solicitado.

    Consulta la solicitud SOL-12345 estableciendo
    incluir_historial en True.

    Verificaciones:
        - La respuesta contiene el estado actual.
        - Se incluye la sección de historial.
        - Aparece el evento de recepción de la solicitud.
        - Aparece el evento de validación documental.

    Esta prueba comprueba que el parámetro opcional
    habilite la información histórica esperada.
    """

    # Ejecuta la herramienta solicitando expresamente
    # el historial de la solicitud municipal.
    resultado = consultar_estado_solicitud.invoke(
        {
            "numero_solicitud": "SOL-12345",
            "incluir_historial": True,
        }
    )

    # Comprueba que la respuesta contenga el estado actual.
    assert "En revisión por la unidad municipal." in resultado

    # Verifica que se incorpore la sección de historial.
    assert "historial:" in resultado

    # Comprueba la presencia de los eventos históricos.
    assert "Solicitud recibida." in resultado
    assert "Documentación validada." in resultado


# ============================================================
# 3. CONSULTA SIN HISTORIAL
# ============================================================

def test_consultar_solicitud_sin_historial() -> None:
    """Verifica el valor predeterminado del historial.

    Consulta la solicitud SOL-12345 sin proporcionar
    el argumento opcional incluir_historial.

    Verificaciones:
        - Se devuelve únicamente el estado esperado.
        - No se incorpora la sección de historial.

    Esta prueba comprueba el comportamiento
    predeterminado de la herramienta cuando
    se omite el parámetro opcional.
    """

    # Ejecuta la consulta proporcionando únicamente
    # el identificador de la solicitud.
    resultado = consultar_estado_solicitud.invoke(
        {"numero_solicitud": "SOL-12345"}
    )

    # La respuesta debe coincidir exactamente
    # con el estado de la solicitud.
    assert resultado == "En revisión por la unidad municipal."

    # No debe incluirse el historial cuando
    # no se solicita expresamente.
    assert "historial:" not in resultado


# ============================================================
# 4. CONSULTA DE SOLICITUD INEXISTENTE
# ============================================================

def test_consultar_solicitud_inexistente() -> None:
    """Verifica la respuesta ante una solicitud desconocida.

    Consulta el identificador SOL-99999.

    Verificación:
        - La respuesta informa que no se encontró
          la solicitud indicada.

    Este escenario comprueba que la herramienta
    proporcione un mensaje identificable cuando
    la solicitud consultada no existe.
    """

    # Consulta un identificador que no corresponde
    # a una solicitud conocida en este escenario.
    resultado = consultar_estado_solicitud.invoke(
        {"numero_solicitud": "SOL-99999"}
    )

    # Comprueba que se informe la ausencia
    # de la solicitud incluyendo su identificador.
    assert "No se encontró la solicitud SOL-99999" in resultado


# ============================================================
# 5. VALIDACIÓN DE ARGUMENTOS CON PYDANTIC
# ============================================================

def test_consultar_solicitud_rechaza_historial_invalido() -> None:
    """Verifica que Pydantic rechace un booleano inválido.

    Intenta consultar una solicitud proporcionando
    el texto "tal vez" en incluir_historial.

    El parámetro espera un valor que pueda
    validarse como booleano.

    Verificaciones:
        - Se genera una excepción ValidationError.
        - El error identifica el campo incluir_historial.
        - El error contiene el código bool_parsing.

    Esta prueba comprueba la validación del argumento
    mediante el esquema de entrada de la herramienta.
    """

    # Espera que la validación de argumentos
    # genere una excepción de Pydantic.
    with pytest.raises(ValidationError) as error:
        consultar_estado_solicitud.invoke(
            {
                "numero_solicitud": "SOL-12345",
                "incluir_historial": "tal vez",
            }
        )

    # Comprueba que el error identifique
    # el argumento que contiene el valor inválido.
    assert "incluir_historial" in str(error.value)

    # Verifica el código de error asociado
    # a la interpretación de un valor booleano.
    assert "bool_parsing" in str(error.value)


# ============================================================
# 6. CONTRATO DE LA HERRAMIENTA EN LANGCHAIN
# ============================================================

def test_herramienta_tiene_nombre_y_esquema() -> None:
    """Verifica el nombre y los argumentos registrados en LangChain.

    Comprueba que la herramienta exponga el nombre
    consultar_estado_solicitud.

    También inspecciona su esquema de argumentos
    definido mediante Pydantic.

    Verificaciones:
        - El nombre registrado coincide con el esperado.
        - Existe un esquema de argumentos.
        - El esquema contiene numero_solicitud.
        - El esquema contiene incluir_historial.

    Esta prueba verifica la presencia de los campos
    necesarios para invocar la herramienta desde LangChain.

    No comprueba las descripciones de los campos
    ni todas sus restricciones de validación.
    """

    # Comprueba el nombre con el que la herramienta
    # está registrada en LangChain.
    assert consultar_estado_solicitud.name == (
        "consultar_estado_solicitud"
    )

    # Obtiene el esquema Pydantic utilizado
    # para validar los argumentos de entrada.
    esquema = consultar_estado_solicitud.args_schema

    # La herramienta debe tener un esquema definido.
    assert esquema is not None

    # Verifica la presencia del identificador
    # obligatorio de la solicitud.
    assert "numero_solicitud" in esquema.model_fields

    # Verifica la presencia del argumento opcional
    # que controla la inclusión del historial.
    assert "incluir_historial" in esquema.model_fields
