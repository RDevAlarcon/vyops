
"""Pruebas unitarias del pipeline de procesamiento de texto de VyOps.

Este módulo verifica las funciones implementadas en
src.pipeline_texto, desarrolladas durante los bloques
15 y 16 del curso SkillNest.

Las pruebas comprueban las siguientes capacidades:

    1. Limpieza y normalización de texto.
    2. Tokenización y conservación de palabras repetidas.
    3. Integración de las etapas de procesamiento.
    4. Vectorización mediante frecuencias de palabras.
    5. Cálculo de coincidencias entre textos.
    6. Cálculo de precisión, cobertura y F1.
    7. Manejo de entradas vacías.
    8. Identificación de limitaciones de las métricas léxicas.
    9. Integración del pipeline completo de evaluación.

El procesamiento utiliza comparaciones basadas en palabras
y sus frecuencias, sin recurrir a modelos generativos
ni a representaciones semánticas mediante embeddings.

Además de verificar resultados correctos, algunas pruebas
demuestran limitaciones importantes de las métricas:

    - Los sinónimos pueden reducir artificialmente F1.
    - Una respuesta con datos incorrectos puede obtener F1 alto.
    - La omisión de una negación puede cambiar el significado
      sin producir una penalización proporcional.

Estas pruebas permiten distinguir la coincidencia léxica
de la calidad semántica y factual de una respuesta.

No realizan llamadas a Gemini ni modifican ChromaDB.
"""


# ============================================================
# 1. DEPENDENCIAS DEL PIPELINE
# ============================================================

# Funciones responsables de la normalización, tokenización,
# vectorización y evaluación de coincidencias entre textos.
from src.pipeline_texto import (
    limpiar_texto,
    tokenizar,
    procesar_texto,
    vectorizar,
    calcular_coincidencia,
    contar_coincidencias,
    calcular_precision_cobertura_f1,
    calcular_metricas,
)


# ============================================================
# 2. LIMPIEZA Y NORMALIZACIÓN DE TEXTO
# ============================================================

def test_limpiar_texto_normaliza_mayusculas_y_puntuacion():
    """Verifica que la limpieza normalice el formato del texto.

    Comprueba que se eliminen los signos de puntuación,
    se conviertan las letras a minúsculas y se reduzcan
    los espacios repetidos a uno solo.

    La normalización permite comparar textos sin que
    diferencias superficiales de escritura afecten
    innecesariamente las coincidencias.
    """

    # Preparamos un texto con mayúsculas, puntuación
    # y espacios repetidos para comprobar la normalización.
    texto_original = "¡HOLA,   Mundo! ¿Cómo ESTÁS?"

    # Ejecutamos la función que queremos validar.
    resultado = limpiar_texto(texto_original)

    # Comprobamos que el texto conserve su contenido,
    # pero sin diferencias artificiales de formato.
    assert resultado == "hola mundo cómo estás"


# ============================================================
# 3. TOKENIZACIÓN DE TEXTO
# ============================================================

def test_tokenizar_conserva_palabras_repetidas():
    """Verifica que la tokenización conserve todas las palabras.

    Comprueba que el texto limpio se convierta en una lista
    de tokens, manteniendo el orden original y las palabras
    repetidas para su posterior análisis de frecuencias.

    Esta conservación es importante porque las métricas
    posteriores consideran la cantidad de apariciones
    de cada palabra.
    """

    # Preparamos un texto previamente normalizado que
    # contiene la palabra "el" en dos posiciones.
    texto_limpio = "el gato y el perro"

    # Ejecutamos la función de tokenización.
    resultado = tokenizar(texto_limpio)

    # Comprobamos que se conserven el orden y las repeticiones.
    assert resultado == ["el", "gato", "y", "el", "perro"]


# ============================================================
# 4. INTEGRACIÓN DE LIMPIEZA Y TOKENIZACIÓN
# ============================================================

def test_procesar_texto_integra_limpieza_y_tokenizacion():
    """Verifica la integración de las etapas del pipeline.

    Comprueba que procesar_texto() convierta el contenido
    a minúsculas, elimine la puntuación y devuelva una lista
    de tokens conservando las palabras repetidas.

    Esta prueba verifica el resultado conjunto de las
    etapas de limpieza y tokenización.
    """

    # Preparamos una entrada con mayúsculas, puntuación
    # y palabras repetidas.
    texto_original = "¡Hola, HOLA mundo!"

    # Ejecutamos el pipeline completo.
    resultado = procesar_texto(texto_original)

    # Verificamos que ambas etapas funcionen conjuntamente.
    assert resultado == ["hola", "hola", "mundo"]


def test_procesar_texto_vacio_devuelve_lista_vacia():
    """Verifica que el pipeline maneje textos sin contenido.

    Comprueba que una cadena vacía o formada únicamente
    por espacios y puntuación no genere tokens.

    Esta prueba cubre entradas que, después de normalizarse,
    no contienen palabras útiles para el análisis.
    """

    # Definimos entradas que no contienen palabras.
    textos_vacios = [
        "",
        "   ",
        "!!! ???",
    ]

    # Comprobamos que ninguna entrada produzca tokens.
    for texto in textos_vacios:
        resultado = procesar_texto(texto)
        assert resultado == []


# ============================================================
# 5. VECTORIZACIÓN POR FRECUENCIA DE PALABRAS
# ============================================================

def test_vectorizar_cuenta_frecuencia_de_palabras():
    """Verifica que la vectorización cuente las palabras repetidas.

    Comprueba que cada palabra aparezca como clave
    del diccionario y que su valor corresponda
    al número de veces que aparece en los tokens.

    La representación resultante es un diccionario
    de frecuencias, no un embedding semántico.
    """

    # Preparamos una lista de tokens con palabras repetidas.
    tokens = ["el", "gato", "y", "el", "perro", "gato"]

    # Ejecutamos la vectorización.
    resultado = vectorizar(tokens)

    # Comprobamos las frecuencias de todas las palabras.
    assert resultado == {
        "el": 2,
        "gato": 2,
        "y": 1,
        "perro": 1,
    }


def test_vectorizar_lista_vacia():
    """Verifica que una lista vacía no genere frecuencias.

    Comprueba que la función devuelva un diccionario
    vacío cuando no existen palabras para contar.

    Este comportamiento permite representar una entrada
    sin tokens sin introducir frecuencias artificiales.
    """

    # Ejecutamos la vectorización sin tokens.
    resultado = vectorizar([])

    # Confirmamos que no se generen registros.
    assert resultado == {}


# ============================================================
# 6. CÁLCULO DE COINCIDENCIA ENTRE TEXTOS
# ============================================================

def test_calcular_coincidencia_sin_normalizacion():
    """Verifica la coincidencia antes de limpiar los textos.

    Comprueba que las diferencias de mayúsculas y
    puntuación afecten la comparación de palabras.

    En este escenario, la coincidencia se calcula
    utilizando los textos sin normalización previa.
    """

    # Preparamos dos textos con el mismo contenido,
    # pero con diferencias de formato.
    referencia = "El cielo es azul."
    respuesta = "el cielo es azul"

    # Calculamos la coincidencia sin normalizar.
    resultado = calcular_coincidencia(
        referencia,
        respuesta,
        normalizar=False,
    )

    # Coinciden únicamente las palabras "cielo" y "es".
    # Dos coincidencias entre cuatro palabras de referencia.
    assert resultado == 0.5


def test_calcular_coincidencia_con_normalizacion():
    """Verifica que la normalización mejore la comparación.

    Comprueba que las diferencias de mayúsculas y
    puntuación desaparezcan después de procesar los textos.

    Al normalizar ambos contenidos, las palabras
    de la referencia coinciden con las de la respuesta.
    """

    # Utilizamos los mismos textos de la prueba anterior.
    referencia = "El cielo es azul."
    respuesta = "el cielo es azul"

    # Calculamos la coincidencia aplicando el pipeline.
    resultado = calcular_coincidencia(
        referencia,
        respuesta,
        normalizar=True,
    )

    # Todas las palabras coinciden después de normalizar.
    assert resultado == 1.0


def test_calcular_coincidencia_referencia_vacia():
    """Verifica el manejo de referencias sin palabras.

    Comprueba que la función devuelva cero cuando
    no existen palabras de referencia para comparar.

    Esta validación también comprueba que el cálculo
    no produzca un error por división entre cero.
    """

    # Evaluamos una referencia vacía.
    resultado = calcular_coincidencia(
        "",
        "Esta es una respuesta",
    )

    # Confirmamos que se evita una división por cero.
    assert resultado == 0.0


# ============================================================
# 7. CONTEO DE COINCIDENCIAS CON REPETICIONES
# ============================================================

def test_contar_coincidencias_considera_repeticiones():
    """Verifica que las coincidencias respeten las frecuencias.

    Comprueba que la función utilice la cantidad mínima
    de apariciones de cada palabra compartida entre
    la referencia y la respuesta.

    También verifica que las palabras adicionales
    no aumenten artificialmente las coincidencias.

    Este comportamiento permite contar coincidencias
    considerando repeticiones, en lugar de limitarse
    a identificar palabras únicas compartidas.
    """

    # La referencia contiene dos apariciones de "el"
    # y una aparición de "gato" y "duerme".
    tokens_referencia = [
        "el", "gato", "duerme", "el"
    ]

    # La respuesta contiene tres apariciones de "el",
    # una de "gato" y una palabra que no está en la referencia.
    tokens_respuesta = [
        "el", "el", "el", "gato", "sillón"
    ]

    # Ejecutamos la función que cuenta coincidencias.
    resultado = contar_coincidencias(
        tokens_referencia,
        tokens_respuesta,
    )

    # Coinciden dos apariciones de "el" y una de "gato".
    # "duerme" falta y "sillón" no pertenece a la referencia.
    assert resultado == 3


# ============================================================
# 8. PRECISIÓN, COBERTURA Y F1
# ============================================================

def test_calcular_precision_cobertura_f1_con_repeticiones():
    """Verifica las métricas considerando palabras repetidas.

    Utiliza el ejemplo del gato presentado en SkillNest.
    Comprueba que las coincidencias se calculen respetando
    la frecuencia de cada token y que F1 combine
    correctamente precisión y cobertura.

    La precisión compara las coincidencias con la cantidad
    de tokens de la respuesta.

    La cobertura compara las coincidencias con la cantidad
    de tokens de la referencia.

    F1 combina ambas métricas mediante su media armónica.
    """

    # Preparamos los textos originales del ejemplo.
    referencia = "El gato duerme en el sofá."
    respuesta = "El gato duerme en el sillón todo el día."

    # Aplicamos el pipeline del Bloque 15 para obtener
    # listas de tokens normalizados.
    tokens_referencia = procesar_texto(referencia)
    tokens_respuesta = procesar_texto(respuesta)

    # Calculamos las tres métricas del Bloque 16.
    resultado = calcular_precision_cobertura_f1(
        tokens_referencia,
        tokens_respuesta,
    )

    # Existen cinco coincidencias entre nueve tokens
    # de respuesta y seis tokens de referencia.
    assert round(resultado["precision"], 2) == 0.56
    assert round(resultado["cobertura"], 2) == 0.83

    # La media armónica de ambas métricas es aproximadamente 0.67.
    assert round(resultado["f1"], 2) == 0.67


def test_calcular_precision_cobertura_f1_con_listas_vacias():
    """Verifica que las listas vacías no provoquen errores.

    Comprueba que la función devuelva cero en las tres
    métricas cuando falta la referencia, la respuesta
    o ambas listas de tokens.

    Se evalúan los tres casos para verificar que
    el cálculo gestione correctamente denominadores vacíos.
    """

    # Definimos los tres escenarios que podrían
    # provocar una división por cero.
    casos = [
        ([], []),
        (["python", "es", "útil"], []),
        ([], ["python", "es", "útil"]),
    ]

    # Evaluamos cada escenario de manera independiente.
    for tokens_referencia, tokens_respuesta in casos:
        resultado = calcular_precision_cobertura_f1(
            tokens_referencia,
            tokens_respuesta,
        )

        # Ningún escenario debe producir coincidencias.
        assert resultado == {
            "precision": 0.0,
            "cobertura": 0.0,
            "f1": 0.0,
        }


# ============================================================
# 9. LIMITACIÓN: SINÓNIMOS Y SIGNIFICADO
# ============================================================

def test_f1_penaliza_sinonimos_con_mismo_significado():
    """Demuestra que F1 no reconoce equivalencias semánticas.

    Compara dos oraciones que expresan esencialmente
    la misma idea utilizando palabras diferentes.

    La métrica únicamente reconoce las palabras
    compartidas y no identifica que "auto" y "vehículo",
    o "veloz" y "rápido", son equivalentes en este contexto.

    Esta prueba ilustra por qué una coincidencia léxica
    baja no implica necesariamente una respuesta incorrecta.
    """

    # Definimos las dos oraciones del ejemplo de SkillNest.
    referencia = "El auto es veloz."
    respuesta = "El vehículo es rápido."

    # Normalizamos y tokenizamos ambos textos utilizando
    # el pipeline implementado durante el Bloque 15.
    tokens_referencia = procesar_texto(referencia)
    tokens_respuesta = procesar_texto(respuesta)

    # Calculamos precisión, cobertura y F1.
    resultado = calcular_precision_cobertura_f1(
        tokens_referencia,
        tokens_respuesta,
    )

    # Coinciden únicamente "el" y "es".
    # Son dos coincidencias entre cuatro tokens por lado.
    assert resultado["precision"] == 0.5
    assert resultado["cobertura"] == 0.5
    assert resultado["f1"] == 0.5


# ============================================================
# 10. LIMITACIÓN: ERRORES FACTUALES
# ============================================================

def test_f1_alto_con_dato_factual_incorrecto():
    """Demuestra que F1 puede ser alto pese a un dato incorrecto.

    Compara dos oraciones casi idénticas que contienen
    años diferentes.

    Verifica que la métrica reconozca las coincidencias
    de palabras, pero no detecte por sí misma que
    el año indicado en la respuesta es incorrecto.

    Esta prueba evidencia que un resultado F1 elevado
    no garantiza exactitud factual.
    """

    # Definimos una referencia con el año correcto
    # y una respuesta con un año diferente.
    referencia = "Python fue creado en 1991."
    respuesta = "Python fue creado en 1989."

    # Aplicamos el pipeline de limpieza y tokenización
    # para preparar ambos textos antes de compararlos.
    tokens_referencia = procesar_texto(referencia)
    tokens_respuesta = procesar_texto(respuesta)

    # Calculamos las métricas utilizando la función
    # implementada durante el Bloque 16.
    resultado = calcular_precision_cobertura_f1(
        tokens_referencia,
        tokens_respuesta,
    )

    # Coinciden cuatro de los cinco tokens:
    # "python", "fue", "creado" y "en".
    # Los años son diferentes y no coinciden.
    assert resultado["precision"] == 0.8
    assert resultado["cobertura"] == 0.8

    # Comparamos con una tolerancia decimal para evitar
    # diferencias propias de la representación de números float.
    assert round(resultado["f1"], 2) == 0.8


# ============================================================
# 11. LIMITACIÓN: OMISIÓN DE NEGACIONES
# ============================================================

def test_f1_alto_cuando_se_omite_una_negacion():
    """Demuestra que F1 no detecta inversiones de significado.

    Compara una referencia que contiene una negación
    con una respuesta que omite dicha palabra.

    Aunque las oraciones expresan afirmaciones opuestas,
    la mayoría de sus tokens coinciden y producen
    una puntuación F1 elevada.

    Este escenario demuestra que la métrica no interpreta
    las relaciones lógicas entre las palabras.
    """

    # La referencia contiene la negación "no".
    referencia = "Python no es un lenguaje compilado."

    # La respuesta omite la negación, cambiando
    # el significado de la afirmación original.
    respuesta = "Python es un lenguaje compilado."

    # Normalizamos y tokenizamos ambos textos.
    tokens_referencia = procesar_texto(referencia)
    tokens_respuesta = procesar_texto(respuesta)

    # Calculamos las métricas basadas en coincidencias.
    resultado = calcular_precision_cobertura_f1(
        tokens_referencia,
        tokens_respuesta,
    )

    # Los cinco tokens de la respuesta están presentes
    # en la referencia: precisión del 100 %.
    assert round(resultado["precision"], 2) == 1.0

    # La referencia tiene seis tokens, pero la respuesta
    # solo contiene cinco de ellos: cobertura del 83 %.
    assert round(resultado["cobertura"], 2) == 0.83

    # F1 sigue siendo elevado pese al cambio de significado.
    assert round(resultado["f1"], 2) == 0.91


# ============================================================
# 12. INTEGRACIÓN DEL PIPELINE COMPLETO DE MÉTRICAS
# ============================================================

def test_calcular_metricas_integra_pipeline_completo():
    """Verifica la integración de limpieza, tokenización y métricas.

    Comprueba que la función calcular_metricas procese
    directamente dos textos originales, incluyendo
    diferencias de mayúsculas y puntuación.

    También verifica que los resultados sean equivalentes
    a los obtenidos al ejecutar manualmente el pipeline.

    Esta prueba confirma que la función de integración
    utiliza de forma coherente las etapas individuales
    del procesamiento y evaluación.
    """

    # Definimos dos textos originales que incluyen
    # diferencias de mayúsculas y puntuación.
    referencia = "¡PYTHON fue creado en 1991!"
    respuesta = "Python fue creado en 1989."

    # Ejecutamos la nueva función de integración.
    resultado = calcular_metricas(
        referencia,
        respuesta,
    )

    # Calculamos el resultado esperado utilizando
    # las funciones individuales del pipeline.
    tokens_referencia = procesar_texto(referencia)
    tokens_respuesta = procesar_texto(respuesta)

    resultado_esperado = calcular_precision_cobertura_f1(
        tokens_referencia,
        tokens_respuesta,
    )

    # Verificamos que la integración produzca
    # exactamente los mismos resultados.
    assert resultado == resultado_esperado

    # Coinciden cuatro de los cinco tokens.
    assert round(resultado["precision"], 2) == 0.80
    assert round(resultado["cobertura"], 2) == 0.80
    assert round(resultado["f1"], 2) == 0.80
