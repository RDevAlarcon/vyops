"""Pruebas automatizadas de la evaluación del Bloque 17.

Verificamos la recuperación de resultados anteriores,
la identificación de consultas pendientes y la conservación
de los datos originales.

Estas pruebas no realizan llamadas reales a Gemini.
"""

import json

from src.casos_evaluacion_bloque_17 import (
    CASOS_EVALUACION_BLOQUE_17,
)
from src.evaluacion_bloque_17 import (
    cargar_resultados_anteriores,
    obtener_casos_pendientes,
)


def test_banco_contiene_23_casos() -> None:
    """Verifica que el banco tenga 23 consultas válidas."""

    # Comprobamos la cantidad total de casos configurados.
    assert len(CASOS_EVALUACION_BLOQUE_17) == 23

    # Cada caso debe tener una consulta y una referencia.
    for caso in CASOS_EVALUACION_BLOQUE_17:
        assert caso["consulta"].strip()
        assert caso["referencia"].strip()

    # No deben existir consultas duplicadas.
    consultas = [
        caso["consulta"]
        for caso in CASOS_EVALUACION_BLOQUE_17
    ]

    assert len(consultas) == len(set(consultas))


def test_cargar_resultados_desde_json(tmp_path) -> None:
    """Comprueba la recuperación de resultados guardados."""

    # Creamos un archivo temporal para no modificar
    # la evidencia real del Bloque 16.
    ruta = tmp_path / "resultados.json"

    resultados_esperados = [
        {
            "consulta": "¿Qué es Python?",
            "respuesta": "Python es un lenguaje de programación.",
            "precision": 0.8,
            "cobertura": 1.0,
            "f1": 0.89,
        }
    ]

    # Guardamos los datos simulados en formato JSON.
    ruta.write_text(
        json.dumps(resultados_esperados, ensure_ascii=False),
        encoding="utf-8",
    )

    # Recuperamos los resultados mediante nuestra función.
    resultados = cargar_resultados_anteriores(ruta)

    assert resultados == resultados_esperados


def test_archivo_inexistente_devuelve_lista_vacia(tmp_path) -> None:
    """Verifica que un archivo inexistente no genere errores."""

    ruta = tmp_path / "archivo_inexistente.json"

    assert cargar_resultados_anteriores(ruta) == []


def test_json_con_estructura_incorrecta(tmp_path) -> None:
    """Comprueba el rechazo de un JSON que no contiene una lista."""

    import pytest

    ruta = tmp_path / "resultados_invalidos.json"

    ruta.write_text(
        '{"consulta": "Python"}',
        encoding="utf-8",
    )

    # La función debe rechazar estructuras incompatibles.
    with pytest.raises(ValueError):
        cargar_resultados_anteriores(ruta)


def test_identificar_casos_pendientes() -> None:
    """Comprueba que se excluyan las consultas ya evaluadas."""

    casos = [
        {"consulta": "Pregunta A", "referencia": "Respuesta A"},
        {"consulta": "Pregunta B", "referencia": "Respuesta B"},
        {"consulta": "Pregunta C", "referencia": "Respuesta C"},
    ]

    anteriores = [
        {
            "consulta": "Pregunta A",
            "respuesta": "Respuesta generada A",
            "precision": 1.0,
            "cobertura": 1.0,
            "f1": 1.0,
        }
    ]

    # Conservamos copias para verificar que los datos
    # originales no sean modificados.
    casos_originales = [caso.copy() for caso in casos]
    anteriores_originales = [
        resultado.copy() for resultado in anteriores
    ]

    pendientes = obtener_casos_pendientes(casos, anteriores)

    assert len(pendientes) == 2

    assert [caso["consulta"] for caso in pendientes] == [
        "Pregunta B",
        "Pregunta C",
    ]

    # Verificamos que ambas listas originales permanezcan intactas.
    assert casos == casos_originales
    assert anteriores == anteriores_originales


def test_todos_los_casos_evaluados() -> None:
    """Comprueba que no haya pendientes cuando todos están evaluados."""

    casos = [
        {"consulta": "Pregunta A", "referencia": "Respuesta A"},
    ]

    anteriores = [
        {
            "consulta": "Pregunta A",
            "respuesta": "Respuesta generada A",
            "precision": 1.0,
            "cobertura": 1.0,
            "f1": 1.0,
        }
    ]

    assert obtener_casos_pendientes(casos, anteriores) == []

def test_guardado_progresivo_ante_fallo(
    tmp_path,
    monkeypatch,
) -> None:
    """Verifica que una respuesta se conserve si Gemini falla.

    Simula dos consultas: la primera funciona correctamente
    y la segunda genera un error de comunicación.

    Comprueba que el primer resultado permanezca guardado
    en JSON, incluso cuando la evaluación se interrumpe.
    """

    import pytest
    import src.evaluacion_bloque_17 as modulo

    # Definimos dos casos de prueba independientes.
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

    # Simulamos el comportamiento de Gemini.
    # La primera consulta responde; la segunda falla.
    def consultar_modelo_simulado(consulta: str) -> str:
        if consulta == casos[0]["consulta"]:
            return "La capital de Chile es Santiago."

        raise RuntimeError("Fallo simulado de Gemini.")

    # Sustituimos temporalmente el cliente real.
    # De esta manera no consumimos cuota de la API.
    monkeypatch.setattr(
        modulo,
        "consultar_modelo",
        consultar_modelo_simulado,
    )

    # Utilizamos una ruta temporal para proteger
    # los resultados reales de los bloques anteriores.
    ruta = tmp_path / "resultados_bloque_17.json"

    # Esperamos que la segunda consulta interrumpa
    # la ejecución con un error controlado.
    with pytest.raises(RuntimeError, match="Fallo simulado"):
        modulo.evaluar_casos_pendientes(
            casos_pendientes=casos,
            ruta_archivo=ruta,
            resultados_existentes=[],
        )

    # Recuperamos el archivo generado antes del fallo.
    resultados = cargar_resultados_anteriores(ruta)

    # La primera respuesta debe haberse conservado.
    assert len(resultados) == 1
    assert resultados[0]["consulta"] == casos[0]["consulta"]
    assert resultados[0]["referencia"] == casos[0]["referencia"]

    # También deben existir las tres métricas.
    assert "precision" in resultados[0]
    assert "cobertura" in resultados[0]
    assert "f1" in resultados[0]

def test_reanudar_evaluacion_sin_duplicados(
    tmp_path,
    monkeypatch,
) -> None:
    """Verifica que una evaluación pueda reanudarse sin duplicados.

    Simula una evaluación con una respuesta ya guardada.
    Comprueba que Gemini solo reciba la consulta pendiente
    y que el JSON final conserve ambos resultados.
    """

    import src.evaluacion_bloque_17 as modulo

    # Preparamos dos casos para la evaluación.
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

    # Simulamos un resultado guardado anteriormente.
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

    # Registramos las consultas realizadas al modelo.
    consultas_realizadas: list[str] = []

    def consultar_modelo_simulado(consulta: str) -> str:
        """Simula Gemini y registra cada consulta recibida."""

        consultas_realizadas.append(consulta)
        return "2 más 2 es 4."

    # Sustituimos Gemini por la función simulada.
    monkeypatch.setattr(
        modulo,
        "consultar_modelo",
        consultar_modelo_simulado,
    )

    # Utilizamos un archivo temporal.
    ruta = tmp_path / "resultados_bloque_17.json"

    # Simulamos el archivo existente antes de reanudar.
    ruta.write_text(
        json.dumps(resultados_anteriores, ensure_ascii=False),
        encoding="utf-8",
    )

    # Reanudamos incluyendo deliberadamente ambos casos.
    # La función debe omitir el caso ya registrado.
    modulo.evaluar_casos_pendientes(
        casos_pendientes=casos,
        ruta_archivo=ruta,
        resultados_existentes=resultados_anteriores,
    )

    # Gemini debe haber recibido solo la segunda pregunta.
    assert consultas_realizadas == [casos[1]["consulta"]]

    # Recuperamos los resultados persistidos.
    resultados = cargar_resultados_anteriores(ruta)

    # Deben existir exactamente dos resultados.
    assert len(resultados) == 2

    # Verificamos que ninguna consulta esté duplicada.
    consultas_guardadas = [
        resultado["consulta"]
        for resultado in resultados
    ]

    assert len(consultas_guardadas) == len(set(consultas_guardadas))

    # La evaluación anterior debe conservarse intacta.
    assert resultados[0] == resultados_anteriores[0]

def test_ejecucion_completa_bloque_17(
    tmp_path,
    monkeypatch,
) -> None:
    """Verifica el flujo completo del Bloque 17 sin usar Gemini.

    Simula tres respuestas anteriores y genera las veinte
    restantes, comprobando que se almacenen 23 resultados
    sin duplicados y sin modificar el archivo original.
    """

    import ejecutar_bloque_17 as modulo_ejecucion
    import src.evaluacion_bloque_17 as modulo_evaluacion

    # Preparamos un directorio temporal independiente.
    monkeypatch.chdir(tmp_path)

    directorio = tmp_path / "resultados"
    directorio.mkdir()

    ruta_original = directorio / "resultados_metricas.json"
    ruta_nueva = directorio / "resultados_bloque_17.json"

    # Simulamos los tres resultados del Bloque 16.
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

    contenido_original = json.dumps(
        resultados_originales,
        ensure_ascii=False,
        indent=2,
    )

    ruta_original.write_text(
        contenido_original,
        encoding="utf-8",
    )

    # Registramos las consultas para detectar repeticiones.
    consultas_realizadas: list[str] = []

    def consultar_modelo_simulado(consulta: str) -> str:
        """Devuelve una respuesta simulada sin llamar a Gemini."""

        consultas_realizadas.append(consulta)
        return "Respuesta simulada para evaluación."

    monkeypatch.setattr(
        modulo_evaluacion,
        "consultar_modelo",
        consultar_modelo_simulado,
    )

    # Ejecutamos el flujo completo con archivos temporales.
    modulo_ejecucion.ejecutar_bloque_17()

    # Recuperamos los resultados del Bloque 17.
    resultados = cargar_resultados_anteriores(ruta_nueva)

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

    assert len(consultas_realizadas) == 20
    assert len(cargar_resultados_anteriores(ruta_nueva)) == 23