
"""Estima el tiempo y costo del etiquetado de datos para VyOps.

Este módulo permite calcular el esfuerzo económico asociado
a la preparación manual de ejemplos de entrenamiento
para la personalización de modelos de inteligencia artificial.

El cálculo considera tres variables:

    1. Cantidad de ejemplos que deben etiquetarse.
    2. Tiempo promedio necesario por ejemplo.
    3. Costo por hora de trabajo.

A partir de estos valores se obtienen:

    - Horas totales de trabajo.
    - Costo económico estimado.

La ejecución directa presenta un escenario que incluye:

    - Etiquetado inicial de 500 ejemplos.
    - Segunda revisión del 20 % de los ejemplos.
    - Tiempo promedio de 4 minutos por etiquetado.
    - Tiempo promedio de 2 minutos por revisión.
    - Tarifa de USD 20 por hora.
    - Conversión del esfuerzo total a jornadas de 8 horas.

Este módulo realiza cálculos aritméticos locales.

No utiliza servicios externos, modelos de lenguaje
ni llamadas a la API de Gemini.

Los resultados son estimaciones basadas en los
parámetros proporcionados, no costos facturados.
"""


# ============================================================
# 1. ESTIMACIÓN DE HORAS Y COSTOS DE ETIQUETADO
# ============================================================

def estimar_costo_de_etiquetar(
    num_ejemplos: int,
    minutos_por_ejemplo: float,
    costo_por_hora: float,
) -> tuple[float, float]:
    """Calcula las horas y el costo estimado del etiquetado.

    Estima el esfuerzo necesario para etiquetar o revisar
    un conjunto de ejemplos utilizando un tiempo promedio
    por elemento y una tarifa horaria.

    El cálculo se realiza mediante las fórmulas:

        horas = (num_ejemplos * minutos_por_ejemplo) / 60

        costo = horas * costo_por_hora

    Args:
        num_ejemplos (int):
            Cantidad de ejemplos que deben procesarse.

        minutos_por_ejemplo (float):
            Tiempo promedio de trabajo requerido
            para cada ejemplo, expresado en minutos.

        costo_por_hora (float):
            Tarifa económica correspondiente
            a una hora de trabajo.

    Returns:
        tuple[float, float]:
            Tupla que contiene:

            - horas: Tiempo total estimado en horas.
            - costo: Costo económico total estimado.

    Notes:
        La función puede utilizarse tanto para
        etiquetado inicial como para revisiones.

        No incorpora gastos administrativos,
        infraestructura, impuestos ni otros
        costos indirectos.

        No realiza redondeos internos.

        Los resultados dependen directamente
        de los valores entregados.

        No se aplican validaciones adicionales
        sobre los parámetros recibidos.
    """

    # Calcula el tiempo total en minutos
    # y lo convierte a horas dividiendo entre 60.
    horas = (num_ejemplos * minutos_por_ejemplo) / 60

    # Multiplica las horas estimadas
    # por la tarifa horaria configurada.
    costo = horas * costo_por_hora

    # Devuelve el esfuerzo en horas
    # y el costo económico correspondiente.
    return horas, costo


# ============================================================
# 2. EJECUCIÓN DEL ESCENARIO DE ESTIMACIÓN
# ============================================================

if __name__ == "__main__":
    # --------------------------------------------------------
    # 2.1. COSTO DEL ETIQUETADO INICIAL
    # --------------------------------------------------------

    # Estima el procesamiento de 500 ejemplos.
    #
    # Parámetros:
    #     - 500 ejemplos.
    #     - 4 minutos por ejemplo.
    #     - USD 20 por hora.
    horas_base, costo_base = estimar_costo_de_etiquetar(500, 4, 20)

    # --------------------------------------------------------
    # 2.2. COSTO DE LA SEGUNDA REVISIÓN
    # --------------------------------------------------------

    # Calcula el esfuerzo adicional necesario
    # para revisar el 20 % de los ejemplos.
    #
    # Parámetros:
    #     - 500 * 0.20 = 100 ejemplos.
    #     - 2 minutos por revisión.
    #     - USD 20 por hora.
    #
    # La cantidad revisada se obtiene mediante
    # una multiplicación porcentual.
    horas_revision, costo_revision = estimar_costo_de_etiquetar(
        500 * 0.20, 2, 20
    )

    # --------------------------------------------------------
    # 2.3. CONSOLIDACIÓN DE RESULTADOS
    # --------------------------------------------------------

    # Suma las horas del etiquetado inicial
    # y de la segunda revisión.
    total_horas = horas_base + horas_revision

    # Suma los costos de ambas actividades.
    total_costo = costo_base + costo_revision

    # Convierte el tiempo total a jornadas
    # laborales equivalentes de ocho horas.
    jornadas = total_horas / 8

    # --------------------------------------------------------
    # 2.4. PRESENTACIÓN DE LA ESTIMACIÓN
    # --------------------------------------------------------

    # Presenta los resultados con dos decimales
    # para horas y costos.
    print(f"Etiquetado base: {horas_base:.2f} horas, USD {costo_base:.2f}")
    print(f"Segunda revisión: {horas_revision:.2f} horas, USD {costo_revision:.2f}")
    print(f"Total: {total_horas:.2f} horas, USD {total_costo:.2f}")

    # Presenta las jornadas equivalentes
    # utilizando un decimal.
    print(f"Jornadas de 8 horas: {jornadas:.1f}")
