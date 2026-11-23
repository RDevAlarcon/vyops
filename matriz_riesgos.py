
"""Gestiona la matriz de riesgos del asistente municipal VyOps.

Este módulo documenta y evalúa los riesgos identificados
durante el Bloque 32 del curso SkillNest.

Permite:
    - Mantener un catálogo de riesgos y mitigaciones.
    - Calcular puntuaciones según probabilidad e impacto.
    - Clasificar riesgos en cuatro categorías.
    - Identificar puntuaciones cercanas a cambios de categoría.
    - Ordenar los riesgos por su puntuación.
    - Determinar el requisito de supervisión humana.
    - Presentar informes individuales y tabulares.

La metodología utiliza escalas de probabilidad e impacto
de 1 a 5 y calcula el puntaje mediante su multiplicación.

Las categorías establecidas son:
    - BAJO: puntuaciones inferiores a 4.
    - MEDIO: puntuaciones desde 4 hasta 8.
    - ALTO: puntuaciones desde 9 hasta 14.
    - CRÍTICO: puntuaciones desde 15 hasta 25.

Las categorías ALTO y CRÍTICO requieren supervisión
humana según las reglas definidas en este módulo.

La matriz constituye una herramienta de evaluación
y documentación de riesgos. No ejecuta automáticamente
las medidas de mitigación descritas.

No realiza llamadas a Gemini ni modifica ChromaDB.
"""

from tabulate import tabulate


# ============================================================
# 1. CATÁLOGO DE RIESGOS
# ============================================================

# Riesgos identificados durante el Bloque 32 de SkillNest.
#
# Cada registro contiene:
#     riesgo: Descripción del escenario identificado.
#     probabilidad: Valor estimado entre 1 y 5.
#     impacto: Consecuencia estimada entre 1 y 5.
#     mitigacion: Medida propuesta para reducir el riesgo.
#
# Los valores representan la evaluación registrada
# y no se recalculan automáticamente.

RIESGOS = [
    {
        "riesgo": "Inyección de prompt en documentos recuperados",
        "probabilidad": 4,
        "impacto": 4,
        "mitigacion": "Filtrar documentos y aislar el contexto no confiable.",
    },
    {
        "riesgo": "Exposición de datos personales en logs",
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": "Evitar registrar datos sensibles y revisar los logs.",
    },
    {
        "riesgo": "Respuesta municipal sin respaldo documental",
        "probabilidad": 3,
        "impacto": 4,
        "mitigacion": "Exigir citas y responder solo con evidencia recuperada.",
    },
    {
        "riesgo": "Documentos municipales desactualizados",
        "probabilidad": 3,
        "impacto": 3,
        "mitigacion": "Controlar vigencia y actualización de las fuentes.",
    },
    {
        "riesgo": "Cambio de prompt sin aprobación humana",
        "probabilidad": 2,
        "impacto": 4,
        "mitigacion": "Exigir aprobación explícita antes de aplicar cambios.",
    },
]


# ============================================================
# 2. CLASIFICACIÓN DE RIESGOS
# ============================================================

def clasificar_riesgo(probabilidad: int, impacto: int):
    """Calcula la puntuación y categoría de un riesgo.

    Valida los valores de probabilidad e impacto y calcula
    su producto para determinar la clasificación.

    Args:
        probabilidad (int): Probabilidad estimada del riesgo,
            expresada en una escala de 1 a 5.
        impacto (int): Impacto estimado del riesgo,
            expresado en una escala de 1 a 5.

    Returns:
        tuple: Dos elementos:
            - puntaje (int): Producto de probabilidad
              por impacto.
            - categoria (str): Clasificación BAJO,
              MEDIO, ALTO o CRÍTICO.

    Raises:
        ValueError:
            Si la probabilidad o el impacto se encuentran
            fuera del intervalo permitido.

    Notes:
        Los umbrales de clasificación son:
            - CRÍTICO: puntaje >= 15.
            - ALTO: puntaje >= 9.
            - MEDIO: puntaje >= 4.
            - BAJO: puntaje < 4.

        La función utiliza los valores proporcionados
        y no modifica el catálogo de riesgos.
    """

    # Comprueba que la probabilidad esté dentro
    # de la escala definida para la matriz.
    if not (1 <= probabilidad <= 5):
        raise ValueError("La probabilidad debe estar entre 1 y 5.")

    # Comprueba que el impacto también pertenezca
    # al intervalo de evaluación permitido.
    if not (1 <= impacto <= 5):
        raise ValueError("El impacto debe estar entre 1 y 5.")

    # Calcula la puntuación mediante el producto
    # de los dos factores de evaluación.
    puntaje = probabilidad * impacto

    # Asigna la categoría de acuerdo con los umbrales.
    if puntaje >= 15:
        categoria = "CRÍTICO"
    elif puntaje >= 9:
        categoria = "ALTO"
    elif puntaje >= 4:
        categoria = "MEDIO"
    else:
        categoria = "BAJO"

    return puntaje, categoria


# ============================================================
# 3. DETECCIÓN DE CASOS LÍMITE
# ============================================================

def esta_en_el_limite(probabilidad: int, impacto: int) -> bool:
    """Identifica riesgos cercanos a un cambio de categoría.

    Evalúa si aumentar o disminuir un punto en uno
    de los factores puede modificar la categoría
    asignada al riesgo.

    Args:
        probabilidad (int): Probabilidad actual,
            dentro del intervalo de 1 a 5.
        impacto (int): Impacto actual,
            dentro del intervalo de 1 a 5.

    Returns:
        bool: True si al menos una variación válida
            de un punto cambia la categoría del riesgo.

            False si ninguna de las variaciones
            evaluadas modifica su clasificación.

    Raises:
        ValueError:
            Si los valores originales no cumplen
            las reglas de clasificar_riesgo().

    Notes:
        Se consideran cuatro variaciones:
            - Reducir la probabilidad en un punto.
            - Aumentar la probabilidad en un punto.
            - Reducir el impacto en un punto.
            - Aumentar el impacto en un punto.

        Las variaciones fuera del intervalo 1 a 5
        se omiten.

        No se modifican ambos factores simultáneamente.

        Un caso límite indica sensibilidad de la
        clasificación ante pequeños cambios, pero
        no constituye una categoría adicional.
    """

    # Determina la clasificación correspondiente
    # a los valores originales.
    _, categoria_original = clasificar_riesgo(
        probabilidad,
        impacto,
    )

    # Construye los cuatro escenarios que modifican
    # exactamente un factor en una unidad.
    variaciones = [
        (probabilidad - 1, impacto),
        (probabilidad + 1, impacto),
        (probabilidad, impacto - 1),
        (probabilidad, impacto + 1),
    ]

    for nueva_probabilidad, nuevo_impacto in variaciones:
        # Descarta escenarios que excedan los límites
        # establecidos para la matriz de riesgos.
        if not (
            1 <= nueva_probabilidad <= 5
            and 1 <= nuevo_impacto <= 5
        ):
            continue

        # Clasifica el escenario alternativo.
        _, nueva_categoria = clasificar_riesgo(
            nueva_probabilidad,
            nuevo_impacto,
        )

        # Basta una variación que cambie la categoría
        # para considerar que el riesgo está en el límite.
        if nueva_categoria != categoria_original:
            return True

    return False


# ============================================================
# 4. ORDENAMIENTO DE RIESGOS
# ============================================================

def obtener_riesgos_ordenados():
    """Ordena los riesgos por puntuación descendente.

    Calcula el producto de probabilidad e impacto
    para utilizarlo como criterio de ordenamiento.

    Returns:
        list: Nueva lista con los riesgos ordenados
            desde la puntuación más alta hasta la más baja.

    Notes:
        No modifica el orden de la lista RIESGOS original.

        En caso de puntuaciones iguales, sorted()
        conserva el orden relativo de los registros.

        El ordenamiento utiliza la puntuación numérica,
        sin aplicar criterios adicionales de desempate.
    """

    return sorted(
        RIESGOS,
        key=lambda riesgo: (
            riesgo["probabilidad"] * riesgo["impacto"]
        ),
        reverse=True,
    )


# ============================================================
# 5. INFORME DETALLADO DE RIESGOS
# ============================================================

def mostrar_detalle_riesgos():
    """Presenta una evaluación individual de cada riesgo.

    Recorre los riesgos ordenados y muestra su descripción,
    probabilidad, impacto, puntuación, categoría, mitigación,
    condición de caso límite y requisito de supervisión.

    Returns:
        None: Imprime el informe directamente en consola.

    Notes:
        Los riesgos clasificados como ALTO o CRÍTICO
        se presentan con supervisión humana REQUERIDA.

        Las demás categorías se presentan con supervisión
        humana según procedimiento.

        Esta función informa el requisito de supervisión,
        pero no ejecuta un flujo de aprobación.
    """

    print("=== DETALLE DE RIESGOS VYOPS ===")

    for riesgo in obtener_riesgos_ordenados():
        # Obtiene los factores originales de evaluación.
        probabilidad = riesgo["probabilidad"]
        impacto = riesgo["impacto"]

        # Calcula la puntuación y clasificación.
        puntaje, categoria = clasificar_riesgo(
            probabilidad,
            impacto,
        )

        # Determina si una variación de un punto
        # podría cambiar la categoría asignada.
        en_limite = esta_en_el_limite(
            probabilidad,
            impacto,
        )

        # Presenta los datos y la medida de mitigación.
        print(f"\nRiesgo: {riesgo['riesgo']}")
        print(f"Probabilidad: {probabilidad}")
        print(f"Impacto: {impacto}")
        print(f"Puntaje: {puntaje}")
        print(f"Categoría: {categoria}")
        print(f"Mitigación: {riesgo['mitigacion']}")

        print(
            "Caso límite:",
            "SÍ - revisar clasificación"
            if en_limite
            else "NO",
        )

        # Determina el requisito de supervisión
        # a partir de la categoría del riesgo.
        if categoria in ("ALTO", "CRÍTICO"):
            print("Supervisión humana: REQUERIDA")
        else:
            print("Supervisión humana: Según procedimiento")


# ============================================================
# 6. MATRIZ TABULAR DE RIESGOS
# ============================================================

def mostrar_tabla_riesgos():
    """Construye y presenta una tabla comparativa de riesgos.

    Genera una fila por cada riesgo, incorporando
    su puntuación, clasificación, mitigación,
    condición de caso límite y supervisión.

    Utiliza la biblioteca tabulate para mostrar
    la información en formato de cuadrícula.

    Returns:
        None: Imprime la tabla directamente en consola.

    Notes:
        La tabla conserva el orden descendente
        de puntuación definido por obtener_riesgos_ordenados().

        Las columnas poseen los encabezados y límites
        de anchura configurados en este módulo.

        La función no modifica los registros originales.
    """

    filas = []

    for riesgo in obtener_riesgos_ordenados():
        # Obtiene los factores de evaluación del riesgo.
        probabilidad = riesgo["probabilidad"]
        impacto = riesgo["impacto"]

        # Calcula la puntuación y la categoría.
        puntaje, categoria = clasificar_riesgo(
            probabilidad,
            impacto,
        )

        # Convierte la condición de caso límite
        # en una representación textual para la tabla.
        limite = (
            "SÍ"
            if esta_en_el_limite(probabilidad, impacto)
            else "NO"
        )

        # Asigna el requisito de supervisión humana
        # según la categoría calculada.
        supervision = (
            "REQUERIDA"
            if categoria in ("ALTO", "CRÍTICO")
            else "SEGÚN PROCEDIMIENTO"
        )

        # Agrega una fila con los datos completos
        # que se mostrarán en la matriz comparativa.
        filas.append([
            riesgo["riesgo"],
            probabilidad,
            impacto,
            puntaje,
            categoria,
            riesgo["mitigacion"],
            limite,
            supervision,
        ])

    # Define los encabezados visibles de la matriz.
    encabezados = [
        "RIESGO",
        "PROBABILIDAD",
        "IMPACTO",
        "PUNTAJE",
        "CATEGORÍA",
        "MITIGACIÓN",
        "LÍMITE",
        "SUPERVISIÓN",
    ]

    print("\n=== MATRIZ DE RIESGOS VYOPS ===\n")

    # Presenta las filas mediante tabulate,
    # manteniendo el formato y las alineaciones originales.
    print(
        tabulate(
            filas,
            headers=encabezados,
            tablefmt="grid",
            stralign="left",
            numalign="center",
            maxcolwidths=[
                35, None, None, None,
                None, 45, None, 20,
            ],
        )
    )


# ============================================================
# 7. PUNTO DE ENTRADA
# ============================================================

def main():
    """Ejecuta el informe completo de riesgos de VyOps.

    Presenta primero el detalle individual de cada riesgo
    y después la matriz comparativa en formato tabular.

    Returns:
        None: Imprime ambos informes en consola.

    Notes:
        La ejecución no modifica las puntuaciones
        ni las medidas de mitigación configuradas.
    """

    mostrar_detalle_riesgos()
    mostrar_tabla_riesgos()


if __name__ == "__main__":
    # Ejecuta el informe únicamente cuando el archivo
    # se inicia directamente, no cuando se importa.
    main()
