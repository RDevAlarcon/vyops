"""Pruebas automatizadas de la evaluación del Bloque 16.

Verifica la integración entre el cliente Gemini y el
pipeline de métricas sin realizar solicitudes reales
a servicios externos.
"""

import evaluar_respuestas

from src.pipeline_texto import calcular_metricas


def test_evaluar_casos_bloque_16_sin_llamadas_reales(monkeypatch):
    """Comprueba la evaluación de varios casos con Gemini simulado.

    Verifica que:
    - Cada consulta se envíe exactamente una vez.
    - Las respuestas simuladas se conserven correctamente.
    - Las métricas coincidan con el pipeline de evaluación.
    - El resultado contenga todas las claves esperadas.
    """

    # Definimos dos casos de prueba independientes.
    casos = [
        {
            "consulta": "¿Qué es Python?",
            "referencia": "Python es un lenguaje de programación.",
        },
        {
            "consulta": "¿Cuándo se creó Python?",
            "referencia": "Python fue creado en 1991.",
        },
    ]

    # Preparamos respuestas simuladas para cada pregunta.
    respuestas_simuladas = {
        "¿Qué es Python?": "Python es un lenguaje de programación.",
        "¿Cuándo se creó Python?": "Python fue creado en 1989.",
    }

    # Registraremos las consultas recibidas para comprobar
    # que el cliente se invoque exactamente una vez por caso.
    consultas_recibidas: list[str] = []

    def consultar_modelo_simulado(pregunta: str) -> str:
        """Devuelve una respuesta simulada sin utilizar Gemini."""

        # Registramos cada invocación del cliente.
        consultas_recibidas.append(pregunta)

        # Devolvemos la respuesta correspondiente a la pregunta.
        return respuestas_simuladas[pregunta]

    # Sustituimos temporalmente el cliente real por el simulado.
    # El cambio solo tiene efecto durante esta prueba.
    monkeypatch.setattr(
        evaluar_respuestas,
        "consultar_modelo",
        consultar_modelo_simulado,
    )

    # Ejecutamos la evaluación completa.
    resultados = evaluar_respuestas.evaluar_casos_bloque_16(casos)

    # Debe existir un resultado por cada caso.
    assert len(resultados) == 2

    # Cada pregunta debe haberse consultado exactamente una vez.
    assert consultas_recibidas == [
        "¿Qué es Python?",
        "¿Cuándo se creó Python?",
    ]

    # Verificamos el contenido de cada resultado.
    for caso, resultado in zip(casos, resultados):

        # Recuperamos la respuesta simulada esperada.
        respuesta_esperada = respuestas_simuladas[caso["consulta"]]

        # Calculamos las métricas esperadas de manera independiente.
        metricas_esperadas = calcular_metricas(
            caso["referencia"],
            respuesta_esperada,
        )

        # Comprobamos la estructura y los valores obtenidos.
        assert resultado == {
            "consulta": caso["consulta"],
            "respuesta": respuesta_esperada,
            "precision": metricas_esperadas["precision"],
            "cobertura": metricas_esperadas["cobertura"],
            "f1": metricas_esperadas["f1"],
        }

def test_guardar_resultados_metricas_en_json(tmp_path):
    """Verifica el almacenamiento y recuperación de métricas en JSON.

    Comprueba que la función:
    - Cree automáticamente los directorios necesarios.
    - Genere un archivo JSON válido.
    - Conserve las tildes y los caracteres especiales.
    - Mantenga los valores originales de las métricas.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest
            para ejecutar la prueba sin modificar archivos reales.
    """

    # Definimos resultados simulados para evitar
    # cualquier consulta real al modelo Gemini.
    resultados = [
        {
            "consulta": "¿Qué es Python?",
            "respuesta": "Python es un lenguaje de programación.",
            "precision": 0.8,
            "cobertura": 0.9,
            "f1": 0.847,
        },
        {
            "consulta": "¿Qué es una lista?",
            "respuesta": "Una lista es una colección ordenada.",
            "precision": 0.75,
            "cobertura": 0.85,
            "f1": 0.797,
        },
    ]

    # Construimos una ruta dentro del directorio temporal.
    # La carpeta "resultados" todavía no existe.
    ruta_archivo = (
        tmp_path / "resultados" / "resultados_metricas.json"
    )

    # Ejecutamos la función de guardado.
    evaluar_respuestas.guardar_resultados_metricas(
        resultados,
        ruta_archivo,
    )

    # Comprobamos que el archivo se haya creado.
    assert ruta_archivo.is_file()

    # Leemos el contenido original utilizando UTF-8.
    contenido = ruta_archivo.read_text(encoding="utf-8")

    # Verificamos que las tildes se conserven
    # directamente y no como secuencias Unicode escapadas.
    assert "programación" in contenido
    assert "colección" in contenido
    assert "¿Qué es Python?" in contenido

    # Importamos json para recuperar los datos almacenados.
    import json

    # Convertimos el contenido JSON a objetos de Python.
    datos_recuperados = json.loads(contenido)

    # Verificamos que todos los datos originales
    # se hayan conservado correctamente.
    assert datos_recuperados == resultados

def test_resumir_metricas_calcula_promedios():
    """Verifica el cálculo de promedios de evaluación.

    Comprueba que la función calcule correctamente
    la media aritmética de precisión, cobertura y F1
    utilizando varios resultados simulados.

    No realiza llamadas reales a Gemini.
    """

    # Definimos tres evaluaciones con métricas conocidas.
    resultados = [
        {
            "consulta": "Pregunta 1",
            "respuesta": "Respuesta 1",
            "precision": 0.6,
            "cobertura": 0.8,
            "f1": 0.7,
        },
        {
            "consulta": "Pregunta 2",
            "respuesta": "Respuesta 2",
            "precision": 0.8,
            "cobertura": 0.6,
            "f1": 0.7,
        },
        {
            "consulta": "Pregunta 3",
            "respuesta": "Respuesta 3",
            "precision": 1.0,
            "cobertura": 1.0,
            "f1": 1.0,
        },
    ]

    # Calculamos los promedios utilizando la nueva función.
    resumen = evaluar_respuestas.resumir_metricas(resultados)

    # Verificamos los promedios esperados:
    # Precisión: (0.6 + 0.8 + 1.0) / 3 = 0.8
    # Cobertura: (0.8 + 0.6 + 1.0) / 3 = 0.8
    # F1:        (0.7 + 0.7 + 1.0) / 3 = 0.8
    #
    # Redondeamos para evitar diferencias de punto flotante.
    assert round(resumen["precision"], 2) == 0.8
    assert round(resumen["cobertura"], 2) == 0.8
    assert round(resumen["f1"], 2) == 0.8


def test_resumir_metricas_sin_resultados():
    """Verifica que una evaluación vacía devuelva promedios cero.

    Comprueba que la función gestione correctamente
    una lista vacía sin provocar divisiones por cero.
    """

    # Ejecutamos la función sin resultados disponibles.
    resumen = evaluar_respuestas.resumir_metricas([])

    # Todas las métricas deben ser cero.
    assert resumen == {
        "precision": 0.0,
        "cobertura": 0.0,
        "f1": 0.0,
    }

def test_obtener_peores_casos_ordena_y_respeta_limite():
    """Verifica la selección de respuestas con menor F1.

    Comprueba que la función:
    - Ordene las evaluaciones por F1 ascendente.
    - Respete la cantidad máxima solicitada.
    - No modifique el orden de la lista original.
    - Devuelva una lista vacía cuando el límite sea cero.
    """

    # Definimos cuatro evaluaciones simuladas.
    # Sus puntuaciones F1 están deliberadamente desordenadas.
    resultados = [
        {
            "consulta": "Pregunta A",
            "respuesta": "Respuesta A",
            "precision": 0.9,
            "cobertura": 0.9,
            "f1": 0.9,
        },
        {
            "consulta": "Pregunta B",
            "respuesta": "Respuesta B",
            "precision": 0.3,
            "cobertura": 0.3,
            "f1": 0.3,
        },
        {
            "consulta": "Pregunta C",
            "respuesta": "Respuesta C",
            "precision": 0.7,
            "cobertura": 0.7,
            "f1": 0.7,
        },
        {
            "consulta": "Pregunta D",
            "respuesta": "Respuesta D",
            "precision": 0.5,
            "cobertura": 0.5,
            "f1": 0.5,
        },
    ]

    # Guardamos el orden original para comprobar
    # que la función no lo modifique.
    orden_original = [
        resultado["consulta"] for resultado in resultados
    ]

    # Solicitamos únicamente los tres casos con menor F1.
    peores_casos = evaluar_respuestas.obtener_peores_casos(
        resultados,
        limite=3,
    )

    # Verificamos que se devuelvan exactamente tres casos.
    assert len(peores_casos) == 3

    # El orden esperado corresponde a los valores
    # F1 de 0.3, 0.5 y 0.7, respectivamente.
    assert [
        resultado["consulta"] for resultado in peores_casos
    ] == [
        "Pregunta B",
        "Pregunta D",
        "Pregunta C",
    ]

    # Confirmamos que la lista original mantiene su orden.
    assert [
        resultado["consulta"] for resultado in resultados
    ] == orden_original

    # Un límite de cero no debe devolver resultados.
    assert evaluar_respuestas.obtener_peores_casos(
        resultados,
        limite=0,
    ) == []

def test_ejecutar_evaluacion_bloque_16_integracion(
    monkeypatch,
    tmp_path,
    capsys,
):
    """Verifica el flujo completo del Bloque 16 sin utilizar Gemini.

    Comprueba que:
    - Cada consulta se ejecute exactamente una vez.
    - Las métricas se calculen correctamente.
    - Los resultados se guarden en formato JSON.
    - Se presenten los promedios y los casos con menor F1.
    - No se realicen solicitudes reales a la API.

    Args:
        monkeypatch: Permite sustituir temporalmente
            funciones y configuraciones durante la prueba.
        tmp_path: Directorio temporal proporcionado por pytest.
        capsys: Permite capturar la salida de la terminal.
    """

    # Importamos Path para construir rutas de archivos
    # y json para comprobar el contenido guardado.
    import json
    from pathlib import Path

    # Definimos respuestas simuladas para las tres consultas.
    respuestas_simuladas = {
        "¿Qué es Python?": (
            "Python es un lenguaje de programación interpretado."
        ),
        "¿Cuándo se creó Python?": (
            "Python fue creado en 1989."
        ),
        "¿Qué es una lista en Python?": (
            "Una lista es una colección ordenada."
        ),
    }

    # Registramos las consultas para comprobar
    # que ninguna pregunta se envíe más de una vez.
    consultas_recibidas: list[str] = []

    def consultar_modelo_simulado(pregunta: str) -> str:
        """Simula Gemini y registra cada consulta recibida."""

        consultas_recibidas.append(pregunta)
        return respuestas_simuladas[pregunta]

    # Sustituimos el cliente real por nuestra simulación.
    monkeypatch.setattr(
        evaluar_respuestas,
        "consultar_modelo",
        consultar_modelo_simulado,
    )

    # Cambiamos temporalmente el directorio de trabajo
    # para que el JSON se guarde fuera del proyecto.
    monkeypatch.chdir(tmp_path)

    # Ejecutamos el flujo completo del Bloque 16.
    evaluar_respuestas.ejecutar_evaluacion_bloque_16()

    # Comprobamos que cada consulta se haya realizado
    # exactamente una vez y en el orden configurado.
    assert consultas_recibidas == [
        caso["consulta"]
        for caso in evaluar_respuestas.CASOS_EVALUACION_BLOQUE_16
    ]

    # Verificamos que se haya creado el archivo JSON.
    ruta_json = (
        Path("resultados") / "resultados_metricas.json"
    )

    assert ruta_json.is_file()

    # Recuperamos los resultados guardados.
    resultados = json.loads(
        ruta_json.read_text(encoding="utf-8")
    )

    # Deben existir tres evaluaciones.
    assert len(resultados) == 3

    # Comprobamos que cada respuesta corresponda
    # a la consulta original.
    for resultado in resultados:
        assert resultado["respuesta"] == respuestas_simuladas[
            resultado["consulta"]
        ]

        # Todas las métricas deben estar entre cero y uno.
        for metrica in ("precision", "cobertura", "f1"):
            assert 0.0 <= resultado[metrica] <= 1.0

    # Recuperamos la salida generada en la terminal.
    salida = capsys.readouterr().out

    # Verificamos que se haya presentado el resumen.
    assert "Respuestas evaluadas: 3" in salida
    assert "Precisión promedio:" in salida
    assert "Cobertura promedio:" in salida
    assert "F1 promedio:" in salida
    assert "CASOS CON MENOR F1" in salida