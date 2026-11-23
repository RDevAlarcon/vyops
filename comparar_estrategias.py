
"""Compara estrategias de personalización de modelos para VyOps.

Este módulo implementa un método de decisión basado
en puntuaciones para comparar tres alternativas:

    - RAG:
      Recuperación de información documental para
      proporcionar contexto actualizado al modelo.

    - Fine-tuning completo:
      Ajuste de los parámetros del modelo mediante
      un conjunto de datos de entrenamiento.

    - PEFT:
      Ajuste eficiente de parámetros para adaptar
      el comportamiento del modelo.

La comparación considera cinco criterios:

    1. Frecuencia de actualización de la información.
    2. Necesidad de modificar el formato o tono.
    3. Disponibilidad de un dataset grande y de calidad.
    4. Restricciones presupuestarias o rapidez de iteración.
    5. Necesidad de mantener múltiples variantes.

Cada criterio aporta puntos a una o más estrategias.

El módulo permite:

    - Calcular puntuaciones por estrategia.
    - Identificar la estrategia con mayor puntuación.
    - Detectar empates entre alternativas.
    - Realizar análisis de sensibilidad.
    - Generar un borrador de decisión en Markdown.
    - Evaluar la estrategia propuesta para VyOps.

El método es una herramienta de apoyo a la decisión.
Sus puntuaciones representan reglas predefinidas,
no mediciones empíricas de rendimiento.

La ejecución directa puede crear el archivo
decision_personalizacion.md si todavía no existe.

No utiliza Gemini ni realiza llamadas a servicios externos.
"""


# ============================================================
# 1. EVALUACIÓN DE ESTRATEGIAS
# ============================================================

def recomendar_estrategia(respuestas):
    """Calcula las puntuaciones de RAG, fine-tuning y PEFT.

    Evalúa cinco criterios mediante valores booleanos
    y asigna puntos a las estrategias correspondientes.

    Reglas de puntuación:

        Información que cambia frecuentemente:
            RAG: +3

        Problema de formato o tono:
            PEFT: +2
            Fine-tuning completo: +1

        Dataset grande y de calidad:
            Fine-tuning completo: +2
            PEFT: +1

        Presupuesto limitado o iteración rápida:
            RAG: +2
            PEFT: +1

        Necesidad de múltiples variantes:
            PEFT: +2

    Args:
        respuestas (dict):
            Diccionario con los siguientes campos:

            - informacion_cambia_seguido
            - problema_de_formato_o_tono
            - dataset_grande_y_de_calidad
            - presupuesto_limitado_o_iterar_rapido
            - necesita_multiples_variantes

            Cada campo indica si se cumple el criterio.

    Returns:
        tuple:
            Contiene dos elementos:

            puntos (dict):
                Puntuación acumulada para cada estrategia.

            ganadoras (list[str]):
                Estrategias que alcanzan la puntuación máxima.

                Puede contener más de una alternativa
                cuando existe un empate.

    Notes:
        Las puntuaciones comienzan en cero.

        Los criterios se evalúan de manera independiente.

        No se establece una preferencia automática
        para resolver empates.

        La función presupone que el diccionario contiene
        todas las claves requeridas.

        No modifica el diccionario de entrada.
    """

    # Inicializa las puntuaciones de las tres estrategias.
    puntos = {
        "RAG": 0,
        "Fine-tuning completo": 0,
        "PEFT": 0,
    }

    # --------------------------------------------------------
    # 1.1. INFORMACIÓN CAMBIANTE
    # --------------------------------------------------------

    # Favorece RAG cuando la información debe actualizarse
    # frecuentemente mediante fuentes documentales.
    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3

    # --------------------------------------------------------
    # 1.2. FORMATO O TONO
    # --------------------------------------------------------

    # Favorece las técnicas de ajuste cuando el problema
    # se relaciona con el comportamiento de las respuestas.
    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1

    # --------------------------------------------------------
    # 1.3. DISPONIBILIDAD DE DATOS
    # --------------------------------------------------------

    # Aumenta la puntuación de las técnicas de ajuste
    # cuando existe un dataset grande y de calidad.
    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1

    # --------------------------------------------------------
    # 1.4. PRESUPUESTO Y RAPIDEZ
    # --------------------------------------------------------

    # Favorece RAG y PEFT cuando existen restricciones
    # de presupuesto o se requiere iterar rápidamente.
    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1

    # --------------------------------------------------------
    # 1.5. MÚLTIPLES VARIANTES
    # --------------------------------------------------------

    # Favorece PEFT cuando se necesitan distintas
    # adaptaciones del modelo.
    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2

    # --------------------------------------------------------
    # 1.6. SELECCIÓN DE ESTRATEGIAS GANADORAS
    # --------------------------------------------------------

    # Identifica la puntuación más alta.
    maximo = max(puntos.values())

    # Recupera todas las estrategias que obtuvieron
    # la puntuación máxima, incluyendo posibles empates.
    ganadoras = [
        tecnica
        for tecnica, puntuacion in puntos.items()
        if puntuacion == maximo
    ]

    return puntos, ganadoras


# ============================================================
# 2. GENERACIÓN DEL DOCUMENTO DE DECISIÓN
# ============================================================

def generar_esqueleto_decision(problema, puntos, ganadoras):
    """Genera un borrador Markdown para documentar una decisión.

    Construye un documento estructurado con la descripción
    del problema, las puntuaciones obtenidas y espacios
    para justificar la estrategia seleccionada.

    Args:
        problema (str):
            Descripción del problema que se desea resolver.

        puntos (dict):
            Diccionario con las puntuaciones calculadas
            para cada estrategia.

        ganadoras (list[str]):
            Estrategias que obtuvieron la mayor puntuación.

    Returns:
        str:
            Documento Markdown con cuatro secciones:

            1. El problema.
            2. Resultado del método de decisión.
            3. Técnica elegida y por qué.
            4. Qué necesitarías para ejecutarla.

    Notes:
        Las estrategias se ordenan de mayor a menor
        puntuación.

        Si existe un empate, se incluye una indicación
        para justificar cómo se resolverá.

        Si existe una única ganadora, se solicita
        justificar su elección.

        El documento contiene marcadores [COMPLETAR]
        que deben desarrollarse posteriormente.

        Esta función solo devuelve el contenido.
        No crea ni modifica archivos.

        Se presupone que ganadoras contiene
        al menos una estrategia.
    """

    # Comprueba si existe más de una estrategia ganadora.
    empate = len(ganadoras) > 1

    # Almacena las líneas que conformarán
    # el documento Markdown.
    lineas = []

    # --------------------------------------------------------
    # 2.1. TÍTULO Y DESCRIPCIÓN DEL PROBLEMA
    # --------------------------------------------------------

    lineas.append("# Decisión de personalización")
    lineas.append("")
    lineas.append("## 1. El problema")
    lineas.append(problema)
    lineas.append("")

    # --------------------------------------------------------
    # 2.2. RESULTADOS DEL MÉTODO DE DECISIÓN
    # --------------------------------------------------------

    lineas.append("## 2. Resultado del método de decisión")

    # Ordena las estrategias por puntuación descendente.
    for tecnica, puntuacion in sorted(
        puntos.items(),
        key=lambda x: -x[1],
    ):
        # Utiliza singular o plural según la puntuación.
        unidad = "punto" if puntuacion == 1 else "puntos"

        # Agrega la estrategia y su puntuación al documento.
        lineas.append(f"- {tecnica}: {puntuacion} {unidad}")

    # Si existe empate, incorpora una indicación explícita
    # con las estrategias que comparten la puntuación máxima.
    if empate:
        lineas.append("")
        lineas.append(
            f"**Empate entre: {', '.join(ganadoras)}**"
        )

    # --------------------------------------------------------
    # 2.3. JUSTIFICACIÓN DE LA ESTRATEGIA
    # --------------------------------------------------------

    lineas.append("")
    lineas.append("## 3. Técnica elegida y por qué")

    if empate:
        # Solicita justificar el criterio utilizado
        # para resolver el empate.
        lineas.append(
            "[COMPLETAR: justificar cómo se resuelve el empate]"
        )
    else:
        # Solicita justificar la estrategia ganadora.
        lineas.append(
            f"[COMPLETAR: justificar por qué {ganadoras[0]} "
            "responde mejor a este caso]"
        )

    # --------------------------------------------------------
    # 2.4. REQUISITOS DE IMPLEMENTACIÓN
    # --------------------------------------------------------

    lineas.append("")
    lineas.append("## 4. Qué necesitarías para ejecutarla")

    # Reserva un espacio para documentar los recursos
    # necesarios para aplicar la estrategia seleccionada.
    lineas.append(
        "[COMPLETAR: corpus faltante o cantidad de ejemplos "
        "etiquetados necesarios]"
    )

    # Une las líneas mediante saltos de línea.
    return "\n".join(lineas)


# ============================================================
# 3. EJECUCIÓN DE LOS CASOS DE COMPARACIÓN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # 3.1. CASO 2: FORMATO Y DISPONIBILIDAD DE DATOS
    # --------------------------------------------------------

    # Define un escenario con problemas de formato o tono
    # y disponibilidad de un dataset grande y de calidad.
    respuestas_caso2 = {
        "informacion_cambia_seguido": False,
        "problema_de_formato_o_tono": True,
        "dataset_grande_y_de_calidad": True,
        "presupuesto_limitado_o_iterar_rapido": False,
        "necesita_multiples_variantes": False,
    }

    # Calcula las puntuaciones y las estrategias ganadoras.
    puntos, ganadoras = recomendar_estrategia(respuestas_caso2)

    print("Caso 2:", puntos)
    print("Candidatas empatadas:", ganadoras)

    # --------------------------------------------------------
    # 3.2. ANÁLISIS DE SENSIBILIDAD DEL CASO 2
    # --------------------------------------------------------

    # Examina cómo cambia la recomendación cuando
    # se invierte individualmente cada criterio.
    print("\nAnálisis de sensibilidad:")

    for clave in respuestas_caso2:

        # Crea una copia para conservar intacto
        # el escenario original.
        variante = dict(respuestas_caso2)

        # Invierte únicamente el criterio actual.
        variante[clave] = not variante[clave]

        # Recalcula las puntuaciones con la variante.
        puntos_variante, ganadoras_variante = recomendar_estrategia(
            variante
        )

        # Determina si cambió el conjunto de ganadoras.
        #
        # La comparación utiliza conjuntos para que
        # el orden de las estrategias no afecte el resultado.
        cambio = (
            "CAMBIA"
            if set(ganadoras_variante) != set(ganadoras)
            else "igual"
        )

        print(
            f"{clave} -> {variante[clave]}: "
            f"{ganadoras_variante} [{cambio}]"
        )

    # --------------------------------------------------------
    # 3.3. CASO 1: INFORMACIÓN CAMBIANTE
    # --------------------------------------------------------

    print("\nCaso 1 — Información cambiante:")

    # Define un escenario que requiere información
    # actualizada y considera restricciones de recursos.
    respuestas_caso1 = {
        "informacion_cambia_seguido": True,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    }

    # Calcula las puntuaciones del primer escenario.
    puntos_caso1, ganadoras_caso1 = recomendar_estrategia(
        respuestas_caso1
    )

    print("Puntuaciones:", puntos_caso1)
    print("Estrategia recomendada:", ganadoras_caso1)

    # --------------------------------------------------------
    # 3.4. EVALUACIÓN DEL PROYECTO VYOPS
    # --------------------------------------------------------

    print("\nEvaluación real — VyOps:")

    # Define las condiciones consideradas para VyOps:
    #
    #     - Información municipal cambiante.
    #     - Sin problema principal de formato o tono.
    #     - Sin dataset grande de entrenamiento.
    #     - Necesidad de iterar con recursos limitados.
    #     - Sin necesidad inicial de múltiples variantes.
    respuestas_vyops = {
        "informacion_cambia_seguido": True,
        "problema_de_formato_o_tono": False,
        "dataset_grande_y_de_calidad": False,
        "presupuesto_limitado_o_iterar_rapido": True,
        "necesita_multiples_variantes": False,
    }

    # Calcula la recomendación para el proyecto.
    puntos_vyops, ganadoras_vyops = recomendar_estrategia(
        respuestas_vyops
    )

    print("Puntuaciones:", puntos_vyops)
    print("Estrategia recomendada:", ganadoras_vyops)

    # --------------------------------------------------------
    # 3.5. DOCUMENTACIÓN DE LA DECISIÓN
    # --------------------------------------------------------

    # Describe el problema que motiva
    # la selección de una estrategia para VyOps.
    problema_vyops = (
        "VyOps necesita responder consultas ciudadanas con información "
        "municipal actualizada, verificable y respaldada por fuentes."
    )

    # Genera el contenido Markdown de la decisión.
    esqueleto = generar_esqueleto_decision(
        problema_vyops,
        puntos_vyops,
        ganadoras_vyops,
    )

    print("\nDocumento generado:")
    print(esqueleto)

    # --------------------------------------------------------
    # 3.6. SENSIBILIDAD DE LA DECISIÓN DE VYOPS
    # --------------------------------------------------------

    print("\nSensibilidad de la decisión de VyOps:")

    # Copia las condiciones originales para evitar
    # modificar la configuración evaluada.
    respuestas_vyops_alternativas = dict(respuestas_vyops)

    # Simula un escenario donde la información municipal
    # deja de cambiar frecuentemente.
    respuestas_vyops_alternativas["informacion_cambia_seguido"] = False

    # Calcula la recomendación del escenario alternativo.
    puntos_alternativos, ganadoras_alternativas = recomendar_estrategia(
        respuestas_vyops_alternativas
    )

    # Presenta las puntuaciones y recomendaciones
    # para comparar ambos escenarios.
    print("Puntuaciones originales:", puntos_vyops)
    print("Puntuaciones alternativas:", puntos_alternativos)
    print("Recomendación original:", ganadoras_vyops)
    print("Recomendación alternativa:", ganadoras_alternativas)

    # --------------------------------------------------------
    # 3.7. PERSISTENCIA DEL DOCUMENTO
    # --------------------------------------------------------

    # Importación utilizada para construir
    # la ruta del documento de decisión.
    from pathlib import Path

    ruta_documento = Path("decision_personalizacion.md")

    # Conserva el documento si ya existe.
    #
    # Esto evita sobrescribir una versión que
    # pudiera contener justificaciones completadas.
    if ruta_documento.exists():
        print("Documento existente conservado; no se sobrescribe.")

    else:
        # Crea el documento con codificación UTF-8
        # únicamente cuando todavía no existe.
        ruta_documento.write_text(esqueleto, encoding="utf-8")

        print("Documento creado correctamente.")
