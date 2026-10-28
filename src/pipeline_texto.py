import re
from collections import Counter


def limpiar_texto(texto: str) -> str:
    """Normaliza un texto para facilitar su comparación.

    Convierte el contenido a minúsculas, elimina los signos
    de puntuación y reemplaza las secuencias de espacios
    en blanco por un único espacio.

    Args:
        texto: Cadena de caracteres que se desea normalizar.

    Returns:
        Texto normalizado, sin puntuación ni espacios sobrantes.

    Raises:
        TypeError: Si el argumento recibido no es una cadena.

    Nota:
        Se conservan letras acentuadas, la letra ñ y los números.
        Si el texto contiene únicamente puntuación o espacios,
        se devuelve una cadena vacía.
    """

    # Validamos el tipo antes de aplicar operaciones de texto.
    if not isinstance(texto, str):
        tipo = type(texto).__name__
        raise TypeError(f"limpiar_texto espera str, no {tipo}")

    # Convertimos el texto a minúsculas para evitar diferencias
    # artificiales durante las comparaciones.
    texto = texto.lower()

    # Eliminamos la puntuación conservando caracteres Unicode
    # de palabras, incluidos números, tildes y la letra ñ.
    texto = re.sub(r"[^\w\s]", "", texto)

    # Unificamos los espacios y eliminamos los sobrantes
    # al comienzo y al final de la cadena.
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto

def tokenizar(texto_limpio: str) -> list[str]:
    """Convierte un texto normalizado en una lista de tokens.

    Separa el texto previamente limpiado en palabras,
    utilizando los espacios como delimitadores.

    Args:
        texto_limpio: Cadena de texto previamente normalizada
            mediante la función limpiar_texto().

    Returns:
        Lista de cadenas, donde cada elemento representa
        una palabra del texto original.

        Si el texto está vacío o contiene únicamente
        espacios, devuelve una lista vacía.

    Nota:
        Esta función no realiza limpieza adicional.
        Se espera que el texto haya sido normalizado
        antes de utilizarla.
    """

    # Separamos el texto por espacios en blanco.
    # split() también evita generar tokens vacíos cuando
    # el texto contiene espacios repetidos.
    tokens = texto_limpio.split()

    # Devolvemos la lista de palabras para su posterior
    # procesamiento y comparación.
    return tokens

def procesar_texto(texto: str) -> list[str]:
    """Ejecuta el pipeline de limpieza y tokenización de texto.

    Coordina las funciones de normalización y tokenización
    para transformar un texto original en una lista de
    palabras preparadas para su análisis.

    Args:
        texto: Cadena de caracteres original que se
            desea procesar.

    Returns:
        Lista de palabras normalizadas, en minúsculas,
        sin puntuación y conservando las repeticiones.

        Si el texto está vacío o contiene únicamente
        espacios o puntuación, devuelve una lista vacía.

    Raises:
        TypeError: Si el argumento recibido no es una cadena.

    Nota:
        Esta función reutiliza limpiar_texto() y tokenizar()
        para evitar duplicar lógica de procesamiento.
    """

    # Primera etapa: normalizamos el texto original,
    # eliminando puntuación y espacios innecesarios.
    texto_limpio = limpiar_texto(texto)

    # Segunda etapa: convertimos el texto normalizado
    # en una lista de palabras individuales.
    tokens = tokenizar(texto_limpio)

    # Entregamos los tokens para su posterior análisis
    # o comparación con otros textos.
    return tokens

def vectorizar(tokens: list[str]) -> dict[str, int]:
    """Construye un vector de frecuencias a partir de tokens.

    Cuenta cuántas veces aparece cada palabra en una lista
    de tokens previamente procesados.

    Args:
        tokens: Lista de palabras obtenidas mediante
            la función procesar_texto().

    Returns:
        Diccionario donde cada clave representa una palabra
        y cada valor indica su frecuencia de aparición.

        Si la lista está vacía, devuelve un diccionario vacío.

    Nota:
        Se utiliza Counter de la biblioteca estándar de Python.
        Esta representación corresponde a un modelo sencillo
        de bolsa de palabras (Bag of Words).
    """

    # Contamos las apariciones de cada palabra.
    frecuencias = Counter(tokens)

    # Convertimos el contador en un diccionario convencional
    # para facilitar su uso en otras funciones del proyecto.
    return dict(frecuencias)

def calcular_coincidencia(
    referencia: str,
    respuesta: str,
    normalizar: bool = True,
) -> float:
    """Calcula la coincidencia de vocabulario con un texto de referencia.

    Compara las palabras únicas de la referencia con las
    palabras presentes en la respuesta.

    Args:
        referencia: Texto que contiene la respuesta esperada.
        respuesta: Texto generado que se desea evaluar.
        normalizar: Indica si ambos textos deben pasar por
            el pipeline de limpieza y tokenización.

    Returns:
        Proporción de palabras de referencia encontradas
        en la respuesta, expresada entre 0.0 y 1.0.

        Si la referencia no contiene palabras, devuelve 0.0.

    Nota:
        La métrica no considera el orden, las repeticiones
        ni el significado de las palabras. Por lo tanto,
        una coincidencia alta no garantiza una respuesta correcta.
    """

    # Seleccionamos cómo obtener los tokens de ambos textos.
    # Esto permite comparar resultados antes y después
    # de aplicar nuestro pipeline de normalización.
    if normalizar:
        tokens_referencia = procesar_texto(referencia)
        tokens_respuesta = procesar_texto(respuesta)
    else:
        # Sin normalización, conservamos las diferencias
        # de mayúsculas y puntuación.
        tokens_referencia = referencia.split()
        tokens_respuesta = respuesta.split()

    # Convertimos los tokens en conjuntos para comparar
    # palabras únicas, sin considerar sus repeticiones.
    palabras_referencia = set(tokens_referencia)
    palabras_respuesta = set(tokens_respuesta)

    # Evitamos dividir por cero cuando la referencia
    # no contiene palabras.
    if not palabras_referencia:
        return 0.0

    # Identificamos las palabras compartidas.
    palabras_coincidentes = (
        palabras_referencia & palabras_respuesta
    )

    # Calculamos la proporción de coincidencia.
    coincidencia = (
        len(palabras_coincidentes) / len(palabras_referencia)
    )

    return coincidencia

def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre dos listas de tokens.

    Compara las frecuencias de aparición de cada palabra
    en la referencia y en la respuesta generada.

    A diferencia de una comparación mediante conjuntos,
    esta función considera cuántas veces aparece cada token.

    Args:
        tokens_referencia: Lista de palabras de la respuesta
            considerada como referencia.
        tokens_respuesta: Lista de palabras de la respuesta
            que se desea evaluar.

    Returns:
        Número total de coincidencias, considerando
        las repeticiones de cada palabra.

        Si alguna lista está vacía, devuelve cero.

    Nota:
        La intersección de dos objetos Counter utiliza
        la frecuencia mínima de cada palabra compartida.
        No evalúa el significado ni el orden de los tokens.
    """

    # Contamos cuántas veces aparece cada palabra
    # en el texto de referencia.
    conteo_referencia = Counter(tokens_referencia)

    # Contamos las apariciones de cada palabra
    # en la respuesta que estamos evaluando.
    conteo_respuesta = Counter(tokens_respuesta)

    # Calculamos la intersección de frecuencias.
    # Para cada palabra compartida, Counter conserva
    # la menor cantidad de apariciones entre ambos textos.
    interseccion = conteo_referencia & conteo_respuesta

    # Sumamos todas las frecuencias compartidas
    # para obtener el número total de coincidencias.
    coincidencias = sum(interseccion.values())

    return coincidencias

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 entre dos listas de tokens.

    Utiliza las coincidencias obtenidas mediante Counter,
    considerando la frecuencia de aparición de cada palabra.

    Args:
        tokens_referencia: Lista de tokens del texto esperado.
        tokens_respuesta: Lista de tokens del texto generado.

    Returns:
        Diccionario con tres métricas:
            precision: Proporción de tokens generados coincidentes.
            cobertura: Proporción de tokens de referencia encontrados.
            f1: Media armónica de precisión y cobertura.

        Todos los valores están comprendidos entre 0.0 y 1.0.

    Nota:
        Si alguna lista está vacía, las tres métricas
        se establecen en 0.0 para evitar divisiones por cero.

        Estas métricas comparan coincidencias léxicas,
        pero no evalúan significado ni exactitud factual.
    """

    # Calculamos las coincidencias considerando las
    # repeticiones de palabras en ambos textos.
    coincidencias = contar_coincidencias(
        tokens_referencia,
        tokens_respuesta,
    )

    # Si alguna lista está vacía, no podemos calcular
    # las proporciones de manera convencional.
    if not tokens_respuesta or not tokens_referencia:
        return {
            "precision": 0.0,
            "cobertura": 0.0,
            "f1": 0.0,
        }

    # La precisión mide qué parte de la respuesta
    # generada coincide con el texto de referencia.
    precision = coincidencias / len(tokens_respuesta)

    # La cobertura mide qué parte del texto de
    # referencia aparece en la respuesta generada.
    cobertura = coincidencias / len(tokens_referencia)

    # Calculamos F1 mediante la media armónica.
    # Controlamos el caso en que ambas métricas sean cero.
    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    # Devolvemos las tres métricas para que otros
    # componentes de VyOps puedan reutilizarlas.
    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(
    texto_referencia: str,
    texto_respuesta: str,
) -> dict[str, float]:
    """Calcula métricas de evaluación a partir de dos textos.

    Integra las funciones de limpieza, tokenización
    y evaluación desarrolladas en los bloques 15 y 16.

    Args:
        texto_referencia: Respuesta considerada correcta
            o esperada para una consulta.
        texto_respuesta: Respuesta generada por el modelo
            de inteligencia artificial.

    Returns:
        Diccionario que contiene:
            precision: Proporción de tokens generados
                que coinciden con la referencia.
            cobertura: Proporción de tokens de referencia
                presentes en la respuesta.
            f1: Media armónica de precisión y cobertura.

    Nota:
        Esta función evalúa coincidencias léxicas.
        No determina si una respuesta es semánticamente
        equivalente ni si contiene información verdadera.
    """

    # Normalizamos y tokenizamos la respuesta de referencia
    # utilizando el pipeline desarrollado en el Bloque 15.
    tokens_referencia = procesar_texto(texto_referencia)

    # Aplicamos exactamente el mismo procesamiento
    # a la respuesta generada por el modelo.
    tokens_respuesta = procesar_texto(texto_respuesta)

    # Calculamos las métricas del Bloque 16
    # utilizando las listas de tokens obtenidas.
    metricas = calcular_precision_cobertura_f1(
        tokens_referencia,
        tokens_respuesta,
    )

    # Devolvemos el resultado para que pueda utilizarse
    # desde otros módulos, pruebas o scripts de VyOps.
    return metricas