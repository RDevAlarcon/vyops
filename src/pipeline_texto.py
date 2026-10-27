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