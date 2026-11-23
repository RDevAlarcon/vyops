
"""Pruebas automatizadas del dataset y seguimiento de tuning.

Este módulo verifica las funciones definidas en
dataset_tuning.py para validar ejemplos de entrenamiento
y consultar el estado de trabajos de ajuste de modelos.

Las pruebas cubren:

    1. Cantidad de ejemplos del dataset original.
    2. Equilibrio entre las categorías del conjunto.
    3. Validación del dataset original.
    4. Detección de entradas vacías.
    5. Detección de entradas duplicadas.
    6. Detección de salidas JSON inválidas.
    7. Detección de campos obligatorios faltantes.
    8. Validación de las intenciones permitidas.
    9. Validación de las prioridades permitidas.
    10. Seguimiento de un trabajo hasta su finalización.
    11. Reconocimiento de diferentes estados finales.

Los ejemplos de tuning utilizan la estructura
types.TuningExample de Google GenAI.

Las respuestas esperadas contienen los campos
"intencion" y "prioridad", que representan
la clasificación de solicitudes.

Las pruebas de seguimiento sustituyen el cliente
de Google GenAI y las esperas por simulaciones.

No se crean trabajos reales de tuning ni se
realizan solicitudes a servicios externos.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite construir y validar las salidas JSON
# utilizadas en los ejemplos de entrenamiento.
import json

# Herramientas para simular clientes, respuestas
# y llamadas a funciones externas.
from unittest.mock import Mock, patch

# Tipos utilizados por Google GenAI para representar
# ejemplos de tuning, trabajos y sus estados.
from google.genai import types

# Datos y funciones del módulo de preparación
# y seguimiento de trabajos de tuning.
from dataset_tuning import (
    ejemplos,
    ejemplos_raw,
    chequear_balance,
    validar_dataset,
    esperar_a_que_termine,
)


# ============================================================
# 2. INTEGRIDAD DEL DATASET
# ============================================================

def test_dataset_tiene_12_ejemplos():
    """Verifica que el dataset contenga exactamente 12 ejemplos.

    Comprueba la cantidad de registros disponibles
    en el conjunto de ejemplos preparados para tuning.

    Esta prueba permite detectar cambios accidentales
    en el tamaño del dataset original.
    """

    # El conjunto preparado debe contener 12 ejemplos.
    assert len(ejemplos) == 12


def test_dataset_esta_equilibrado():
    """Verifica la distribución de ejemplos por categoría.

    Utiliza chequear_balance() para obtener la cantidad
    de registros asociados a cada categoría.

    Verificaciones:
        - Existen exactamente cuatro categorías.
        - Cada categoría contiene tres ejemplos.

    Este escenario comprueba el equilibrio esperado
    del dataset utilizado en las pruebas.
    """

    # Calcula la distribución de los datos originales.
    balance = chequear_balance(ejemplos_raw)

    # Comprueba que existan cuatro categorías.
    assert len(balance) == 4

    # Todas las categorías deben tener tres ejemplos.
    assert all(cantidad == 3 for cantidad in balance.values())


def test_dataset_original_es_valido():
    """Verifica que el dataset original supere la validación.

    Ejecuta validar_dataset() sobre los ejemplos
    preparados para tuning.

    La función debe devolver una lista vacía,
    indicando que no se detectaron problemas
    mediante las reglas de validación implementadas.
    """

    # Ningún ejemplo original debe generar errores.
    assert validar_dataset(ejemplos) == []


# ============================================================
# 3. VALIDACIÓN DE ENTRADAS
# ============================================================

def test_detecta_entrada_vacia():
    """Verifica la detección de una entrada sin contenido.

    Construye un ejemplo de tuning cuyo text_input
    contiene una cadena vacía.

    La salida mantiene una estructura JSON válida
    para aislar el problema de la entrada.

    Verificación:
        - La validación informa "text_input vacío".
    """

    # Construye un ejemplo con entrada vacía
    # y una salida JSON estructuralmente válida.
    datos = [
        types.TuningExample(
            text_input="",
            output=json.dumps({
                "intencion": "reclamo",
                "prioridad": "alta",
            }),
        )
    ]

    # Ejecuta las reglas de validación.
    problemas = validar_dataset(datos)

    # Comprueba que se detecte la entrada vacía.
    assert any("text_input vacío" in p for p in problemas)


def test_detecta_entrada_duplicada():
    """Verifica la detección de entradas repetidas.

    Construye dos ejemplos con el mismo text_input,
    pero con prioridades diferentes en sus salidas.

    Verificación:
        - La validación informa un problema
          relacionado con duplicados.

    Esta prueba comprueba que las entradas repetidas
    sean identificadas aunque sus etiquetas difieran.
    """

    # Define dos ejemplos con la misma consulta.
    datos = [
        types.TuningExample(
            text_input="Solicitud repetida",
            output='{"intencion": "reclamo", "prioridad": "alta"}',
        ),
        types.TuningExample(
            text_input="Solicitud repetida",
            output='{"intencion": "reclamo", "prioridad": "baja"}',
        ),
    ]

    # Valida el conjunto de ejemplos.
    problemas = validar_dataset(datos)

    # Comprueba que se informe la duplicación.
    assert any("duplicado" in p for p in problemas)


# ============================================================
# 4. VALIDACIÓN DE SALIDAS JSON
# ============================================================

def test_detecta_json_invalido():
    """Verifica el rechazo de una salida que no es JSON.

    Construye un ejemplo con una entrada válida
    y una salida de texto sin estructura JSON.

    Verificación:
        - La validación informa que se requiere JSON válido.

    Esta prueba comprueba el formato esperado
    para las respuestas del dataset de tuning.
    """

    # Define una salida que no puede interpretarse como JSON.
    datos = [
        types.TuningExample(
            text_input="Quiero consultar mi solicitud",
            output="No es JSON",
        )
    ]

    # Ejecuta la validación del ejemplo.
    problemas = validar_dataset(datos)

    # Comprueba que se detecte el formato inválido.
    assert any("JSON válido" in p for p in problemas)


def test_detecta_campo_faltante():
    """Verifica la detección de un campo obligatorio ausente.

    Construye un ejemplo cuya salida JSON
    contiene "intencion", pero omite "prioridad".

    Verificación:
        - La validación informa la ausencia
          del campo "prioridad".

    Este escenario comprueba que una salida JSON
    sintácticamente válida también cumpla
    con la estructura requerida.
    """

    # Define una salida JSON sin el campo prioridad.
    datos = [
        types.TuningExample(
            text_input="Quiero ingresar un reclamo",
            output='{"intencion": "reclamo"}',
        )
    ]

    # Valida la estructura del ejemplo.
    problemas = validar_dataset(datos)

    # Comprueba que se identifique el campo faltante.
    assert any("prioridad" in p for p in problemas)


# ============================================================
# 5. VALIDACIÓN DE VALORES PERMITIDOS
# ============================================================

def test_detecta_intencion_no_permitida():
    """Verifica el rechazo de una intención no permitida.

    Construye un ejemplo con una intención
    denominada "desconocida".

    La salida contiene ambos campos requeridos,
    por lo que se evalúa específicamente
    la validez del valor de "intencion".

    Verificación:
        - Se informa "intención no permitida".
    """

    # Define una intención fuera del conjunto permitido.
    datos = [
        types.TuningExample(
            text_input="Necesito información municipal",
            output=json.dumps({
                "intencion": "desconocida",
                "prioridad": "baja",
            }),
        )
    ]

    # Ejecuta las reglas de validación.
    problemas = validar_dataset(datos)

    # Comprueba que se rechace la intención.
    assert any("intención no permitida" in p for p in problemas)


def test_detecta_prioridad_no_permitida():
    """Verifica el rechazo de una prioridad no permitida.

    Construye un ejemplo con una intención válida
    y una prioridad denominada "urgente_maxima".

    Verificación:
        - Se informa "prioridad no permitida".

    Este escenario comprueba que los valores
    de prioridad respeten el conjunto definido
    por las reglas de validación.
    """

    # Define una prioridad fuera del conjunto permitido.
    datos = [
        types.TuningExample(
            text_input="Quiero presentar una solicitud",
            output=json.dumps({
                "intencion": "nueva_solicitud",
                "prioridad": "urgente_maxima",
            }),
        )
    ]

    # Ejecuta la validación del ejemplo.
    problemas = validar_dataset(datos)

    # Comprueba que se detecte la prioridad inválida.
    assert any("prioridad no permitida" in p for p in problemas)


# ============================================================
# 6. SEGUIMIENTO DE UN TRABAJO DE TUNING
# ============================================================

def test_esperar_a_que_termine():
    """Verifica el seguimiento hasta la finalización exitosa.

    Simula un cliente de Google GenAI que devuelve
    dos estados consecutivos del mismo trabajo:

        1. JOB_STATE_RUNNING.
        2. JOB_STATE_SUCCEEDED.

    Verificaciones:
        - Se devuelve el estado de éxito.
        - El cliente se consulta dos veces.
        - Se realiza una espera simulada de un segundo.

    Se sustituye time.sleep para evitar
    una espera real durante la prueba.
    """

    # Construye un cliente simulado.
    cliente = Mock()

    # Representa un trabajo que continúa ejecutándose.
    trabajo_en_progreso = Mock()
    trabajo_en_progreso.state = types.JobState.JOB_STATE_RUNNING

    # Representa un trabajo finalizado correctamente.
    trabajo_finalizado = Mock()
    trabajo_finalizado.state = types.JobState.JOB_STATE_SUCCEEDED

    # Configura la secuencia de respuestas
    # que devolverá la consulta del trabajo.
    cliente.tunings.get.side_effect = [
        trabajo_en_progreso,
        trabajo_finalizado,
    ]

    # Sustituye temporalmente la función de espera
    # para registrar su invocación sin detener la prueba.
    with patch("dataset_tuning.time.sleep") as dormir:
        resultado = esperar_a_que_termine(
            client=cliente,
            nombre_trabajo="tunings/prueba-simulada",
            intervalo_segundos=1,
        )

    # El seguimiento debe finalizar con éxito.
    assert resultado.state == types.JobState.JOB_STATE_SUCCEEDED

    # Deben realizarse dos consultas al cliente.
    assert cliente.tunings.get.call_count == 2

    # Entre ambas consultas debe existir una espera.
    dormir.assert_called_once_with(1)


# ============================================================
# 7. RECONOCIMIENTO DE ESTADOS FINALES
# ============================================================

# Pytest permite ejecutar el mismo escenario
# con diferentes estados finales del trabajo.
import pytest


@pytest.mark.parametrize(
    "estado_final",
    [
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    ],
)
def test_seguimiento_termina_en_estado_final(
    estado_final,
    monkeypatch,
):
    """Verifica que el seguimiento termine ante estados finales.

    Ejecuta el mismo escenario con tres estados:

        - JOB_STATE_FAILED.
        - JOB_STATE_CANCELLED.
        - JOB_STATE_PARTIALLY_SUCCEEDED.

    Verificaciones:
        - Se devuelve el estado final recibido.
        - El cliente se consulta una sola vez.
        - No se realiza ninguna espera adicional.

    Args:
        estado_final:
            Estado del trabajo proporcionado
            por la parametrización de pytest.

        monkeypatch:
            Fixture utilizada para sustituir
            temporalmente time.sleep.

    La prueba comprueba que el seguimiento no continúe
    consultando un trabajo que ya alcanzó uno
    de los estados finales evaluados.
    """

    # Cliente simulado que expone la interfaz
    # tunings.get utilizada por el seguimiento.
    class ClienteSimulado:
        """Simula la consulta del estado de un trabajo de tuning.

        Attributes:
            consultas (int):
                Cantidad de consultas realizadas al cliente.

            tunings:
                Referencia al propio objeto para proporcionar
                el método get mediante cliente.tunings.get.
        """

        def __init__(self):
            """Inicializa el contador y la interfaz simulada."""

            # Registra cuántas veces se consulta el trabajo.
            self.consultas = 0

            # Permite utilizar cliente.tunings.get().
            self.tunings = self

        def get(self, name):
            """Devuelve un trabajo con el estado final configurado.

            Args:
                name:
                    Identificador del trabajo consultado.

            Returns:
                types.TuningJob:
                    Trabajo simulado con el estado
                    recibido desde la parametrización.
            """

            # Registra cada consulta realizada.
            self.consultas += 1

            # Devuelve un trabajo que ya alcanzó
            # el estado final evaluado.
            return types.TuningJob(
                name=name,
                state=estado_final,
            )

    # Construye una instancia del cliente simulado.
    cliente = ClienteSimulado()

    def no_debe_dormir(segundos):
        """Impide esperas después de alcanzar un estado final.

        Args:
            segundos:
                Duración de la espera solicitada.

        Raises:
            AssertionError:
                Siempre que se intente ejecutar una espera.

        Esta función permite detectar cualquier intento
        de continuar esperando después de la finalización.
        """

        raise AssertionError(
            "No debe esperar después de un estado final"
        )

    # Sustituye time.sleep por una función
    # que falla si se solicita una espera.
    monkeypatch.setattr(
        "dataset_tuning.time.sleep",
        no_debe_dormir,
    )

    # Consulta el trabajo simulado.
    resultado = esperar_a_que_termine(
        client=cliente,
        nombre_trabajo="tunings/prueba-simulada",
        intervalo_segundos=1,
    )

    # Comprueba que se devuelva el estado final recibido.
    assert resultado.state == estado_final

    # El trabajo finalizado debe consultarse una sola vez.
    assert cliente.consultas == 1
