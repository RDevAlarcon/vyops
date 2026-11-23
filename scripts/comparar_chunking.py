
"""Compara estrategias de división de texto para RAG.

Script de experimentación con estrategias de chunking
utilizadas en sistemas de generación aumentada
por recuperación (Retrieval-Augmented Generation).

Su objetivo es comparar cómo dos divisores
de LangChain fragmentan un mismo texto
utilizando configuraciones equivalentes.

Estrategias implementadas:

    1. CharacterTextSplitter:
        Divide el contenido utilizando un separador
        de caracteres vacío.

    2. RecursiveCharacterTextSplitter:
        Intenta dividir el contenido respetando
        separadores naturales, cuando es posible.

Configuración compartida:

    chunk_size:
        100 caracteres.

    chunk_overlap:
        20 caracteres.

Texto de prueba:

    Se utiliza un ejemplo de SkillNest
    que describe:

        - Reintentos ante TimeoutError.
        - Errores de autenticación sin reintentos.
        - Acumulación de costos por sesión.

Responsabilidades principales:

    - Proporcionar un texto de prueba reproducible.
    - Aplicar chunking por caracteres.
    - Aplicar chunking recursivo.
    - Mostrar la cantidad de fragmentos generados.
    - Mostrar el tamaño de cada fragmento.
    - Presentar los fragmentos para su comparación.

Consideraciones:

    La configuración de chunk_size establece
    el tamaño objetivo de los fragmentos.

    chunk_overlap configura el solapamiento
    que el divisor intentará mantener
    entre fragmentos consecutivos.

    El comportamiento exacto depende
    del algoritmo y de los separadores disponibles.

IMPORTANTE:
    Este script no genera embeddings.

    Tampoco consulta una base vectorial,
    ejecuta búsquedas semánticas ni utiliza
    un modelo de lenguaje.

    Su responsabilidad se limita
    a comparar la fragmentación del texto.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Divisores de texto proporcionados por LangChain.
#
# CharacterTextSplitter:
#     Fragmenta el texto utilizando un separador
#     definido explícitamente.
#
# RecursiveCharacterTextSplitter:
#     Utiliza una estrategia recursiva para intentar
#     conservar agrupaciones naturales del contenido.
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)


# ============================================================
# 2. TEXTO DE PRUEBA
# ============================================================

def obtener_texto_prueba() -> str:
    """Devuelve el texto de ejemplo utilizado en SkillNest.

    Returns:
        str:
            Texto de prueba compuesto por tres párrafos.

    Contenido:

        Primer párrafo:
            Describe el comportamiento de reintentos
            ante errores TimeoutError.

        Segundo párrafo:
            Explica que los errores de autenticación
            no deben generar reintentos.

        Tercer párrafo:
            Describe la acumulación de costos
            durante una sesión.

    Los párrafos están separados
    mediante dos saltos de línea.

    Esta estructura permite observar
    si los divisores respetan los límites
    naturales del contenido.

    El texto se mantiene fijo para que
    ambas estrategias reciban exactamente
    la misma entrada.
    """

    # Devuelve el documento utilizado
    # para comparar ambas estrategias.
    #
    # La concatenación de cadenas entre paréntesis
    # permite organizar el texto en varias líneas
    # sin modificar su contenido final.
    return (
        "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente "
        "entre intento e intento.\n\n"
        "Los errores de autenticación nunca se reintentan: fallan de inmediato con un "
        "ValueError, sin ninguna espera.\n\n"
        "El costo de cada llamada se acumula en una variable de sesión mientras el "
        "programa sigue corriendo."
    )


# ============================================================
# 3. CHUNKING RECURSIVO
# ============================================================

def dividir_recursivamente(texto: str) -> list[str]:
    """Divide el texto respetando límites naturales cuando sea posible.

    Args:
        texto:
            Contenido que se desea fragmentar.

    Returns:
        list[str]:
            Lista de fragmentos producidos
            por RecursiveCharacterTextSplitter.

    Configuración:

        chunk_size=100:
            Establece un tamaño objetivo
            de 100 caracteres por fragmento.

        chunk_overlap=20:
            Configura un solapamiento objetivo
            de 20 caracteres entre fragmentos.

    Estrategia:

        El divisor recursivo intenta utilizar
        separadores naturales del texto.

        Esto puede favorecer la conservación
        de párrafos, frases o palabras
        dentro de un mismo fragmento.

    El resultado depende de la estructura
    y longitud del texto recibido.

    Esta función no modifica
    el contenido original.
    """

    # --------------------------------------------------------
    # 3.1. CONFIGURACIÓN DEL DIVISOR
    # --------------------------------------------------------

    # Crea un divisor recursivo.
    #
    # Se utiliza el conjunto predeterminado
    # de separadores de la biblioteca.
    #
    # El tamaño y el solapamiento coinciden
    # con los utilizados en la otra estrategia.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
    )

    # --------------------------------------------------------
    # 3.2. FRAGMENTACIÓN DEL TEXTO
    # --------------------------------------------------------

    # Divide el contenido y devuelve
    # la lista de fragmentos resultantes.
    return splitter.split_text(texto)


# ============================================================
# 4. EJECUCIÓN DE LA COMPARACIÓN
# ============================================================

def main() -> None:
    """Prepara el texto para comparar ambas estrategias.

    Ejecuta la comparación de chunking
    utilizando el texto de prueba de SkillNest.

    Flujo:
        1. Obtener el texto original.
        2. Mostrar su cantidad de caracteres.
        3. Aplicar chunking por caracteres.
        4. Mostrar los fragmentos obtenidos.
        5. Aplicar chunking recursivo.
        6. Mostrar los fragmentos obtenidos.

    Returns:
        None:
            La función muestra los resultados
            en la consola y no devuelve valores.

    Información presentada:

        - Longitud del texto original.
        - Cantidad de chunks por estrategia.
        - Número de cada fragmento.
        - Cantidad de caracteres por fragmento.
        - Representación textual de cada fragmento.

    Se utiliza repr() para visualizar
    explícitamente caracteres especiales,
    como los saltos de línea.

    La función no guarda resultados
    en archivos ni bases de datos.
    """

    # --------------------------------------------------------
    # 4.1. PREPARACIÓN DEL DOCUMENTO
    # --------------------------------------------------------

    # Obtiene el texto de prueba compartido
    # por ambas estrategias.
    texto = obtener_texto_prueba()

    # Muestra el encabezado de comparación.
    print("Comparación de estrategias de chunking")

    # Informa la longitud del documento original.
    print(f"Caracteres del texto original: {len(texto)}")

    # ========================================================
    # 5. COMPARACIÓN POR CARACTERES
    # ========================================================

    # --------------------------------------------------------
    # 5.1. EJECUCIÓN DEL DIVISOR
    # --------------------------------------------------------

    # Aplica la estrategia CharacterTextSplitter
    # definida en dividir_por_caracteres().
    fragmentos = dividir_por_caracteres(texto)

    # --------------------------------------------------------
    # 5.2. RESUMEN DE RESULTADOS
    # --------------------------------------------------------

    # Identifica la estrategia utilizada.
    print("\n--- Chunking por caracteres ---")

    # Muestra la cantidad total de fragmentos.
    print(f"Cantidad de chunks: {len(fragmentos)}")

    # --------------------------------------------------------
    # 5.3. PRESENTACIÓN DE FRAGMENTOS
    # --------------------------------------------------------

    # Recorre los fragmentos generados.
    #
    # start=1 permite numerarlos desde uno.
    for indice, fragmento in enumerate(fragmentos, start=1):

        # Muestra el número y tamaño del fragmento.
        print(f"\nChunk {indice} ({len(fragmento)} caracteres):")

        # repr() permite observar el contenido
        # y los caracteres especiales del fragmento.
        print(repr(fragmento))

    # ========================================================
    # 6. COMPARACIÓN RECURSIVA
    # ========================================================

    # --------------------------------------------------------
    # 6.1. EJECUCIÓN DEL DIVISOR
    # --------------------------------------------------------

    # Aplica RecursiveCharacterTextSplitter
    # sobre el mismo texto original.
    fragmentos_recursivos = dividir_recursivamente(texto)

    # --------------------------------------------------------
    # 6.2. RESUMEN DE RESULTADOS
    # --------------------------------------------------------

    # Identifica la estrategia recursiva.
    print("\n--- Chunking recursivo ---")

    # Muestra la cantidad de fragmentos obtenidos.
    print(f"Cantidad de chunks: {len(fragmentos_recursivos)}")

    # --------------------------------------------------------
    # 6.3. PRESENTACIÓN DE FRAGMENTOS
    # --------------------------------------------------------

    # Recorre los fragmentos de la segunda estrategia.
    for indice, fragmento in enumerate(fragmentos_recursivos, start=1):

        # Muestra el número y tamaño del fragmento.
        print(f"\nChunk {indice} ({len(fragmento)} caracteres):")

        # Presenta el contenido mediante repr()
        # para facilitar la comparación visual.
        print(repr(fragmento))


# ============================================================
# 7. CHUNKING POR CARACTERES
# ============================================================

def dividir_por_caracteres(texto: str) -> list[str]:
    """Divide el texto en fragmentos de tamaño fijo.

    Args:
        texto:
            Contenido que se desea fragmentar.

    Returns:
        list[str]:
            Lista de fragmentos generados
            por CharacterTextSplitter.

    Configuración:

        separator="":
            Utiliza un separador vacío
            para dividir el contenido
            a nivel de caracteres.

        chunk_size=100:
            Configura fragmentos con
            un tamaño objetivo de 100 caracteres.

        chunk_overlap=20:
            Configura un solapamiento objetivo
            de 20 caracteres entre fragmentos.

    Estrategia:

        A diferencia del divisor recursivo,
        esta configuración no prioriza
        los límites naturales de párrafos.

        Por ello, puede producir cortes
        dentro de palabras o frases.

    Esta función permite establecer
    una referencia de comparación
    frente al chunking recursivo.
    """

    # --------------------------------------------------------
    # 7.1. CONFIGURACIÓN DEL DIVISOR
    # --------------------------------------------------------

    # Crea un divisor basado en caracteres.
    #
    # separator="" permite dividir
    # utilizando caracteres individuales.
    splitter = CharacterTextSplitter(
        separator="",
        chunk_size=100,
        chunk_overlap=20,
    )

    # --------------------------------------------------------
    # 7.2. FRAGMENTACIÓN DEL TEXTO
    # --------------------------------------------------------

    # Aplica el divisor configurado
    # y devuelve los fragmentos resultantes.
    return splitter.split_text(texto)


# ============================================================
# 8. PUNTO DE ENTRADA DEL SCRIPT
# ============================================================

# Ejecuta main() cuando el archivo
# se inicia directamente como programa.
#
# Aunque dividir_por_caracteres() está definido
# después de main(), Python habrá procesado
# ambas definiciones antes de ejecutar esta llamada.
#
# Si el módulo se importa desde otro archivo,
# la comparación no se ejecuta automáticamente.
if __name__ == "__main__":
    main()
