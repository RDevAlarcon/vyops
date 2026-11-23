
"""Pruebas de cancelación municipal simulada.

Este módulo verifica los controles de autorización humana
aplicados a la cancelación simulada de solicitudes en VyOps.

La operación se realiza mediante cancelar_solicitud_simulada()
y utiliza SupervisorHumano para gestionar la autorización.

Las pruebas cubren seis escenarios:

    1. Cancelación con autorización humana aprobada.
    2. Bloqueo de cancelaciones sin autorización.
    3. Bloqueo de operaciones rechazadas por el supervisor.
    4. Prevención de reutilización de autorizaciones.
    5. Validación de la solicitud asociada a la autorización.
    6. Rechazo de identificadores de solicitud vacíos.

El supervisor utiliza funciones simuladas que devuelven
True o False para representar decisiones humanas.

Estas pruebas comprueban los controles del flujo
simulado; no realizan cancelaciones reales en
sistemas municipales externos.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Función que ejecuta una cancelación municipal simulada
# y devuelve el estado resultante de la operación.
from src.cancelacion_simulada import cancelar_solicitud_simulada

# Componente que gestiona la autorización humana
# requerida antes de ejecutar la cancelación.
from src.supervisor_humano import SupervisorHumano


# ============================================================
# 2. CANCELACIÓN CON AUTORIZACIÓN APROBADA
# ============================================================

def test_cancelacion_autorizada() -> None:
    """Permite simular una cancelación aprobada.

    Configura un supervisor cuya decisión es afirmativa
    y solicita autorización para SOL-12345.

    Verificaciones:
        - La operación devuelve el estado "simulada".
        - El resultado conserva el número de solicitud.

    Este escenario representa el flujo permitido
    cuando existe una autorización humana válida.
    """

    # Configura un supervisor que aprueba la operación.
    supervisor = SupervisorHumano(lambda: True)

    # Obtiene una autorización asociada a la solicitud.
    autorizacion = supervisor.autorizar_cancelacion("SOL-12345")

    # Ejecuta la cancelación simulada con la autorización.
    resultado = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        autorizacion,
    )

    # Comprueba que la operación haya sido simulada
    # y corresponda a la solicitud autorizada.
    assert resultado["estado"] == "simulada"
    assert resultado["numero_solicitud"] == "SOL-12345"


# ============================================================
# 3. CANCELACIÓN SIN AUTORIZACIÓN
# ============================================================

def test_cancelacion_sin_autorizacion() -> None:
    """Bloquea una cancelación sin autorización humana.

    Configura un supervisor con decisión afirmativa,
    pero intenta ejecutar la operación sin proporcionar
    una autorización.

    Verificación:
        - El resultado devuelve el estado "bloqueada".

    La prueba comprueba que una decisión potencialmente
    favorable del supervisor no sustituya la necesidad
    de obtener una autorización para la operación.
    """

    # Configura un supervisor con decisión afirmativa.
    supervisor = SupervisorHumano(lambda: True)

    # Intenta cancelar sin proporcionar autorización.
    resultado = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        None,
    )

    # La ausencia de autorización debe bloquear la operación.
    assert resultado["estado"] == "bloqueada"


# ============================================================
# 4. CANCELACIÓN RECHAZADA POR EL SUPERVISOR
# ============================================================

def test_cancelacion_rechazada_por_supervisor() -> None:
    """Bloquea una operación rechazada por el supervisor.

    Configura un supervisor cuya decisión es negativa
    e intenta obtener autorización para SOL-12345.

    Verificación:
        - La cancelación devuelve el estado "bloqueada".

    Este escenario comprueba que el flujo respete
    una decisión humana de rechazo.
    """

    # Configura un supervisor que rechaza la operación.
    supervisor = SupervisorHumano(lambda: False)

    # Solicita autorización para la cancelación.
    autorizacion = supervisor.autorizar_cancelacion("SOL-12345")

    # Intenta ejecutar la cancelación con el resultado
    # del proceso de autorización.
    resultado = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        autorizacion,
    )

    # La decisión negativa debe bloquear la cancelación.
    assert resultado["estado"] == "bloqueada"


# ============================================================
# 5. PREVENCIÓN DE REUTILIZACIÓN DE AUTORIZACIONES
# ============================================================

def test_cancelacion_no_reutiliza_autorizacion() -> None:
    """Impide ejecutar dos cancelaciones con una autorización.

    Obtiene una autorización aprobada para SOL-12345
    y la utiliza en dos operaciones consecutivas.

    Verificaciones:
        - La primera cancelación devuelve "simulada".
        - La segunda cancelación devuelve "bloqueada".

    Este escenario comprueba que una autorización
    utilizada no pueda volver a habilitar
    la misma operación.
    """

    # Configura un supervisor que aprueba la cancelación.
    supervisor = SupervisorHumano(lambda: True)

    # Obtiene una única autorización para la solicitud.
    autorizacion = supervisor.autorizar_cancelacion("SOL-12345")

    # Primera utilización de la autorización.
    primero = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        autorizacion,
    )

    # Segundo intento utilizando la misma autorización.
    segundo = cancelar_solicitud_simulada(
        "SOL-12345",
        supervisor,
        autorizacion,
    )

    # Solo la primera operación debe ser permitida.
    assert primero["estado"] == "simulada"
    assert segundo["estado"] == "bloqueada"


# ============================================================
# 6. AUTORIZACIÓN VINCULADA A UNA SOLICITUD
# ============================================================

def test_cancelacion_no_autoriza_otra_solicitud() -> None:
    """Impide cancelar una solicitud distinta de la autorizada.

    Obtiene una autorización para SOL-12345,
    pero intenta utilizarla para cancelar SOL-99999.

    Verificación:
        - La operación devuelve el estado "bloqueada".

    Este escenario comprueba que la autorización
    esté vinculada al identificador de la solicitud
    para la que fue concedida.
    """

    # Configura un supervisor con decisión afirmativa.
    supervisor = SupervisorHumano(lambda: True)

    # Autoriza exclusivamente la solicitud SOL-12345.
    autorizacion = supervisor.autorizar_cancelacion("SOL-12345")

    # Intenta utilizar la autorización para otra solicitud.
    resultado = cancelar_solicitud_simulada(
        "SOL-99999",
        supervisor,
        autorizacion,
    )

    # La autorización no debe habilitar otra solicitud.
    assert resultado["estado"] == "bloqueada"


# ============================================================
# 7. VALIDACIÓN DEL IDENTIFICADOR DE SOLICITUD
# ============================================================

def test_cancelacion_rechaza_numero_vacio() -> None:
    """Rechaza solicitudes sin identificador.

    Intenta ejecutar una cancelación proporcionando
    una cadena vacía como número de solicitud.

    Verificación:
        - La operación devuelve el estado "rechazada".

    Este escenario comprueba que el flujo distinga
    una solicitud inválida de una operación bloqueada
    por ausencia de autorización.
    """

    # Configura un supervisor con decisión afirmativa.
    supervisor = SupervisorHumano(lambda: True)

    # Intenta cancelar una solicitud sin identificador.
    resultado = cancelar_solicitud_simulada(
        "",
        supervisor,
        None,
    )

    # La solicitud inválida debe ser rechazada.
    assert resultado["estado"] == "rechazada"
