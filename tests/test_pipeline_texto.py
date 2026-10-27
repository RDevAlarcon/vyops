from src.pipeline_texto import (
    limpiar_texto,
    tokenizar,
    procesar_texto,
    vectorizar,
    calcular_coincidencia,
)

def test_limpiar_texto_normaliza_mayusculas_y_puntuacion():
    """Verifica que la limpieza normalice el formato del texto.

    Comprueba que se eliminen los signos de puntuación,
    se conviertan las letras a minúsculas y se reduzcan
    los espacios repetidos a uno solo.
    """

    # Preparamos un texto con mayúsculas, puntuación
    # y espacios repetidos para comprobar la normalización.
    texto_original = "¡HOLA,   Mundo! ¿Cómo ESTÁS?"

    # Ejecutamos la función que queremos validar.
    resultado = limpiar_texto(texto_original)

    # Comprobamos que el texto conserve su contenido,
    # pero sin diferencias artificiales de formato.
    assert resultado == "hola mundo cómo estás"

def test_tokenizar_conserva_palabras_repetidas():
    """Verifica que la tokenización conserve todas las palabras.

    Comprueba que el texto limpio se convierta en una lista
    de tokens, manteniendo el orden original y las palabras
    repetidas para su posterior análisis de frecuencias.
    """

    # Preparamos un texto previamente normalizado que
    # contiene la palabra "el" en dos posiciones.
    texto_limpio = "el gato y el perro"

    # Ejecutamos la función de tokenización.
    resultado = tokenizar(texto_limpio)

    # Comprobamos que se conserven el orden y las repeticiones.
    assert resultado == ["el", "gato", "y", "el", "perro"]

def test_procesar_texto_integra_limpieza_y_tokenizacion():
    """Verifica la integración de las etapas del pipeline.

    Comprueba que procesar_texto() convierta el contenido
    a minúsculas, elimine la puntuación y devuelva una lista
    de tokens conservando las palabras repetidas.
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

def test_vectorizar_cuenta_frecuencia_de_palabras():
    """Verifica que la vectorización cuente las palabras repetidas.

    Comprueba que cada palabra aparezca como clave
    del diccionario y que su valor corresponda
    al número de veces que aparece en los tokens.
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
    """

    # Ejecutamos la vectorización sin tokens.
    resultado = vectorizar([])

    # Confirmamos que no se generen registros.
    assert resultado == {}

def test_calcular_coincidencia_sin_normalizacion():
    """Verifica la coincidencia antes de limpiar los textos.

    Comprueba que las diferencias de mayúsculas y
    puntuación afecten la comparación de palabras.
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
    """

    # Evaluamos una referencia vacía.
    resultado = calcular_coincidencia(
        "",
        "Esta es una respuesta",
    )

    # Confirmamos que se evita una división por cero.
    assert resultado == 0.0