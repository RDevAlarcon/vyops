
"""Pruebas unitarias de estimación de costos de personalización.

Este módulo verifica los cálculos realizados por
estimar_costo_de_etiquetar(), definida en
costos_personalizacion.py.

Las pruebas comprueban cuatro escenarios:

    1. Estimación base para 500 ejemplos.
    2. Estimación de una segunda revisión con 100 ejemplos.
    3. Estimación cuando no existen ejemplos.
    4. Estimación cuando la tarifa por hora es cero.

La función evaluada recibe:

    - Cantidad de ejemplos que deben etiquetarse.
    - Minutos necesarios para etiquetar cada ejemplo.
    - Tarifa de trabajo por hora.

El resultado contiene las horas estimadas
y el costo total del proceso de etiquetado.

Se utiliza pytest.approx() para comparar resultados
decimales considerando pequeñas diferencias
de precisión de punto flotante.

Estas pruebas no realizan llamadas a servicios externos.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework de pruebas utilizado para comparar
# resultados numéricos con tolerancia.
import pytest

# Función que calcula las horas de etiquetado
# y el costo asociado al trabajo.
from costos_personalizacion import estimar_costo_de_etiquetar


# ============================================================
# 2. ESTIMACIÓN BASE DE ETIQUETADO
# ============================================================

def test_costo_etiquetado_base():
    """Verifica la estimación base de horas y costos.

    Escenario:
        - 500 ejemplos.
        - 4 minutos por ejemplo.
        - Tarifa de 20 por hora.

    Resultados esperados:
        - Aproximadamente 33,33 horas.
        - Costo aproximado de 666,67.

    La prueba comprueba que el cálculo convierta
    correctamente los minutos totales a horas
    y aplique la tarifa correspondiente.
    """

    # Calcula el esfuerzo y costo de etiquetar
    # 500 ejemplos a razón de 4 minutos cada uno.
    horas, costo = estimar_costo_de_etiquetar(500, 4, 20)

    # Comprueba las horas estimadas y el costo total.
    assert horas == pytest.approx(33.333333)
    assert costo == pytest.approx(666.666667)


# ============================================================
# 3. ESTIMACIÓN DE UNA SEGUNDA REVISIÓN
# ============================================================

def test_costo_segunda_revision():
    """Verifica el costo de una segunda revisión de datos.

    Escenario:
        - 100 ejemplos.
        - 2 minutos por ejemplo.
        - Tarifa de 20 por hora.

    Resultados esperados:
        - Aproximadamente 3,33 horas.
        - Costo aproximado de 66,67.

    Este escenario comprueba el cálculo para
    un conjunto más pequeño y con menor tiempo
    de trabajo por ejemplo.
    """

    # Estima el esfuerzo de revisar 100 ejemplos
    # utilizando 2 minutos por registro.
    horas, costo = estimar_costo_de_etiquetar(100, 2, 20)

    # Verifica las horas y el costo de revisión.
    assert horas == pytest.approx(3.333333)
    assert costo == pytest.approx(66.666667)


# ============================================================
# 4. ESTIMACIÓN SIN EJEMPLOS
# ============================================================

def test_costo_sin_ejemplos():
    """Verifica el cálculo cuando no existen ejemplos.

    Escenario:
        - 0 ejemplos.
        - 4 minutos por ejemplo.
        - Tarifa de 20 por hora.

    Resultados esperados:
        - 0 horas de trabajo.
        - Costo total igual a cero.

    Comprueba que la ausencia de ejemplos
    no genere tiempo ni costos de etiquetado.
    """

    # Ejecuta la estimación con un conjunto vacío.
    horas, costo = estimar_costo_de_etiquetar(0, 4, 20)

    # Sin ejemplos no debe existir trabajo ni costo.
    assert horas == 0
    assert costo == 0


# ============================================================
# 5. ESTIMACIÓN CON TARIFA CERO
# ============================================================

def test_costo_con_tarifa_cero():
    """Verifica el cálculo cuando la tarifa es cero.

    Escenario:
        - 60 ejemplos.
        - 1 minuto por ejemplo.
        - Tarifa de 0 por hora.

    Resultados esperados:
        - 1 hora de trabajo.
        - Costo total igual a cero.

    Esta prueba comprueba que las horas estimadas
    sean independientes del valor de la tarifa.

    Una tarifa cero elimina el costo monetario,
    pero no el tiempo necesario para etiquetar.
    """

    # Calcula el esfuerzo de etiquetar 60 ejemplos
    # sin aplicar una tarifa monetaria.
    horas, costo = estimar_costo_de_etiquetar(60, 1, 0)

    # El trabajo requiere una hora, aunque su costo sea cero.
    assert horas == 1
    assert costo == 0
