
"""Pruebas automatizadas de la evaluación del Bloque 17.

Este módulo verifica los mecanismos utilizados por VyOps
para ejecutar y recuperar evaluaciones de respuestas.

Las pruebas cubren:

    1. Integridad del banco de 23 casos de evaluación.
    2. Recuperación de resultados almacenados en JSON.
    3. Manejo de archivos de resultados inexistentes.
    4. Rechazo de estructuras JSON incompatibles.
    5. Identificación de consultas pendientes.
    6. Reconocimiento de evaluaciones ya completadas.
    7. Guardado progresivo ante fallos del modelo.
    8. Reanudación sin repetir consultas evaluadas.
    9. Ejecución completa del Bloque 17.

Se utilizan archivos y directorios temporales para
evitar modificaciones sobre la evidencia real
de los bloques anteriores.

Las llamadas al modelo se sustituyen mediante
monkeypatch por funciones simuladas, permitiendo
comprobar el flujo sin consumir cuota de Gemini.

Las pruebas también verifican la conservación
de resultados anteriores y la ausencia de consultas
duplicadas durante la reanudación.

Las métricas evaluadas son precisión, cobertura y F1.

Este módulo comprueba el funcionamiento del proceso
de evaluación, no la calidad real de las respuestas
generadas por un modelo de lenguaje.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite serializar y recuperar los resultados
# de evaluación almacenados en formato JSON.
import json

# Banco de consultas y respuestas de referencia
# utilizado durante la evaluación del Bloque 17.
from src.casos_evaluacion_bloque_17 import (
    CASOS_EVALUACION_BLOQUE_17,
)

# Funciones responsables de recuperar resultados
# anteriores e identificar consultas pendientes.
from src.evaluacion_bloque_17 import (
    cargar_resultados_anteriores,
    obtener_casos_pendientes,
)


# ============================================================
# 2. INTEGRIDAD DEL BANCO DE EVALUACIÓN
# ============================================================

def test_banco_contiene_23_casos() -> None:
    """Verifica que el banco tenga 23 consultas válidas.

    Comprueba que el conjunto de evaluación contenga
    exactamente 23 casos.

    Cada caso debe incluir:

        - Una consulta con contenido no vacío.
        - Una respuesta de referencia no vacía.

    También se verifica que las consultas sean únicas.

    Esta prueba protege la estructura mínima del banco
    utilizado durante la evaluación del Bloque 17.
    """

    # Comprueba la cantidad total de casos configurados.
    assert len(CASOS_EVALUACION_BLOQUE_17) == 23

    # Verifica que cada caso tenga una consulta
    # y una referencia con contenido significativo.
    for caso in CASOS_EVALUACION_BLOQUE_17:
        assert caso["consulta"].strip()
        assert caso["referencia"].strip()

    # Extrae las consultas para detectar duplicados.
    consultas = [
        caso["consulta"]
        for caso in CASOS_EVALUACION_BLOQUE_17
    ]

    # La cantidad de consultas debe coincidir
    # con la cantidad de valores únicos.
    assert len(consultas) == len(set(consultas))


# ============================================================
# 3. RECUPERACIÓN DE RESULTADOS DESDE JSON
# ============================================================

def test_cargar_resultados_desde_json(tmp_path) -> None:
    """Comprueba la recuperación de resultados guardados.

    Crea un archivo JSON temporal con un resultado
    de evaluación que incluye:

        - Consulta.
        - Respuesta generada.
        - Precisión.
        - Cobertura.
        - F1.

    Verificación:
        - Los resultados recuperados coinciden
          exactamente con los datos originales.

    Args:
        tmp_path:
            Fixture de pytest que proporciona
            un directorio temporal para la prueba.
    """

    # Crea una ruta temporal para evitar modificaciones
    # sobre los archivos reales de evaluación.
    ruta = tmp_path / "resultados.json"

    # Define un resultado simulado con sus métricas.
    resultados_esperados = [
        {
            "consulta": "¿Qué es Python?",
            "respuesta": "Python es un lenguaje de programación.",
            "precision": 0.8,
            "cobertura": 1.0,
            "f1": 0.89,
        }
    ]

    # Serializa los resultados utilizando UTF-8
    # y conservando los caracteres Unicode.
    ruta.write_text(
        json.dumps(resultados_esperados, ensure_ascii=False),
        encoding="utf-8",
    )

    # Recupera los resultados mediante la función evaluada.
    resultados = cargar_resultados_anteriores(ruta)

    # Comprueba que la recuperación preserve
    # los datos originales.
    assert resultados == resultados_esperados


# ============================================================
# 4. MANEJO DE ARCHIVOS INEXISTENTES
# ============================================================

def test_archivo_inexistente_devuelve_lista_vacia(tmp_path) -> None:
    """Verifica que un archivo inexistente no genere errores.

    Construye una ruta temporal que no contiene
    un archivo de resultados.

    Verificación:
        - cargar_resultados_anteriores() devuelve [].

    Este comportamiento permite comenzar una evaluación
    cuando todavía no existen resultados persistidos.

    Args:
        tmp_path:
            Directorio temporal proporcionado por pytest.
    """

    # Define una ruta que no contiene resultados previos.
    ruta = tmp_path / "archivo_inexistente.json"

    # La ausencia del archivo debe representarse
    # mediante una lista vacía.
    assert cargar_resultados_anteriores(ruta) == []


# ============================================================
# 5. VALIDACIÓN DE LA ESTRUCTURA JSON
# ============================================================

def test_json_con_estructura_incorrecta(tmp_path) -> None:
    """Comprueba el rechazo de un JSON que no contiene una lista.

    Crea un archivo JSON válido sintácticamente,
    pero con una estructura de objeto en lugar
    de una lista de resultados.

    Verificación:
        - cargar_resultados_anteriores() genera ValueError.

    Esta prueba comprueba la validación de la estructura
    esperada para los resultados de evaluación.

    Args:
        tmp_path:
            Directorio temporal utilizado para crear
            el archivo JSON incompatible.
    """

    # Importa pytest para comprobar la excepción esperada.
    import pytest

    # Define la ubicación del archivo de prueba.
    ruta = tmp_path / "resultados_invalidos.json"

    # Guarda un objeto JSON en lugar de una lista.
    ruta.write_text(
        '{"consulta": "Python"}',
        encoding="utf-8",
    )

    # La función debe rechazar estructuras incompatibles.
    with pytest.raises(ValueError):
        cargar_resultados_anteriores(ruta)


# ============================================================
# 6. IDENTIFICACIÓN DE CONSULTAS PENDIENTES
# ============================================================

def test_identificar_casos_pendientes() -> None:
    """Comprueba que se excluyan las consultas ya evaluadas.

    Define tres casos de evaluación y un resultado
    correspondiente únicamente a la primera consulta.

    Verificaciones:
        - Quedan dos casos pendientes.
        - Los pendientes son Pregunta B y Pregunta C.
        - Se conserva el orden de los casos pendientes.
        - La lista de casos originales no se modifica.
        - La lista de resultados anteriores no se modifica.

    Esta prueba comprueba que la identificación
    de pendientes no altere los datos de entrada.
    """

    # Define tres consultas disponibles para evaluación.
    casos = [
        {"consulta": "Pregunta A", "referencia": "Respuesta A"},
        {"consulta": "Pregunta B", "referencia": "Respuesta B"},
        {"consulta": "Pregunta C", "referencia": "Respuesta C"},
    ]

    # Simula que la primera consulta
    # ya fue evaluada anteriormente.
    anteriores = [
        {
            "consulta": "Pregunta A",
            "respuesta": "Respuesta generada A",
            "precision": 1.0,
            "cobertura": 1.0,
            "f1": 1.0,
        }
    ]

    # Conserva copias superficiales de los registros
    # para verificar que las entradas permanezcan intactas.
    casos_originales = [caso.copy() for caso in casos]
    anteriores_originales = [
        resultado.copy() for resultado in anteriores
    ]

    # Identifica las consultas que todavía
    # no cuentan con resultados anteriores.
    pendientes = obtener_casos_pendientes(casos, anteriores)

    # Deben quedar exactamente dos consultas pendientes.
    assert len(pendientes) == 2

    # Comprueba cuáles son las consultas pendientes
    # y verifica que se conserve su orden.
    assert [caso["consulta"] for caso in pendientes] == [
        "Pregunta B",
        "Pregunta C",
    ]

    # Verifica que ambas listas originales permanezcan intactas.
    assert casos == casos_originales
    assert anteriores == anteriores_originales


# ============================================================
# 7. EVALUACIÓN SIN CASOS PENDIENTES
# ============================================================

def test_todos_los_casos_evaluados() -> None:
    """Comprueba que no haya pendientes cuando todos están evaluados.

    Define una consulta y un resultado anterior
    correspondiente a esa misma consulta.

    Verificación:
        - obtener_casos_pendientes() devuelve [].

    Este escenario comprueba que una evaluación
    completada no genere consultas pendientes.
    """

    # Define un único caso de evaluación.
    casos = [
        {"consulta": "Pregunta A", "referencia": "Respuesta A"},
    ]

    # Simula que el caso ya cuenta
    # con un resultado persistido.
    anteriores = [
        {
            "consulta": "Pregunta A",
            "respuesta": "Respuesta generada A",
            "precision": 1.0,
            "cobertura": 1.0,
            "f1": 1.0,
        }
    ]

    # No deben quedar consultas por evaluar.
    assert obtener_casos_pendientes(casos, anteriores) == []


# ============================================================
# 8. GUARDADO PROGRESIVO ANTE FALLOS
# ============================================================

def test_guardado_progresivo_ante_fallo(
    tmp_path,
    monkeypatch,
) -> None:
    """Verifica que una respuesta se conserve si Gemini falla.

    Simula dos consultas consecutivas:

        Primera consulta:
            El modelo devuelve una respuesta válida.

        Segunda consulta:
            El modelo genera RuntimeError.

    Verificaciones:
        - El error interrumpe la evaluación.
        - El primer resultado permanece guardado en JSON.
        - Se conserva su consulta y referencia.
        - El resultado incluye precisión, cobertura y F1.

    Se utiliza monkeypatch para sustituir temporalmente
    la función de consulta al modelo.

    Args:
        tmp_path:
            Directorio temporal donde se almacenan
            los resultados simulados.

        monkeypatch:
            Fixture de pytest que permite sustituir
            temporalmente dependencias del módulo.
    """

    # Importa las dependencias necesarias
    # para simular el error del modelo.
    import pytest
    import src.evaluacion_bloque_17 as modulo

    # Define dos casos independientes de evaluación.
    casos = [
        {
            "consulta": "¿Cuál es la capital de Chile?",
            "referencia": "La capital de Chile es Santiago.",
        },
        {
            "consulta": "¿Cuánto es 2 más 2?",
            "referencia": "2 más 2 es 4.",
        },
    ]

    # Simula el comportamiento del modelo:
    # la primera consulta responde y la segunda falla.
    def consultar_modelo_simulado(consulta: str) -> str:
        """Devuelve la primera respuesta o simula un fallo.

        Args:
            consulta (str):
                Consulta que recibe el modelo simulado.

        Returns:
            str:
                Respuesta simulada para la primera consulta.

        Raises:
            RuntimeError:
                Cuando se recibe una consulta distinta
                de la primera del conjunto de prueba.
        """

        if consulta == casos[0]["consulta"]:
            return "La capital de Chile es Santiago."

        raise RuntimeError("Fallo simulado de Gemini.")

    # Sustituye temporalmente el cliente real.
    # Así se evita consumir cuota de Gemini.
    monkeypatch.setattr(
        modulo,
        "consultar_modelo",
        consultar_modelo_simulado,
    )

    # Define un archivo temporal para los resultados
    # generados durante la evaluación.
    ruta = tmp_path / "resultados_bloque_17.json"

    # Comprueba que el fallo de la segunda consulta
    # produzca la excepción esperada.
    with pytest.raises(RuntimeError, match="Fallo simulado"):
        modulo.evaluar_casos_pendientes(
            casos_pendientes=casos,
            ruta_archivo=ruta,
            resultados_existentes=[],
        )

    # Recupera el archivo generado antes del fallo.
    resultados = cargar_resultados_anteriores(ruta)

    # La primera respuesta debe haberse conservado.
    assert len(resultados) == 1
    assert resultados[0]["consulta"] == casos[0]["consulta"]
    assert resultados[0]["referencia"] == casos[0]["referencia"]

    # También deben existir las tres métricas.
    assert "precision" in resultados[0]
    assert "cobertura" in resultados[0]
    assert "f1" in resultados[0]


# ============================================================
# 9. REANUDACIÓN SIN DUPLICADOS
# ============================================================

def test_reanudar_evaluacion_sin_duplicados(
    tmp_path,
    monkeypatch,
) -> None:
    """Verifica que una evaluación pueda reanudarse sin duplicados.

    Simula una evaluación con dos consultas,
    donde la primera ya tiene un resultado guardado.

    Al reanudar, se proporcionan deliberadamente
    ambos casos para verificar que la función
    omita la consulta ya evaluada.

    Verificaciones:
        - Solo se consulta al modelo por el caso pendiente.
        - El archivo final contiene dos resultados.
        - No existen consultas duplicadas.
        - El resultado anterior se conserva intacto.

    Args:
        tmp_path:
            Directorio temporal para almacenar
            los resultados de evaluación.

        monkeypatch:
            Fixture utilizada para sustituir
            la consulta real al modelo.
    """

    # Importa el módulo responsable de la evaluación.
    import src.evaluacion_bloque_17 as modulo

    # Define dos casos disponibles para evaluar.
    casos = [
        {
            "consulta": "¿Cuál es la capital de Chile?",
            "referencia": "La capital de Chile es Santiago.",
        },
        {
            "consulta": "¿Cuánto es 2 más 2?",
            "referencia": "2 más 2 es 4.",
        },
    ]

    # Simula un resultado persistido previamente.
    resultados_anteriores = [
        {
            "consulta": casos[0]["consulta"],
            "referencia": casos[0]["referencia"],
            "respuesta": "La capital de Chile es Santiago.",
            "precision": 1.0,
            "cobertura": 1.0,
            "f1": 1.0,
        }
    ]

    # Registra las consultas recibidas por el modelo
    # para comprobar cuáles se ejecutaron realmente.
    consultas_realizadas: list[str] = []

    def consultar_modelo_simulado(consulta: str) -> str:
        """Simula Gemini y registra cada consulta recibida.

        Args:
            consulta (str):
                Texto de la consulta enviada al modelo.

        Returns:
            str:
                Respuesta simulada para el caso pendiente.
        """

        # Registra la consulta para detectar repeticiones.
        consultas_realizadas.append(consulta)

        # Devuelve una respuesta simulada.
        return "2 más 2 es 4."

    # Sustituye temporalmente la función de consulta real.
    monkeypatch.setattr(
        modulo,
        "consultar_modelo",
        consultar_modelo_simulado,
    )

    # Define la ubicación temporal del archivo.
    ruta = tmp_path / "resultados_bloque_17.json"

    # Simula el archivo existente antes de reanudar.
    ruta.write_text(
        json.dumps(resultados_anteriores, ensure_ascii=False),
        encoding="utf-8",
    )

    # Reanuda incluyendo deliberadamente ambos casos.
    # La función debe omitir el caso ya registrado.
    modulo.evaluar_casos_pendientes(
        casos_pendientes=casos,
        ruta_archivo=ruta,
        resultados_existentes=resultados_anteriores,
    )

    # El modelo debe recibir únicamente la consulta pendiente.
    assert consultas_realizadas == [casos[1]["consulta"]]

    # Recupera los resultados persistidos.
    resultados = cargar_resultados_anteriores(ruta)

    # Deben existir exactamente dos resultados.
    assert len(resultados) == 2

    # Extrae las consultas almacenadas
    # para comprobar que no existan duplicados.
    consultas_guardadas = [
        resultado["consulta"]
        for resultado in resultados
    ]

    # Cada consulta debe aparecer una sola vez.
    assert len(consultas_guardadas) == len(set(consultas_guardadas))

    # La evaluación anterior debe conservarse intacta.
    assert resultados[0] == resultados_anteriores[0]


# ============================================================
# 10. EJECUCIÓN COMPLETA DEL BLOQUE 17
# ============================================================

def test_ejecucion_completa_bloque_17(
    tmp_path,
    monkeypatch,
) -> None:
    """Verifica el flujo completo del Bloque 17 sin usar Gemini.

    Simula la existencia de tres resultados anteriores
    correspondientes al Bloque 16.

    Posteriormente ejecuta el proceso del Bloque 17
    para completar las veinte consultas restantes.

    Verificaciones:
        - El archivo final contiene 23 resultados.
        - Solo se realizan veinte consultas nuevas.
        - No existen consultas repetidas al modelo.
        - Los tres resultados originales se conservan.
        - El archivo del Bloque 16 no se modifica.
        - Los resultados nuevos incluyen referencia
          y las tres métricas de evaluación.
        - Una segunda ejecución no genera nuevas consultas.

    La prueba utiliza un directorio temporal
    y una función simulada para sustituir Gemini.

    Args:
        tmp_path:
            Directorio temporal donde se crean
            los archivos de resultados.

        monkeypatch:
            Fixture utilizada para cambiar temporalmente
            el directorio de trabajo y sustituir Gemini.
    """

    # Importa los módulos responsables
    # de ejecutar y evaluar el Bloque 17.
    import ejecutar_bloque_17 as modulo_ejecucion
    import src.evaluacion_bloque_17 as modulo_evaluacion

    # Cambia temporalmente el directorio de trabajo
    # para aislar los archivos utilizados por la prueba.
    monkeypatch.chdir(tmp_path)

    # Crea el directorio de resultados simulado.
    directorio = tmp_path / "resultados"
    directorio.mkdir()

    # Define las rutas del archivo original
    # y del nuevo archivo del Bloque 17.
    ruta_original = directorio / "resultados_metricas.json"
    ruta_nueva = directorio / "resultados_bloque_17.json"

    # Construye tres resultados anteriores utilizando
    # los primeros casos del banco de evaluación.
    resultados_originales = [
        {
            "consulta": caso["consulta"],
            "respuesta": caso["referencia"],
            "precision": 1.0,
            "cobertura": 1.0,
            "f1": 1.0,
        }
        for caso in CASOS_EVALUACION_BLOQUE_17[:3]
    ]

    # Serializa los resultados anteriores
    # conservando los caracteres Unicode.
    contenido_original = json.dumps(
        resultados_originales,
        ensure_ascii=False,
        indent=2,
    )

    # Guarda el archivo que representa
    # los resultados originales del Bloque 16.
    ruta_original.write_text(
        contenido_original,
        encoding="utf-8",
    )

    # Registra las consultas enviadas al modelo
    # para detectar ejecuciones repetidas.
    consultas_realizadas: list[str] = []

    def consultar_modelo_simulado(consulta: str) -> str:
        """Devuelve una respuesta simulada sin llamar a Gemini.

        Args:
            consulta (str):
                Consulta recibida por la función simulada.

        Returns:
            str:
                Respuesta fija utilizada durante la evaluación.

        También registra cada consulta recibida
        para comprobar la cantidad de ejecuciones.
        """

        # Conserva la consulta para comprobar
        # que no existan repeticiones.
        consultas_realizadas.append(consulta)

        # Devuelve una respuesta fija de prueba.
        return "Respuesta simulada para evaluación."

    # Sustituye temporalmente la función real
    # de consulta al modelo.
    monkeypatch.setattr(
        modulo_evaluacion,
        "consultar_modelo",
        consultar_modelo_simulado,
    )

    # Ejecuta el flujo completo del Bloque 17
    # utilizando los archivos temporales.
    modulo_ejecucion.ejecutar_bloque_17()

    # Recupera los resultados generados.
    resultados = cargar_resultados_anteriores(ruta_nueva)

    # El conjunto final debe contener los 23 casos.
    assert len(resultados) == 23

    # Solo deben realizarse las veinte consultas nuevas.
    assert len(consultas_realizadas) == 20

    # Ninguna consulta debe repetirse.
    assert len(consultas_realizadas) == len(
        set(consultas_realizadas)
    )

    # Los tres resultados originales deben conservarse.
    assert resultados[:3] == resultados_originales

    # El archivo original no debe modificarse.
    assert ruta_original.read_text(
        encoding="utf-8"
    ) == contenido_original

    # Todos los resultados nuevos deben incluir referencia.
    for resultado in resultados[3:]:
        assert "referencia" in resultado
        assert "precision" in resultado
        assert "cobertura" in resultado
        assert "f1" in resultado

    # Una segunda ejecución no debe llamar nuevamente a Gemini.
    modulo_ejecucion.ejecutar_bloque_17()

    # La cantidad de consultas debe permanecer inalterada
    # y el archivo final debe conservar los 23 resultados.
    assert len(consultas_realizadas) == 20
    assert len(cargar_resultados_anteriores(ruta_nueva)) == 23
