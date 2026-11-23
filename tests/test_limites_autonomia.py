
"""Pruebas de los límites de autonomía de VyOps.

Este módulo verifica los mecanismos de supervisión humana
implementados en src.limites_autonomia.

Los límites de autonomía permiten distinguir entre
herramientas de consulta y operaciones que requieren
una autorización explícita antes de ejecutarse.

Las pruebas cubren seis áreas:

    1. Clasificación de herramientas según su nivel de riesgo.
    2. Obtención y validación de decisiones humanas.
    3. Vigencia y alcance de las autorizaciones.
    4. Solicitud de autorizaciones con tiempo limitado.
    5. Registro y consumo único de autorizaciones.
    6. Protección frente al consumo concurrente.

Los escenarios comprueban que una autorización
no pueda utilizarse cuando:

    - La decisión humana fue rechazada.
    - La respuesta no es el booleano True.
    - Se supera el tiempo de aprobación.
    - La autorización está vencida.
    - Se intenta utilizar para otra solicitud.
    - Se intenta utilizar para otra herramienta.
    - Ya fue consumida anteriormente.
    - Su identificador no está registrado.

Se utilizan herramientas y solicitudes simuladas.
No se ejecutan cancelaciones municipales reales.

La prueba de concurrencia utiliza ThreadPoolExecutor
para verificar el consumo único de una autorización
cuando varios hilos intentan utilizarla.

Estas pruebas verifican comportamientos específicos
de los límites de autonomía, pero no constituyen
una auditoría completa de seguridad o autorización.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Framework utilizado para parametrizar pruebas.
import pytest

# Permite simular decisiones humanas que tardan
# más que el plazo máximo permitido.
import time

# Reloj monotónico utilizado para definir
# vencimientos relativos de autorizaciones.
from time import monotonic

# Permite ejecutar intentos concurrentes
# de consumo de una misma autorización.
from concurrent.futures import ThreadPoolExecutor

# Componentes responsables de aplicar
# los límites de autonomía de VyOps.
from src.limites_autonomia import (
    NivelRiesgo,
    RIESGOS_HERRAMIENTAS,
    requiere_aprobacion,
    esperar_aprobacion,
    AutorizacionHumana,
    solicitar_autorizacion,
    RegistroAutorizaciones,
)


# ============================================================
# 2. CLASIFICACIÓN DE HERRAMIENTAS POR NIVEL DE RIESGO
# ============================================================

@pytest.mark.parametrize(
    "herramienta",
    [
        "calcular_metricas",
        "consultar_documentacion",
        "analizar_datos",
        "consultar_estado_solicitud",
    ],
)
def test_herramientas_bajo_riesgo_no_requieren_aprobacion(
    herramienta: str,
) -> None:
    """Verifica que las herramientas de consulta sean de bajo riesgo.

    Evalúa cuatro herramientas registradas:

        - calcular_metricas.
        - consultar_documentacion.
        - analizar_datos.
        - consultar_estado_solicitud.

    Args:
        herramienta (str):
            Nombre de la herramienta proporcionado
            por cada caso parametrizado.

    Verificaciones:
        - La herramienta está clasificada como BAJO.
        - No requiere aprobación humana previa.

    La prueba comprueba la configuración de riesgo
    definida para estas herramientas específicas.
    """

    # Comprueba la clasificación registrada
    # para la herramienta evaluada.
    assert RIESGOS_HERRAMIENTAS[herramienta] == NivelRiesgo.BAJO

    # Las herramientas clasificadas como bajo riesgo
    # no deben requerir aprobación humana.
    assert requiere_aprobacion(herramienta) is False


def test_herramienta_alto_riesgo_requiere_aprobacion() -> None:
    """Verifica que una cancelación requiera supervisión humana.

    Utiliza la herramienta cancelar_solicitud_simulada.

    Verificaciones:
        - Su clasificación corresponde a ALTO.
        - La función requiere_aprobacion() devuelve True.

    Este escenario comprueba que una operación
    potencialmente modificadora no quede habilitada
    automáticamente por la clasificación de riesgos.
    """

    # Identifica la herramienta de cancelación simulada.
    herramienta = "cancelar_solicitud_simulada"

    # Comprueba su clasificación de alto riesgo.
    assert RIESGOS_HERRAMIENTAS[herramienta] == NivelRiesgo.ALTO

    # Verifica que requiera aprobación humana.
    assert requiere_aprobacion(herramienta) is True


def test_herramienta_desconocida_requiere_aprobacion() -> None:
    """Impide autorizar automáticamente herramientas desconocidas.

    Evalúa una herramienta que no corresponde
    a las herramientas conocidas del escenario.

    Verificación:
        - requiere_aprobacion() devuelve True.

    Este comportamiento aplica un criterio restrictivo
    cuando no existe una clasificación explícita
    que permita operar sin supervisión.
    """

    # Una herramienta desconocida no debe obtener
    # autorización automática.
    assert requiere_aprobacion("herramienta_desconocida") is True


# ============================================================
# 3. DECISIONES HUMANAS Y TIEMPOS DE ESPERA
# ============================================================

def test_aprobacion_humana_aceptada() -> None:
    """Permite continuar cuando existe aprobación explícita.

    Simula una decisión humana mediante una función
    que devuelve el booleano True.

    Verificación:
        - esperar_aprobacion() devuelve True.
    """

    # Simula una aprobación humana afirmativa.
    assert esperar_aprobacion(lambda: True) is True


def test_aprobacion_humana_rechazada() -> None:
    """Bloquea una acción rechazada por el supervisor.

    Simula una decisión humana negativa.

    Verificación:
        - esperar_aprobacion() devuelve False.
    """

    # Una decisión negativa no debe habilitar la acción.
    assert esperar_aprobacion(lambda: False) is False


def test_aprobacion_humana_invalida() -> None:
    """No acepta valores distintos del booleano True.

    Simula una respuesta textual afirmativa
    en lugar de una aprobación booleana.

    Verificación:
        - La cadena "sí" no se interpreta como aprobación.

    Esta prueba comprueba que una respuesta textual
    no sustituya la decisión explícita esperada.
    """

    # La cadena "sí" no debe considerarse
    # equivalente al booleano True.
    assert esperar_aprobacion(lambda: "sí") is False


def test_aprobacion_humana_timeout() -> None:
    """Rechaza cuando la aprobación supera el tiempo permitido.

    Simula una decisión que tarda 0.2 segundos,
    mientras que el plazo permitido es de 0.01 segundos.

    Verificación:
        - esperar_aprobacion() devuelve False.

    La prueba comprueba que una decisión afirmativa
    recibida fuera del plazo no habilite la operación.
    """

    def decision_lenta() -> bool:
        """Simula una aprobación que tarda en completarse.

        Returns:
            bool:
                True después de la espera simulada.
        """

        # Introduce un retraso superior al tiempo límite.
        time.sleep(0.2)
        return True

    # Solicita una decisión con un plazo inferior
    # al tiempo que tarda la función simulada.
    resultado = esperar_aprobacion(
        solicitar_decision=decision_lenta,
        tiempo_limite_segundos=0.01,
    )

    # La aprobación tardía debe rechazarse.
    assert resultado is False


def test_aprobacion_humana_tiempo_invalido() -> None:
    """Rechaza un plazo de aprobación no positivo.

    Solicita una aprobación con un tiempo límite
    igual a cero segundos.

    Verificación:
        - esperar_aprobacion() devuelve False.

    Este escenario comprueba el tratamiento
    de un plazo que no permite esperar una decisión.
    """

    # Aunque la decisión simulada sea afirmativa,
    # el plazo cero debe provocar el rechazo.
    assert esperar_aprobacion(
        solicitar_decision=lambda: True,
        tiempo_limite_segundos=0,
    ) is False


# ============================================================
# 4. VIGENCIA Y ALCANCE DE LAS AUTORIZACIONES
# ============================================================

def test_autorizacion_vigente_es_valida() -> None:
    """Acepta una autorización vigente para la acción correcta.

    Construye una autorización aprobada con vencimiento
    establecido 60 segundos después del instante actual.

    Verificaciones:
        - La herramienta coincide con la autorizada.
        - El identificador de solicitud coincide.
        - La autorización está aprobada y vigente.
        - es_valida() devuelve True.
    """

    # Crea una autorización aprobada y vigente
    # para una solicitud municipal específica.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    # Comprueba que la autorización sea válida
    # para la herramienta y solicitud originales.
    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is True


def test_autorizacion_vencida_es_rechazada() -> None:
    """Impide utilizar una autorización cuyo plazo terminó.

    Construye una autorización aprobada cuyo vencimiento
    se encuentra un segundo antes del instante actual.

    Verificación:
        - es_valida() devuelve False.

    La aprobación humana no debe ser suficiente
    cuando la autorización ya está vencida.
    """

    # Crea una autorización cuyo plazo
    # ya finalizó.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() - 1,
    )

    # Comprueba que una autorización vencida
    # no pueda utilizarse.
    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_autorizacion_no_sirve_para_otra_solicitud() -> None:
    """Impide reutilizar la autorización en otra solicitud.

    Crea una autorización aprobada para SOL-12345
    e intenta validarla para SOL-99999.

    Verificación:
        - es_valida() devuelve False.

    Este escenario comprueba que la autorización
    esté vinculada al identificador de solicitud
    para el cual fue emitida.
    """

    # Autoriza una operación sobre SOL-12345.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    # Intenta utilizar la autorización
    # sobre una solicitud diferente.
    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-99999",
    ) is False


def test_autorizacion_no_sirve_para_otra_herramienta() -> None:
    """Impide utilizar la autorización en otra operación.

    Construye una autorización para cancelar
    una solicitud simulada.

    Posteriormente intenta utilizarla
    para modificar una solicitud.

    Verificación:
        - es_valida() devuelve False.

    Esta prueba comprueba la vinculación
    de la autorización con una herramienta concreta.
    """

    # Autoriza específicamente la cancelación simulada.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    # Una autorización de cancelación no debe
    # habilitar una herramienta diferente.
    assert autorizacion.es_valida(
        "modificar_solicitud",
        "SOL-12345",
    ) is False


def test_autorizacion_rechazada_no_es_valida() -> None:
    """Impide ejecutar acciones sin aprobación explícita.

    Construye una autorización vigente
    cuyo campo aprobada es False.

    Verificación:
        - es_valida() devuelve False.

    La coincidencia de herramienta, solicitud
    y plazo no debe sustituir la aprobación humana.
    """

    # Crea una autorización vigente,
    # pero expresamente no aprobada.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=False,
        vence_en=monotonic() + 60,
    )

    # Comprueba que la falta de aprobación
    # invalide la autorización.
    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


# ============================================================
# 5. SOLICITUD Y EMISIÓN DE AUTORIZACIONES
# ============================================================

def test_solicitar_autorizacion_aprobada() -> None:
    """Genera una autorización válida tras una aprobación explícita.

    Solicita autorización para una cancelación simulada
    utilizando una función que devuelve True.

    Verificación:
        - La autorización generada es válida
          para la herramienta y solicitud indicadas.
    """

    # Solicita una autorización con decisión afirmativa
    # y un tiempo límite de 60 segundos.
    autorizacion = solicitar_autorizacion(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        solicitar_decision=lambda: True,
        tiempo_limite_segundos=60,
    )

    # Comprueba que la autorización emitida
    # sea válida para la operación solicitada.
    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is True


def test_solicitar_autorizacion_rechazada() -> None:
    """No autoriza una operación rechazada.

    Solicita una autorización utilizando
    una decisión humana simulada negativa.

    Verificación:
        - La autorización resultante no es válida.
    """

    # Simula el rechazo explícito de la operación.
    autorizacion = solicitar_autorizacion(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        solicitar_decision=lambda: False,
        tiempo_limite_segundos=60,
    )

    # La autorización rechazada no debe
    # habilitar la operación.
    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_solicitar_autorizacion_timeout() -> None:
    """No autoriza una aprobación recibida fuera del plazo.

    Simula una decisión que tarda 0.2 segundos,
    con un plazo máximo de 0.01 segundos.

    Verificación:
        - La autorización resultante no es válida.

    Esta prueba comprueba el tratamiento
    de una aprobación tardía durante
    la solicitud de autorización.
    """

    def decision_lenta() -> bool:
        """Simula una decisión afirmativa tardía.

        Returns:
            bool:
                True después de la espera simulada.
        """

        # Introduce un retraso superior al plazo permitido.
        time.sleep(0.2)
        return True

    # Solicita autorización con un tiempo límite
    # inferior al retraso de la decisión simulada.
    autorizacion = solicitar_autorizacion(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        solicitar_decision=decision_lenta,
        tiempo_limite_segundos=0.01,
    )

    # La aprobación tardía no debe generar
    # una autorización utilizable.
    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_solicitar_autorizacion_no_acepta_respuesta_invalida() -> None:
    """Rechaza respuestas que no sean el booleano True.

    Simula una decisión que devuelve la cadena
    "aprobado" en lugar del booleano True.

    Verificación:
        - La autorización generada no es válida.

    Esta prueba comprueba que un texto afirmativo
    no sea interpretado como autorización explícita.
    """

    # Solicita autorización utilizando
    # una respuesta textual no válida.
    autorizacion = solicitar_autorizacion(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        solicitar_decision=lambda: "aprobado",
        tiempo_limite_segundos=60,
    )

    # Comprueba que la autorización sea rechazada.
    assert autorizacion.es_valida(
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


# ============================================================
# 6. REGISTRO Y CONSUMO DE AUTORIZACIONES
# ============================================================

def test_registro_permite_consumir_autorizacion() -> None:
    """Permite consumir una autorización válida una sola vez.

    Crea un registro y almacena una autorización
    aprobada y vigente.

    Verificación:
        - El primer consumo devuelve True.

    Este escenario comprueba el uso inicial
    de una autorización registrada.
    """

    # Crea un registro independiente de autorizaciones.
    registro = RegistroAutorizaciones()

    # Construye una autorización aprobada y vigente.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    # Registra la autorización y obtiene su identificador.
    identificador = registro.registrar(autorizacion)

    # Comprueba que el primer consumo
    # de la autorización sea aceptado.
    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is True


def test_registro_impide_reutilizar_autorizacion() -> None:
    """Rechaza una autorización que ya fue consumida.

    Registra una autorización válida e intenta
    consumirla dos veces para la misma operación.

    Verificaciones:
        - El primer consumo devuelve True.
        - El segundo consumo devuelve False.

    Esta prueba comprueba que una autorización
    registrada no pueda reutilizarse después
    de haber sido consumida.
    """

    # Crea el registro de autorizaciones.
    registro = RegistroAutorizaciones()

    # Construye una autorización aprobada y vigente.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    # Registra la autorización.
    identificador = registro.registrar(autorizacion)

    # El primer consumo debe ser aceptado.
    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is True

    # El segundo consumo debe ser rechazado,
    # aunque coincidan la herramienta y la solicitud.
    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_registro_rechaza_identificador_desconocido() -> None:
    """Rechaza identificadores que no están registrados.

    Crea un registro vacío e intenta consumir
    una autorización utilizando un identificador
    que no fue registrado previamente.

    Verificación:
        - consumir() devuelve False.
    """

    # Crea un registro sin autorizaciones.
    registro = RegistroAutorizaciones()

    # Intenta consumir una autorización inexistente.
    assert registro.consumir(
        "identificador_inexistente",
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


def test_registro_rechaza_otra_solicitud() -> None:
    """Impide utilizar una autorización para otra solicitud.

    Registra una autorización emitida para SOL-12345
    e intenta consumirla utilizando SOL-99999.

    Verificación:
        - consumir() devuelve False.

    Este escenario comprueba que el registro
    respete la solicitud vinculada a la autorización.
    """

    # Crea el registro de autorizaciones.
    registro = RegistroAutorizaciones()

    # Construye una autorización para SOL-12345.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    # Registra la autorización original.
    identificador = registro.registrar(autorizacion)

    # Intenta consumirla para una solicitud diferente.
    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-99999",
    ) is False


def test_registro_rechaza_autorizacion_vencida() -> None:
    """Impide consumir una autorización fuera de plazo.

    Registra una autorización aprobada
    cuyo vencimiento ya ocurrió.

    Verificación:
        - consumir() devuelve False.

    El registro no debe aceptar una autorización
    únicamente por encontrarse almacenada.
    También debe respetar su vigencia.
    """

    # Crea el registro de autorizaciones.
    registro = RegistroAutorizaciones()

    # Construye una autorización vencida.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() - 1,
    )

    # Registra la autorización vencida.
    identificador = registro.registrar(autorizacion)

    # Comprueba que el registro rechace su consumo.
    assert registro.consumir(
        identificador,
        "cancelar_solicitud_simulada",
        "SOL-12345",
    ) is False


# ============================================================
# 7. CONSUMO CONCURRENTE DE AUTORIZACIONES
# ============================================================

def test_registro_impide_consumo_concurrente() -> None:
    """Permite consumir una autorización solo una vez entre varios hilos.

    Construye una autorización aprobada y vigente,
    la registra y ejecuta diez intentos de consumo
    mediante ThreadPoolExecutor.

    Todos los intentos utilizan:

        - El mismo identificador de autorización.
        - La misma herramienta.
        - La misma solicitud municipal.

    Verificaciones:
        - Exactamente un intento devuelve True.
        - Los otros nueve intentos devuelven False.

    Esta prueba comprueba que el registro
    evite múltiples consumos exitosos
    en este escenario de concurrencia.

    No verifica por sí sola el comportamiento
    entre múltiples procesos o servidores.
    """

    # Crea un registro compartido
    # por todos los hilos de la prueba.
    registro = RegistroAutorizaciones()

    # Construye una autorización aprobada y vigente.
    autorizacion = AutorizacionHumana(
        herramienta="cancelar_solicitud_simulada",
        identificador_solicitud="SOL-12345",
        aprobada=True,
        vence_en=monotonic() + 60,
    )

    # Registra la autorización que todos
    # los hilos intentarán consumir.
    identificador = registro.registrar(autorizacion)

    def intentar_consumir() -> bool:
        """Intenta consumir la autorización compartida.

        Returns:
            bool:
                True si el registro acepta el consumo.
                False si la autorización ya no puede utilizarse.

        Todos los hilos ejecutan esta función
        sobre el mismo registro e identificador.
        """

        # Intenta consumir la autorización registrada.
        return registro.consumir(
            identificador,
            "cancelar_solicitud_simulada",
            "SOL-12345",
        )

    # Ejecuta diez intentos utilizando
    # un máximo de diez hilos trabajadores.
    with ThreadPoolExecutor(max_workers=10) as ejecutor:
        resultados = list(
            ejecutor.map(
                lambda _: intentar_consumir(),
                range(10),
            )
        )

    # Solo uno de los intentos debe conseguir
    # consumir la autorización.
    assert resultados.count(True) == 1

    # Los nueve intentos restantes deben ser rechazados.
    assert resultados.count(False) == 9
