
"""Pruebas de la herramienta LangChain de cancelación simulada.

Este módulo verifica el comportamiento de la herramienta
construida mediante construir_herramienta_cancelacion,
definida en src.herramienta_cancelacion.

La herramienta representa una operación de cancelación
simulada que requiere una decisión de aprobación externa.

Las pruebas comprueban cinco escenarios:

    1. Exposición controlada de los argumentos al modelo.
    2. Cancelación simulada con aprobación humana.
    3. Bloqueo de una cancelación rechazada.
    4. Solicitud de aprobación independiente por operación.
    5. Bloqueo cuando falla el mecanismo de supervisión.

Un principio importante de este diseño es que el modelo
solo puede proporcionar el número de solicitud.

La decisión de autorización se obtiene mediante
una función externa, proporcionada al construir
la herramienta, y no mediante un argumento
controlado por el modelo.

Las pruebas utilizan decisiones simuladas
y no ejecutan cancelaciones municipales reales.

Estos escenarios verifican el comportamiento esperado
de la herramienta ante aprobaciones, rechazos y errores.
No constituyen una auditoría completa del mecanismo
de autorización humana.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Constructor de la herramienta LangChain
# utilizada para simular cancelaciones supervisadas.
from src.herramienta_cancelacion import (
    construir_herramienta_cancelacion,
)


# ============================================================
# 2. CONTROL DE ARGUMENTOS EXPUESTOS AL MODELO
# ============================================================

def test_herramienta_expone_solo_numero_solicitud() -> None:
    """Impide que el modelo proporcione autorizaciones.

    Construye la herramienta utilizando una función
    externa que rechaza las solicitudes de aprobación.

    Verificaciones:
        - La herramienta tiene el nombre esperado.
        - Su interfaz expone únicamente numero_solicitud.

    Esta prueba comprueba que los argumentos disponibles
    para la invocación no incluyan campos mediante
    los cuales el modelo pueda declarar su propia aprobación.

    La decisión humana permanece fuera del esquema
    de argumentos expuesto por la herramienta.
    """

    # Construye la herramienta con una decisión
    # externa que devuelve False.
    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=lambda: False,
    )

    # Comprueba el nombre registrado en LangChain.
    assert herramienta.name == "cancelar_solicitud_simulada"

    # Verifica que el único argumento expuesto
    # al modelo sea el identificador de la solicitud.
    assert set(herramienta.args) == {"numero_solicitud"}


# ============================================================
# 3. CANCELACIÓN SIMULADA CON APROBACIÓN
# ============================================================

def test_herramienta_permite_cancelacion_aprobada() -> None:
    """Simula una cancelación con aprobación externa.

    Construye una herramienta cuya función de supervisión
    devuelve una aprobación explícita mediante True.

    Posteriormente invoca la cancelación simulada
    para la solicitud SOL-12345.

    Verificaciones:
        - El estado devuelto es "simulada".
        - El identificador de solicitud se conserva.

    El resultado indica que la operación simulada
    fue aceptada por el mecanismo de autorización.
    No representa una cancelación municipal real.
    """

    # Construye la herramienta con una decisión
    # externa afirmativa.
    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=lambda: True,
    )

    # Invoca la cancelación simulada
    # para una solicitud específica.
    resultado = herramienta.invoke({
        "numero_solicitud": "SOL-12345",
    })

    # Comprueba que la operación simulada
    # haya sido autorizada.
    assert resultado["estado"] == "simulada"

    # Verifica que el resultado conserve
    # el identificador de la solicitud original.
    assert resultado["numero_solicitud"] == "SOL-12345"


# ============================================================
# 4. BLOQUEO DE CANCELACIÓN RECHAZADA
# ============================================================

def test_herramienta_bloquea_cancelacion_rechazada() -> None:
    """Bloquea una operación rechazada por el supervisor.

    Construye la herramienta utilizando una función
    externa que devuelve False.

    Verificación:
        - El estado de la operación es "bloqueada".

    Esta prueba comprueba que una decisión negativa
    no permita completar la cancelación simulada.
    """

    # Construye la herramienta con una decisión
    # de supervisión negativa.
    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=lambda: False,
    )

    # Intenta ejecutar una cancelación simulada.
    resultado = herramienta.invoke({
        "numero_solicitud": "SOL-12345",
    })

    # La operación debe quedar bloqueada
    # al no existir aprobación.
    assert resultado["estado"] == "bloqueada"


# ============================================================
# 5. APROBACIÓN INDEPENDIENTE POR OPERACIÓN
# ============================================================

def test_herramienta_solicita_aprobacion_por_operacion() -> None:
    """Solicita una decisión nueva para cada cancelación.

    Define una secuencia de dos decisiones simuladas:

        Primera decisión:
            True, que representa una aprobación.

        Segunda decisión:
            False, que representa un rechazo.

    Construye una única herramienta y realiza
    dos invocaciones para solicitudes diferentes.

    Verificaciones:
        - La primera operación obtiene el estado "simulada".
        - La segunda operación obtiene el estado "bloqueada".

    Este escenario comprueba que la aprobación
    de una operación no habilite automáticamente
    la siguiente invocación de la herramienta.
    """

    # Define dos decisiones consecutivas:
    # una aprobación y posteriormente un rechazo.
    decisiones = iter([True, False])

    # Construye la herramienta utilizando una función
    # que obtiene la siguiente decisión disponible.
    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=lambda: next(decisiones),
    )

    # Primera operación:
    # recibe la aprobación simulada.
    primera = herramienta.invoke({
        "numero_solicitud": "SOL-12345",
    })

    # Segunda operación:
    # recibe el rechazo simulado.
    segunda = herramienta.invoke({
        "numero_solicitud": "SOL-99999",
    })

    # La primera cancelación debe quedar autorizada.
    assert primera["estado"] == "simulada"

    # La segunda cancelación debe quedar bloqueada.
    assert segunda["estado"] == "bloqueada"


# ============================================================
# 6. BLOQUEO ANTE ERRORES DEL SUPERVISOR
# ============================================================

def test_herramienta_bloquea_error_del_supervisor() -> None:
    """Rechaza la operación cuando falla la aprobación.

    Simula un error técnico en la función externa
    responsable de obtener la decisión del supervisor.

    La función genera RuntimeError para representar
    la indisponibilidad del mecanismo de aprobación.

    Verificación:
        - El estado devuelto es "bloqueada".

    Este escenario comprueba que un fallo
    del mecanismo de supervisión no se interprete
    como una aprobación automática.
    """

    def decision_con_error() -> bool:
        """Simula un fallo del mecanismo de supervisión.

        Raises:
            RuntimeError:
                Representa la indisponibilidad
                del supervisor externo.
        """

        # Simula un error al intentar
        # obtener la aprobación humana.
        raise RuntimeError("Supervisor no disponible")

    # Construye la herramienta utilizando
    # la función de supervisión que falla.
    herramienta = construir_herramienta_cancelacion(
        solicitar_decision=decision_con_error,
    )

    # Intenta ejecutar una cancelación simulada
    # mientras el supervisor está indisponible.
    resultado = herramienta.invoke({
        "numero_solicitud": "SOL-12345",
    })

    # La operación debe quedar bloqueada
    # cuando no es posible obtener autorización.
    assert resultado["estado"] == "bloqueada"
