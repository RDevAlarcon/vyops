
"""Pruebas unitarias de la matriz de riesgos de VyOps.

Este módulo verifica el comportamiento de las funciones
y los datos definidos en matriz_riesgos.py.

La matriz permite evaluar riesgos utilizando dos dimensiones:

    - Probabilidad de ocurrencia.
    - Impacto potencial.

Ambas dimensiones utilizan una escala de 1 a 5.

La clasificación devuelve un puntaje y una categoría
de riesgo, según las reglas implementadas en el módulo.

Las pruebas comprueban:

    1. Clasificación de riesgos en cuatro categorías.
    2. Rechazo de valores fuera de la escala permitida.
    3. Existencia de al menos cinco riesgos documentados.
    4. Presencia de riesgos altos o críticos.
    5. Identificación de determinados casos límite.
    6. Existencia de casos límite dentro de la matriz.

Se utiliza pytest.mark.parametrize para evaluar
diferentes combinaciones de probabilidad e impacto
sin duplicar las funciones de prueba.

Estas pruebas verifican la coherencia de los datos
y las reglas de clasificación, pero no determinan
si las probabilidades, impactos o mitigaciones
representan correctamente los riesgos reales.

No realizan llamadas a Gemini ni utilizan ChromaDB.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework utilizado para ejecutar pruebas parametrizadas
# y verificar las excepciones esperadas.
import pytest

# Componentes de la matriz de riesgos:
#
# RIESGOS:
#     Colección de riesgos documentados.
#
# clasificar_riesgo:
#     Calcula el puntaje y la categoría de un riesgo.
#
# esta_en_el_limite:
#     Identifica determinadas combinaciones consideradas
#     casos límite por las reglas de la implementación.
from matriz_riesgos import (
    RIESGOS,
    clasificar_riesgo,
    esta_en_el_limite,
)


# ============================================================
# 2. CLASIFICACIÓN DE RIESGOS
# ============================================================

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
    """Verifica la clasificación de riesgos según su puntaje.

    Evalúa cuatro combinaciones de probabilidad e impacto
    correspondientes a las categorías:

        - CRÍTICO: probabilidad 4, impacto 4, puntaje 16.
        - ALTO: probabilidad 3, impacto 3, puntaje 9.
        - MEDIO: probabilidad 2, impacto 2, puntaje 4.
        - BAJO: probabilidad 1, impacto 2, puntaje 2.

    Args:
        probabilidad (int):
            Valor de probabilidad proporcionado por pytest.

        impacto (int):
            Valor de impacto proporcionado por pytest.

        puntaje (int):
            Puntaje esperado para la combinación evaluada.

        categoria (str):
            Categoría esperada del riesgo.

    La prueba comprueba que la función devuelva
    la combinación exacta de puntaje y categoría
    para cada uno de los escenarios definidos.
    """

    # Calcula la clasificación utilizando los valores
    # proporcionados por cada caso parametrizado.
    #
    # Comprueba simultáneamente el puntaje numérico
    # y la categoría de riesgo esperada.
    assert clasificar_riesgo(
        probabilidad, impacto
    ) == (puntaje, categoria)


# ============================================================
# 3. VALIDACIÓN DE LA ESCALA DE RIESGOS
# ============================================================

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
    """Comprueba el rechazo de valores fuera de la escala 1 a 5.

    Evalúa cuatro combinaciones inválidas:

        - Probabilidad inferior al mínimo permitido.
        - Probabilidad superior al máximo permitido.
        - Impacto inferior al mínimo permitido.
        - Impacto superior al máximo permitido.

    Args:
        probabilidad (int):
            Valor de probabilidad utilizado en la prueba.

        impacto (int):
            Valor de impacto utilizado en la prueba.

    Verificación:
        - clasificar_riesgo() genera ValueError
          cuando recibe cualquiera de estas combinaciones.

    Esta validación evita que los escenarios evaluados
    utilicen valores fuera de la escala definida.
    """

    # Cada combinación parametrizada debe producir
    # una excepción ValueError.
    with pytest.raises(ValueError):
        clasificar_riesgo(probabilidad, impacto)


# ============================================================
# 4. VALIDACIÓN DE RIESGOS DOCUMENTADOS
# ============================================================

def test_existen_cinco_riesgos_documentados():
    """Comprueba la existencia de riesgos documentados.

    Verifica que la colección RIESGOS contenga
    al menos cinco registros.

    Para cada riesgo comprueba:

        - Existencia de una descripción no vacía.
        - Existencia de una mitigación no vacía.
        - Probabilidad dentro de la escala de 1 a 5.
        - Impacto dentro de la escala de 1 a 5.

    La prueba verifica la presencia de información
    mínima en los registros, sin evaluar la calidad
    ni la efectividad de las medidas de mitigación.
    """

    # La matriz debe contener al menos cinco riesgos.
    assert len(RIESGOS) >= 5

    # Recorre todos los riesgos documentados
    # y verifica sus campos principales.
    for riesgo in RIESGOS:

        # La descripción del riesgo no debe estar vacía.
        assert riesgo["riesgo"]

        # Debe existir una medida de mitigación.
        assert riesgo["mitigacion"]

        # La probabilidad debe encontrarse
        # dentro de la escala permitida.
        assert 1 <= riesgo["probabilidad"] <= 5

        # El impacto también debe estar
        # dentro de la escala permitida.
        assert 1 <= riesgo["impacto"] <= 5


# ============================================================
# 5. PRESENCIA DE RIESGOS ALTOS O CRÍTICOS
# ============================================================

def test_existe_al_menos_un_riesgo_alto_o_critico():
    """Comprueba que la matriz incluya riesgos de mayor severidad.

    Clasifica cada riesgo documentado utilizando
    su probabilidad y su impacto.

    Después verifica que al menos uno de ellos
    pertenezca a las categorías:

        - ALTO.
        - CRÍTICO.

    Esta prueba comprueba la presencia de riesgos
    de estas categorías dentro del conjunto documentado.

    No determina si la clasificación asignada
    refleja adecuadamente la exposición real del proyecto.
    """

    # Obtiene la categoría de cada riesgo.
    #
    # El índice [1] selecciona la categoría devuelta
    # por clasificar_riesgo(), descartando el puntaje.
    categorias = [
        clasificar_riesgo(
            riesgo["probabilidad"],
            riesgo["impacto"],
        )[1]
        for riesgo in RIESGOS
    ]

    # Comprueba que exista al menos un riesgo
    # clasificado como ALTO o CRÍTICO.
    assert any(
        categoria in ("ALTO", "CRÍTICO")
        for categoria in categorias
    )


# ============================================================
# 6. DETECCIÓN DE CASOS LÍMITE
# ============================================================

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
    """Verifica la identificación de casos límite.

    Evalúa tres combinaciones de probabilidad e impacto:

        - (3, 3): debe identificarse como caso límite.
        - (4, 4): debe identificarse como caso límite.
        - (5, 5): no debe identificarse como caso límite.

    Args:
        probabilidad (int):
            Valor de probabilidad evaluado.

        impacto (int):
            Valor de impacto evaluado.

        esperado (bool):
            Resultado booleano esperado.

    La prueba comprueba las reglas implementadas
    por esta_en_el_limite() para estas combinaciones.

    No presupone que todas las combinaciones cercanas
    a un cambio de categoría estén cubiertas.
    """

    # Evalúa la combinación de probabilidad e impacto.
    #
    # Se utiliza "is" para comprobar que el resultado
    # sea exactamente el booleano esperado.
    assert esta_en_el_limite(
        probabilidad, impacto
    ) is esperado


# ============================================================
# 7. CASOS LÍMITE EN LA MATRIZ DOCUMENTADA
# ============================================================

def test_matriz_contiene_casos_limite():
    """Comprueba que la matriz incluya al menos un caso límite.

    Recorre los riesgos definidos en RIESGOS
    y evalúa sus valores de probabilidad e impacto
    mediante esta_en_el_limite().

    Verificación:
        - Al menos un riesgo documentado debe cumplir
          las condiciones de caso límite.

    Esta prueba complementa la validación de la función
    comprobando su aplicación sobre los datos
    de la matriz de riesgos de VyOps.
    """

    # Recorre los riesgos documentados y comprueba
    # si alguno corresponde a un caso límite.
    #
    # any() devuelve True cuando al menos
    # una de las evaluaciones es verdadera.
    assert any(
        esta_en_el_limite(
            riesgo["probabilidad"],
            riesgo["impacto"],
        )
        for riesgo in RIESGOS
    )
