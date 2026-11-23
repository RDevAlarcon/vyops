
"""Pruebas del mecanismo de supervisión humana de VyOps.

Este módulo verifica el comportamiento de SupervisorHumano,
implementado en src.supervisor_humano.

El supervisor representa un mecanismo de autorización
para operaciones sensibles, como la cancelación
de solicitudes municipales.

Las pruebas comprueban cinco escenarios:

    1. Aprobación de una cancelación simulada.
    2. Rechazo de una solicitud de cancelación.
    3. Prevención de reutilización de autorizaciones.
    4. Rechazo de autorizaciones para otras solicitudes.
    5. Bloqueo cuando el tiempo límite se ha agotado.

Las decisiones se simulan mediante funciones lambda
que devuelven True o False.

Esto permite verificar las reglas de autorización
sin requerir la intervención de una persona real.

Las pruebas se ejecutan sobre instancias independientes
de SupervisorHumano y no realizan llamadas a Gemini
ni operaciones reales sobre solicitudes municipales.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Clase responsable de gestionar las autorizaciones
# humanas para operaciones sensibles de VyOps.
from src.supervisor_humano import SupervisorHumano


# ============================================================
# 2. APROBACIÓN DE CANCELACIONES
# ============================================================

def test_supervisor_aprueba_cancelacion() -> None:
    """Comprueba que una cancelación aprobada pueda autorizarse.

    Configura un supervisor cuya decisión simulada
    es siempre afirmativa.

    Verificaciones:
        - Se obtiene un identificador de autorización.
        - La autorización corresponde a la solicitud indicada.
        - La verificación y consumo de la autorización
          devuelve True.

    Este escenario representa una aprobación
    de cancelación mediante supervisión humana simulada.
    """

    # Crea un supervisor que siempre aprueba
    # las solicitudes de autorización.
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: True,
    )

    # Solicita autorización para cancelar
    # una solicitud municipal específica.
    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
    )

    # Comprueba que se haya generado una autorización.
    assert identificador is not None

    # Verifica que la autorización sea válida
    # para la solicitud y pueda consumirse.
    assert supervisor.verificar_y_consumir(
        identificador,
        "SOL-12345",
    ) is True


# ============================================================
# 3. RECHAZO DE CANCELACIONES
# ============================================================

def test_supervisor_rechaza_cancelacion() -> None:
    """Comprueba que una decisión negativa impida autorizar.

    Configura un supervisor cuya decisión simulada
    es siempre negativa.

    Verificaciones:
        - La solicitud de autorización se rechaza.
        - No se entrega un identificador de autorización.

    Este escenario representa una cancelación
    que no cuenta con aprobación humana.
    """

    # Crea un supervisor que rechaza
    # todas las solicitudes de autorización.
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: False,
    )

    # Solicita autorización para cancelar
    # una solicitud municipal.
    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
    )

    # Una decisión negativa no debe generar
    # un identificador de autorización.
    assert identificador is None


# ============================================================
# 4. PREVENCIÓN DE REUTILIZACIÓN DE AUTORIZACIONES
# ============================================================

def test_supervisor_impide_reutilizar_autorizacion() -> None:
    """Comprueba que una autorización solo pueda consumirse una vez.

    Obtiene una autorización aprobada y realiza
    dos intentos de verificación y consumo.

    Verificaciones:
        - Se genera un identificador válido.
        - El primer consumo devuelve True.
        - El segundo consumo devuelve False.

    Esta prueba verifica que una autorización utilizada
    no pueda reutilizarse para repetir la operación.

    El comportamiento esperado corresponde a una
    autorización de uso único.
    """

    # Configura un supervisor con aprobación simulada.
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: True,
    )

    # Obtiene una autorización para la solicitud.
    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
    )

    # Comprueba que la autorización fue concedida.
    assert identificador is not None

    # El primer intento debe verificar
    # y consumir correctamente la autorización.
    assert supervisor.verificar_y_consumir(
        identificador,
        "SOL-12345",
    ) is True

    # El segundo intento debe rechazarse
    # porque la autorización ya fue consumida.
    assert supervisor.verificar_y_consumir(
        identificador,
        "SOL-12345",
    ) is False


# ============================================================
# 5. VINCULACIÓN DE AUTORIZACIONES A SOLICITUDES
# ============================================================

def test_supervisor_rechaza_otra_solicitud() -> None:
    """Comprueba que una autorización no sirva para otra solicitud.

    Genera una autorización para SOL-12345
    e intenta utilizarla con SOL-99999.

    Verificaciones:
        - La autorización original se concede.
        - El intento de utilizarla para otra solicitud
          devuelve False.

    Esta prueba comprueba la vinculación
    entre una autorización y su solicitud municipal.

    No verifica si la autorización original permanece
    disponible después del intento rechazado.
    """

    # Crea un supervisor que aprueba
    # las solicitudes de autorización.
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: True,
    )

    # Obtiene una autorización vinculada
    # a una solicitud específica.
    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
    )

    # Comprueba que se concedió la autorización.
    assert identificador is not None

    # Intenta utilizar el identificador
    # para una solicitud diferente.
    #
    # La autorización no debe aceptarse.
    assert supervisor.verificar_y_consumir(
        identificador,
        "SOL-99999",
    ) is False


# ============================================================
# 6. CONTROL DEL TIEMPO LÍMITE
# ============================================================

def test_supervisor_rechaza_timeout() -> None:
    """Comprueba el rechazo cuando el tiempo límite es cero.

    Configura un supervisor con decisión afirmativa,
    pero solicita autorización con un tiempo límite
    de cero segundos.

    Verificaciones:
        - La solicitud no obtiene autorización.
        - El resultado es None.

    Este escenario comprueba el comportamiento
    del supervisor ante un plazo sin tiempo disponible.

    No mide tiempos reales de espera ni simula
    una demora mediante temporizadores.
    """

    # Configura un supervisor con aprobación simulada.
    supervisor = SupervisorHumano(
        solicitar_decision=lambda: True,
    )

    # Solicita autorización estableciendo
    # un tiempo límite de cero segundos.
    identificador = supervisor.autorizar_cancelacion(
        numero_solicitud="SOL-12345",
        tiempo_limite_segundos=0,
    )

    # El supervisor no debe conceder la autorización
    # cuando el plazo configurado está agotado.
    assert identificador is None
