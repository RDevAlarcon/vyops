
"""Pruebas del sistema de registro y versionado de prompts de VyOps.

Este módulo verifica el comportamiento de las funciones
y clases implementadas en registro_prompts.py.

El registro de prompts permite identificar versiones
históricas y comprobar su integridad mediante huellas
criptográficas SHA-256.

Las pruebas cubren cinco escenarios:

    1. Diferencias entre huellas de versiones históricas.
    2. Correspondencia entre huellas y contenido del prompt.
    3. Identificación de la última versión registrada.
    4. Rechazo de versiones duplicadas.
    5. Manejo de un registro sin versiones.

Se utiliza pytest para verificar los resultados
esperados y las excepciones de validación.

Estas pruebas se enfocan en el versionado y la integridad
del contenido registrado, sin generar respuestas
mediante modelos de inteligencia artificial.

Los identificadores de commits utilizados corresponden
a las referencias históricas definidas para las pruebas.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework utilizado para comprobar excepciones
# y ejecutar las pruebas automatizadas.
import pytest

# Componentes responsables del registro, recuperación
# y cálculo de huellas de los prompts.
from registro_prompts import (
    RegistroDePrompts,
    calcular_huella,
    obtener_prompt_historico,
    registrar_version,
)


# ============================================================
# 2. HUELLAS DE VERSIONES HISTÓRICAS
# ============================================================

def test_versiones_historicas_tienen_huellas_distintas():
    """Comprueba que las versiones históricas tengan huellas diferentes.

    Obtiene los registros correspondientes a las versiones
    v1 y v2 del prompt.

    Verificaciones:
        - Las huellas SHA-256 de ambas versiones son distintas.
        - El primer registro corresponde a la versión v1.
        - El segundo registro corresponde a la versión v2.

    Esta prueba permite comprobar que el sistema distingue
    los contenidos históricos utilizados en la evaluación.
    """

    # Obtiene el registro de la primera versión.
    v1 = registrar_version("v1")

    # Obtiene el registro de la segunda versión.
    v2 = registrar_version("v2")

    # Comprueba que las versiones tengan huellas diferentes.
    assert v1["sha256"] != v2["sha256"]

    # Verifica que cada registro conserve
    # su identificador de versión.
    assert v1["version"] == "v1"
    assert v2["version"] == "v2"


# ============================================================
# 3. INTEGRIDAD DEL CONTENIDO DE LOS PROMPTS
# ============================================================

def test_huellas_corresponden_al_contenido():
    """Verifica que las huellas correspondan al contenido histórico.

    Para cada versión definida, recupera su registro
    y el contenido histórico asociado a un commit.

    Después calcula nuevamente la huella SHA-256
    del contenido recuperado.

    Verificaciones:
        - La huella almacenada coincide con la huella
          calculada directamente desde el prompt.

    Versiones y referencias utilizadas:
        - v1: commit 7c3c204.
        - v2: commit 04706ff.

    Esta prueba comprueba la consistencia entre
    los registros de versión y sus contenidos históricos.
    """

    # Recorre las versiones y sus identificadores
    # de commit correspondientes.
    for version, commit in [
        ("v1", "7c3c204"),
        ("v2", "04706ff"),
    ]:

        # Obtiene el registro de la versión evaluada.
        registro = registrar_version(version)

        # Recupera el contenido histórico asociado al commit.
        prompt = obtener_prompt_historico(commit)

        # Comprueba que la huella registrada corresponda
        # exactamente al contenido recuperado.
        assert registro["sha256"] == calcular_huella(prompt)


# ============================================================
# 4. IDENTIFICACIÓN DE LA ÚLTIMA VERSIÓN
# ============================================================

def test_ultima_version_es_v2():
    """Comprueba que el registro identifique la última versión agregada.

    Crea un registro independiente e incorpora
    las versiones v1 y v2 en ese orden.

    Verificaciones:
        - El método ultima() devuelve la versión v2.

    Esta prueba verifica el comportamiento del registro
    cuando existen varias versiones incorporadas
    secuencialmente.
    """

    # Crea un registro de prompts inicialmente vacío.
    registro = RegistroDePrompts()

    # Incorpora las dos versiones históricas.
    registro.agregar(registrar_version("v1"))
    registro.agregar(registrar_version("v2"))

    # Comprueba que la última versión agregada
    # sea la identificada por el registro.
    assert registro.ultima()["version"] == "v2"


# ============================================================
# 5. PREVENCIÓN DE VERSIONES DUPLICADAS
# ============================================================

def test_no_permite_versiones_duplicadas():
    """Verifica el rechazo de una versión previamente registrada.

    Crea un registro y agrega inicialmente la versión v1.

    Después intenta agregar nuevamente esa misma versión.

    Verificaciones:
        - Se genera una excepción ValueError.
        - El mensaje indica que la versión ya está registrada.

    Esta validación permite evitar identificadores
    de versión repetidos dentro del mismo registro.
    """

    # Inicializa un registro independiente.
    registro = RegistroDePrompts()

    # Agrega la primera versión.
    registro.agregar(registrar_version("v1"))

    # Intenta registrar nuevamente la misma versión.
    #
    # Se espera un error que indique
    # que la versión ya está registrada.
    with pytest.raises(ValueError, match="ya está registrada"):
        registro.agregar(registrar_version("v1"))


# ============================================================
# 6. MANEJO DE REGISTROS VACÍOS
# ============================================================

def test_registro_vacio_no_tiene_ultima_version():
    """Comprueba el comportamiento de un registro sin versiones.

    Inicializa un registro de prompts vacío
    e intenta recuperar su última versión.

    Verificaciones:
        - Se genera una excepción ValueError.
        - El mensaje indica que no existen versiones.

    Esta prueba verifica que el sistema no devuelva
    una versión inexistente cuando todavía
    no se han incorporado registros.
    """

    # Crea un registro sin versiones.
    registro = RegistroDePrompts()

    # Comprueba que consultar la última versión
    # produzca el error esperado.
    with pytest.raises(ValueError, match="No existen versiones"):
        registro.ultima()
