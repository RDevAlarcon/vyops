
"""Clasificación de riesgos y límites de autonomía de VyOps.

Este módulo define mecanismos de seguridad para controlar
las acciones que puede ejecutar un agente de inteligencia
artificial dentro del proyecto VyOps.

Su propósito es impedir que determinadas operaciones
sensibles se ejecuten sin una autorización humana válida.

Responsabilidades principales:

    1. Clasificar herramientas según su nivel de riesgo.
    2. Determinar cuáles requieren aprobación humana.
    3. Solicitar decisiones humanas con tiempo límite.
    4. Generar autorizaciones temporales.
    5. Asociar autorizaciones a acciones específicas.
    6. Registrar autorizaciones mediante identificadores opacos.
    7. Consumir autorizaciones una sola vez.
    8. Proteger el registro frente a accesos concurrentes.

Niveles de riesgo:

    BAJO:
        Operaciones consideradas de bajo riesgo
        dentro de la clasificación configurada.

    MEDIO:
        Nivel disponible para clasificaciones intermedias.

    ALTO:
        Operaciones que requieren aprobación humana.

Política para herramientas desconocidas:

    Toda herramienta que no aparezca en el registro
    de riesgos requiere aprobación humana.

Esta decisión evita conceder autorización implícita
a herramientas nuevas o no clasificadas.

Las autorizaciones se limitan mediante:

    - Nombre de la herramienta.
    - Identificador de la solicitud.
    - Decisión de aprobación.
    - Tiempo de vencimiento.
    - Consumo de un solo uso.

El tiempo de vigencia se calcula utilizando
un reloj monotónico para evitar depender
de cambios en la hora del sistema.

IMPORTANTE:
    Este módulo administra autorizaciones
    y decisiones de seguridad.

    No ejecuta directamente operaciones municipales
    ni modifica sistemas externos.

    La ejecución de una acción corresponde
    a los componentes que utilizan estas autorizaciones.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite definir clases de datos con atributos inmutables.
from dataclasses import dataclass

# Reloj monotónico utilizado para medir plazos
# sin depender de cambios en la hora del sistema.
from time import monotonic

# Permite representar niveles de riesgo enumerados.
from enum import Enum

# Define el tipo de función utilizada para solicitar
# una decisión humana externa.
from collections.abc import Callable

# Ejecuta la solicitud de decisión en un hilo separado
# y permite establecer un tiempo máximo de espera.
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Protege las operaciones concurrentes sobre
# el registro compartido de autorizaciones.
from threading import Lock

# Genera identificadores únicos para las autorizaciones.
from uuid import uuid4


# ============================================================
# 2. CLASIFICACIÓN DE NIVELES DE RIESGO
# ============================================================

class NivelRiesgo(str, Enum):
    """Niveles de riesgo de las herramientas del agente.

    Define las categorías disponibles para clasificar
    las operaciones ejecutadas mediante herramientas.

    Attributes:
        BAJO:
            Nivel de riesgo bajo.

        MEDIO:
            Nivel de riesgo intermedio.

        ALTO:
            Nivel de riesgo alto.

    La herencia de str permite utilizar valores
    textuales asociados a cada categoría.

    La clasificación se utiliza posteriormente
    para determinar si una herramienta requiere
    aprobación humana.
    """

    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


# ============================================================
# 3. REGISTRO DE RIESGOS DE HERRAMIENTAS
# ============================================================

# Diccionario que relaciona cada herramienta conocida
# con su clasificación de riesgo.
#
# Las herramientas de consulta y análisis incluidas
# actualmente están clasificadas como riesgo bajo.
#
# La cancelación ficticia se clasifica como riesgo alto
# porque representa una operación sensible.
#
# Este registro no concede permisos por sí mismo.
RIESGOS_HERRAMIENTAS: dict[str, NivelRiesgo] = {
    "calcular_metricas": NivelRiesgo.BAJO,
    "consultar_documentacion": NivelRiesgo.BAJO,
    "analizar_datos": NivelRiesgo.BAJO,
    "consultar_estado_solicitud": NivelRiesgo.BAJO,
    "cancelar_solicitud_simulada": NivelRiesgo.ALTO,
}


# ============================================================
# 4. DETERMINACIÓN DE APROBACIÓN HUMANA
# ============================================================

def requiere_aprobacion(herramienta: str) -> bool:
    """Determina si una herramienta necesita aprobación humana.

    Args:
        herramienta:
            Nombre de la herramienta cuya clasificación
            de riesgo se desea consultar.

    Returns:
        bool:
            True cuando la herramienta:

                - Está clasificada como riesgo ALTO.
                - No existe en el registro de riesgos.

            False cuando está clasificada como
            riesgo BAJO o MEDIO.

    Política de seguridad:
        Una herramienta desconocida nunca recibe
        autorización implícita.

        La ausencia de clasificación provoca
        que se exija aprobación humana.

    Esta función solo determina el requisito
    de aprobación; no solicita una decisión.
    """

    # Recupera el nivel de riesgo configurado.
    #
    # get() devuelve None cuando la herramienta
    # no está registrada.
    nivel = RIESGOS_HERRAMIENTAS.get(herramienta)

    # Una herramienta desconocida nunca obtiene autorización implícita.
    if nivel is None:
        return True

    # Las herramientas de riesgo alto requieren aprobación.
    #
    # Con la política actual, los niveles bajo
    # y medio no requieren aprobación humana.
    return nivel == NivelRiesgo.ALTO


# ============================================================
# 5. ESPERA DE UNA DECISIÓN HUMANA
# ============================================================

def esperar_aprobacion(
    solicitar_decision: Callable[[], bool],
    tiempo_limite_segundos: float = 300,
) -> bool:
    """Espera una decisión humana y rechaza si vence el plazo.

    Ejecuta una función externa de decisión humana
    mediante un ThreadPoolExecutor.

    Args:
        solicitar_decision:
            Función sin argumentos que devuelve
            una decisión booleana.

        tiempo_limite_segundos:
            Tiempo máximo de espera, expresado
            en segundos.

            Su valor predeterminado es 300.

    Returns:
        bool:
            True únicamente cuando la función
            devuelve exactamente True dentro
            del tiempo permitido.

            False cuando:

                - El plazo configurado no es positivo.
                - La decisión no es exactamente True.
                - Se supera el tiempo máximo de espera.
                - La ejecución produce una excepción.

    Consideraciones:
        La función utiliza un hilo para esperar
        la decisión sin bloquear indefinidamente
        al llamador.

        shutdown(wait=False, cancel_futures=True)
        evita esperar por la finalización del ejecutor.

        Sin embargo, no interrumpe forzosamente
        una función que ya esté ejecutándose.

    Esta función no genera ni registra autorizaciones.
    """

    # --------------------------------------------------------
    # 5.1. VALIDACIÓN DEL PLAZO
    # --------------------------------------------------------

    # Rechaza inmediatamente los plazos no positivos.
    if tiempo_limite_segundos <= 0:
        return False

    # --------------------------------------------------------
    # 5.2. CREACIÓN DEL EJECUTOR
    # --------------------------------------------------------

    # Crea un ejecutor con un único trabajador.
    #
    # La función externa de decisión se ejecutará
    # dentro de ese hilo.
    ejecutor = ThreadPoolExecutor(max_workers=1)

    try:
        # ----------------------------------------------------
        # 5.3. ENVÍO DE LA SOLICITUD DE DECISIÓN
        # ----------------------------------------------------

        # Envía la función de decisión al ejecutor.
        tarea = ejecutor.submit(solicitar_decision)

        try:
            # ------------------------------------------------
            # 5.4. ESPERA DEL RESULTADO
            # ------------------------------------------------

            # Espera como máximo el tiempo configurado.
            decision = tarea.result(timeout=tiempo_limite_segundos)

            # Solo una aprobación exactamente igual a True
            # se considera favorable.
            return decision is True

        # ----------------------------------------------------
        # 5.5. RECHAZO POR ERROR O TIEMPO AGOTADO
        # ----------------------------------------------------

        # Devuelve False si la espera vence
        # o la función ejecutada genera una excepción.
        except (FutureTimeoutError, Exception):
            return False

    finally:
        # ----------------------------------------------------
        # 5.6. CIERRE DEL EJECUTOR
        # ----------------------------------------------------

        # Solicita el cierre del ejecutor sin esperar
        # a que termine una tarea que ya está en ejecución.
        #
        # Las tareas pendientes que aún puedan cancelarse
        # serán canceladas.
        ejecutor.shutdown(wait=False, cancel_futures=True)


# ============================================================
# 6. REPRESENTACIÓN DE AUTORIZACIONES HUMANAS
# ============================================================

@dataclass(frozen=True)
class AutorizacionHumana:
    """Representa una autorización limitada a una acción concreta.

    La autorización conserva la información necesaria
    para comprobar si una acción específica fue aprobada
    y si todavía se encuentra dentro de su vigencia.

    Attributes:
        herramienta:
            Nombre de la herramienta autorizada.

        identificador_solicitud:
            Identificador de la solicitud a la que
            corresponde la autorización.

        aprobada:
            Indica si se obtuvo una decisión favorable.

        vence_en:
            Instante de vencimiento expresado
            mediante el reloj monotónico.

    La configuración frozen=True impide reasignar
    los atributos de una instancia después
    de su creación.

    La autorización no contiene por sí misma
    un identificador de consumo.

    El control de un solo uso corresponde
    a RegistroAutorizaciones.
    """

    herramienta: str
    identificador_solicitud: str
    aprobada: bool
    vence_en: float

    # --------------------------------------------------------
    # 6.1. VALIDACIÓN DE UNA AUTORIZACIÓN
    # --------------------------------------------------------

    def es_valida(
        self,
        herramienta: str,
        identificador_solicitud: str,
    ) -> bool:
        """Verifica aprobación, alcance y vigencia.

        Args:
            herramienta:
                Nombre de la herramienta que intenta
                utilizar la autorización.

            identificador_solicitud:
                Identificador de la solicitud
                asociada a la operación.

        Returns:
            bool:
                True únicamente cuando:

                1. La autorización está aprobada.
                2. La herramienta coincide exactamente.
                3. La solicitud coincide exactamente.
                4. El plazo de vigencia no ha vencido.

                False cuando alguna condición no se cumple.

        La comparación del vencimiento utiliza monotonic().

        La autorización deja de ser válida cuando
        el tiempo actual alcanza o supera vence_en.

        Este método no consume ni elimina autorizaciones.
        """

        # Todas las condiciones deben cumplirse
        # simultáneamente para considerar válida
        # la autorización.
        return (
            self.aprobada is True
            and self.herramienta == herramienta
            and self.identificador_solicitud == identificador_solicitud
            and monotonic() < self.vence_en
        )


# ============================================================
# 7. SOLICITUD DE AUTORIZACIÓN TEMPORAL
# ============================================================

def solicitar_autorizacion(
    herramienta: str,
    identificador_solicitud: str,
    solicitar_decision: Callable[[], bool],
    tiempo_limite_segundos: float = 300,
) -> AutorizacionHumana:
    """Solicita aprobación y genera una autorización temporal.

    Args:
        herramienta:
            Nombre de la herramienta que requiere
            autorización humana.

        identificador_solicitud:
            Identificador de la solicitud
            sobre la que se ejecutaría la acción.

        solicitar_decision:
            Función externa utilizada para obtener
            la decisión humana.

        tiempo_limite_segundos:
            Plazo máximo para recibir la aprobación.

            El valor predeterminado es 300 segundos.

    Returns:
        AutorizacionHumana:
            Objeto que contiene la herramienta,
            la solicitud, la decisión y el vencimiento.

    Flujo:
        1. Registrar el instante inicial.
        2. Esperar la decisión humana.
        3. Calcular el vencimiento.
        4. Comprobar que la aprobación sigue vigente.
        5. Construir la autorización temporal.

    El vencimiento se calcula desde el instante
    anterior a solicitar la decisión humana.

    Por lo tanto, el tiempo dedicado a esperar
    la aprobación forma parte del plazo total.

    La autorización puede devolverse con
    aprobada=False cuando la decisión es rechazada
    o el plazo ya se encuentra vencido.

    Esta función no registra la autorización
    en RegistroAutorizaciones.
    """

    # --------------------------------------------------------
    # 7.1. REGISTRO DEL INSTANTE INICIAL
    # --------------------------------------------------------

    # Captura el instante anterior a solicitar
    # la decisión humana.
    inicio = monotonic()

    # --------------------------------------------------------
    # 7.2. SOLICITUD DE APROBACIÓN
    # --------------------------------------------------------

    # Ejecuta la función externa de decisión
    # respetando el tiempo máximo configurado.
    aprobada = esperar_aprobacion(
        solicitar_decision=solicitar_decision,
        tiempo_limite_segundos=tiempo_limite_segundos,
    )

    # --------------------------------------------------------
    # 7.3. CÁLCULO DEL VENCIMIENTO
    # --------------------------------------------------------

    # Calcula el instante de expiración.
    #
    # max(0, ...) evita agregar un plazo negativo.
    vence_en = inicio + max(0, tiempo_limite_segundos)

    # --------------------------------------------------------
    # 7.4. CONSTRUCCIÓN DE LA AUTORIZACIÓN
    # --------------------------------------------------------

    # La aprobación solo se conserva cuando:
    #
    # - La decisión humana fue favorable.
    # - El plazo todavía no ha vencido.
    #
    # El objeto mantiene el alcance específico
    # de herramienta y solicitud.
    return AutorizacionHumana(
        herramienta=herramienta,
        identificador_solicitud=identificador_solicitud,
        aprobada=aprobada and monotonic() < vence_en,
        vence_en=vence_en,
    )


# ============================================================
# 8. REGISTRO DE AUTORIZACIONES DE UN SOLO USO
# ============================================================

class RegistroAutorizaciones:
    """Administra autorizaciones temporales de un solo uso.

    Mantiene un registro en memoria de autorizaciones
    asociadas a identificadores únicos.

    Cada autorización puede recuperarse y consumirse
    mediante su identificador.

    El registro utiliza un Lock para proteger
    las operaciones concurrentes de escritura
    y extracción.

    La autorización se elimina del registro
    durante el intento de consumo.

    Esto impide que el mismo identificador
    pueda utilizarse nuevamente.

    Attributes:
        _autorizaciones:
            Diccionario interno que relaciona
            identificadores con autorizaciones.

        _lock:
            Mecanismo de exclusión mutua que protege
            las operaciones sobre el diccionario.

    IMPORTANTE:
        El registro existe únicamente en memoria.

        No implementa persistencia externa
        ni comparte autorizaciones entre procesos.
    """

    # --------------------------------------------------------
    # 8.1. INICIALIZACIÓN DEL REGISTRO
    # --------------------------------------------------------

    def __init__(self) -> None:
        """Inicializa el almacenamiento y el bloqueo de concurrencia.

        Crea un diccionario vacío para almacenar
        las autorizaciones y un Lock para coordinar
        accesos desde distintos hilos.

        No carga autorizaciones desde archivos
        ni desde una base de datos.
        """

        # Diccionario de identificadores y autorizaciones.
        self._autorizaciones: dict[str, AutorizacionHumana] = {}

        # Bloqueo utilizado para proteger accesos concurrentes.
        self._lock = Lock()

    # --------------------------------------------------------
    # 8.2. REGISTRO DE UNA AUTORIZACIÓN
    # --------------------------------------------------------

    def registrar(self, autorizacion: AutorizacionHumana) -> str:
        """Registra una autorización y devuelve un identificador opaco.

        Args:
            autorizacion:
                Objeto AutorizacionHumana que se almacenará
                en el registro interno.

        Returns:
            str:
                Identificador hexadecimal generado
                mediante uuid4().hex.

        El identificador permite recuperar la autorización
        posteriormente sin exponer directamente
        sus atributos internos.

        El registro se realiza dentro de un Lock
        para proteger el diccionario compartido.

        Este método no comprueba si la autorización
        está aprobada o vigente antes de almacenarla.
        """

        # ----------------------------------------------------
        # 8.3. GENERACIÓN DEL IDENTIFICADOR
        # ----------------------------------------------------

        # Genera un identificador UUID aleatorio
        # representado como una cadena hexadecimal.
        identificador = uuid4().hex

        # ----------------------------------------------------
        # 8.4. ALMACENAMIENTO PROTEGIDO
        # ----------------------------------------------------

        # Bloquea temporalmente el acceso concurrente
        # mientras incorpora la autorización.
        with self._lock:
            self._autorizaciones[identificador] = autorizacion

        # Devuelve el identificador asociado al registro.
        return identificador

    # --------------------------------------------------------
    # 8.5. CONSUMO DE UNA AUTORIZACIÓN
    # --------------------------------------------------------

    def consumir(
        self,
        identificador: str,
        herramienta: str,
        identificador_solicitud: str,
    ) -> bool:
        """Valida y consume una autorización de forma atómica.

        Args:
            identificador:
                Identificador opaco de la autorización
                que se desea consumir.

            herramienta:
                Nombre de la herramienta que solicita
                ejecutar la acción.

            identificador_solicitud:
                Identificador de la solicitud asociada
                a la operación.

        Returns:
            bool:
                True cuando la autorización existe
                y supera todas las validaciones.

                False cuando no existe o no cumple
                las condiciones de aprobación,
                alcance y vigencia.

        El método extrae la autorización mediante pop()
        dentro de una sección protegida por Lock.

        La extracción es atómica respecto de otros
        accesos al registro que utilizan el mismo bloqueo.

        Una vez extraída, la autorización no puede
        volver a consumirse mediante ese identificador.

        IMPORTANTE:
            La autorización se elimina incluso
            cuando posteriormente resulta inválida.

            La validación se realiza después
            de liberar el bloqueo.

            El mecanismo garantiza el consumo
            de un solo uso dentro de esta instancia.
        """

        # ----------------------------------------------------
        # 8.6. EXTRACCIÓN ATÓMICA DEL REGISTRO
        # ----------------------------------------------------

        # Protege la extracción frente a otros hilos.
        #
        # pop() recupera y elimina la autorización
        # en una única operación sobre el diccionario.
        with self._lock:
            autorizacion = self._autorizaciones.pop(
                identificador,
                None,
            )

        # ----------------------------------------------------
        # 8.7. VERIFICACIÓN DE EXISTENCIA
        # ----------------------------------------------------

        # Rechaza identificadores inexistentes
        # o que ya fueron consumidos anteriormente.
        if autorizacion is None:
            return False

        # ----------------------------------------------------
        # 8.8. VALIDACIÓN DE LA AUTORIZACIÓN CONSUMIDA
        # ----------------------------------------------------

        # Verifica aprobación, coincidencia de herramienta,
        # coincidencia de solicitud y vigencia temporal.
        #
        # La autorización ya fue retirada del registro,
        # independientemente del resultado.
        return autorizacion.es_valida(
            herramienta,
            identificador_solicitud,
        )
