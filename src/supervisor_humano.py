
"""Supervisión humana externa al agente VyOps.

Este módulo implementa una interfaz de supervisión humana
para operaciones sensibles ejecutadas por el agente municipal.

Su objetivo es separar la decisión de autorización
de la ejecución de las herramientas del agente.

Actualmente, la supervisión se aplica a la herramienta
de cancelación simulada de solicitudes municipales.

Responsabilidades principales:

    1. Recibir una función externa de decisión humana.
    2. Solicitar aprobación para una cancelación concreta.
    3. Asociar la autorización a una solicitud específica.
    4. Aplicar un tiempo máximo de autorización.
    5. Registrar autorizaciones aprobadas y vigentes.
    6. Generar identificadores opacos de autorización.
    7. Verificar y consumir autorizaciones de un solo uso.

Dependencias internas:

    RegistroAutorizaciones:
        Administra el almacenamiento temporal
        y el consumo de autorizaciones.

    solicitar_autorizacion:
        Solicita una decisión humana y construye
        una autorización con alcance y vencimiento.

Flujo general:

    Solicitud de cancelación
        |
        v
    Decisión humana externa
        |
        v
    Validación de autorización
        |
        v
    Registro de autorización
        |
        v
    Entrega de identificador
        |
        v
    Verificación y consumo

Política de autorización:

    Una autorización está asociada a:

        - La herramienta cancelar_solicitud_simulada.
        - Un número de solicitud específico.
        - Una decisión humana favorable.
        - Un plazo de vigencia.

    Las autorizaciones rechazadas o vencidas
    no se registran mediante autorizar_cancelacion().

    Una autorización registrada puede consumirse
    una sola vez mediante verificar_y_consumir().

IMPORTANTE:
    Este módulo no cancela solicitudes directamente.

    Su responsabilidad consiste en administrar
    la aprobación necesaria para permitir
    que otro componente ejecute la operación.

    La decisión humana se obtiene mediante
    una función externa proporcionada
    durante la inicialización del supervisor.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Callable permite definir el tipo de función
# que proporcionará la decisión humana.
from collections.abc import Callable

# Componentes de seguridad definidos
# en el módulo de límites de autonomía.
#
# RegistroAutorizaciones:
#     Almacena y consume autorizaciones de un solo uso.
#
# solicitar_autorizacion:
#     Obtiene una decisión humana y genera
#     una autorización temporal.
from src.limites_autonomia import (
    RegistroAutorizaciones,
    solicitar_autorizacion,
)


# ============================================================
# 2. SUPERVISOR HUMANO
# ============================================================

class SupervisorHumano:
    """Gestiona decisiones humanas para operaciones simuladas.

    Proporciona una interfaz para solicitar,
    registrar y consumir autorizaciones humanas
    asociadas a cancelaciones simuladas.

    Attributes:
        _solicitar_decision:
            Función externa que devuelve
            la decisión humana de aprobación.

        _registro:
            Registro de autorizaciones temporales
            de un solo uso.

    Métodos disponibles:

        autorizar_cancelacion():
            Solicita aprobación humana
            para una solicitud determinada.

        verificar_y_consumir():
            Comprueba y consume una autorización
            previamente registrada.

    Cada instancia de SupervisorHumano crea
    su propio RegistroAutorizaciones.

    Por lo tanto, las autorizaciones registradas
    en una instancia no se comparten automáticamente
    con otras instancias del supervisor.
    """

    # --------------------------------------------------------
    # 2.1. INICIALIZACIÓN DEL SUPERVISOR
    # --------------------------------------------------------

    def __init__(
        self,
        solicitar_decision: Callable[[], bool],
    ) -> None:
        """Inicializa el supervisor y su registro de autorizaciones.

        Args:
            solicitar_decision:
                Función sin argumentos que devuelve
                una decisión booleana.

                True representa una aprobación humana.

                False representa una decisión desfavorable.

        La función de decisión se almacena
        para utilizarse posteriormente
        cuando se solicite una autorización.

        También se crea un registro independiente
        de autorizaciones temporales.

        La inicialización no solicita
        ninguna decisión humana.
        """

        # Conserva la función externa utilizada
        # para solicitar decisiones humanas.
        self._solicitar_decision = solicitar_decision

        # Crea el registro de autorizaciones
        # asociado a esta instancia del supervisor.
        self._registro = RegistroAutorizaciones()

    # --------------------------------------------------------
    # 3. SOLICITUD DE AUTORIZACIÓN PARA CANCELACIÓN
    # --------------------------------------------------------

    def autorizar_cancelacion(
        self,
        numero_solicitud: str,
        tiempo_limite_segundos: float = 300,
    ) -> str | None:
        """Solicita aprobación para una cancelación concreta.

        Args:
            numero_solicitud:
                Identificador de la solicitud municipal
                cuya cancelación simulada se desea autorizar.

            tiempo_limite_segundos:
                Tiempo máximo permitido para obtener
                la decisión humana.

                Su valor predeterminado es 300 segundos.

        Returns:
            str | None:
                Identificador opaco de autorización
                cuando la decisión es favorable
                y la autorización sigue vigente.

                None cuando la autorización
                no supera las validaciones.

        Flujo:
            1. Solicitar una decisión humana.
            2. Generar una autorización temporal.
            3. Verificar aprobación, herramienta,
               solicitud y vigencia.
            4. Registrar la autorización válida.
            5. Devolver su identificador.

        La autorización queda asociada exclusivamente
        a la herramienta cancelar_solicitud_simulada.

        El identificador devuelto puede utilizarse
        posteriormente para verificar y consumir
        la autorización.

        Esta función no ejecuta la cancelación.
        """

        # ----------------------------------------------------
        # 3.1. SOLICITUD DE DECISIÓN HUMANA
        # ----------------------------------------------------

        # Solicita una autorización vinculada
        # a la herramienta de cancelación simulada
        # y al número de solicitud recibido.
        #
        # La función externa de decisión
        # se ejecuta respetando el plazo configurado.
        autorizacion = solicitar_autorizacion(
            herramienta="cancelar_solicitud_simulada",
            identificador_solicitud=numero_solicitud,
            solicitar_decision=self._solicitar_decision,
            tiempo_limite_segundos=tiempo_limite_segundos,
        )

        # ----------------------------------------------------
        # 3.2. VALIDACIÓN DE LA AUTORIZACIÓN
        # ----------------------------------------------------

        # Comprueba que la autorización:
        #
        # - Haya sido aprobada.
        # - Corresponda a la herramienta esperada.
        # - Esté asociada a la solicitud indicada.
        # - No haya alcanzado su vencimiento.
        if not autorizacion.es_valida(
            "cancelar_solicitud_simulada",
            numero_solicitud,
        ):
            # No registra autorizaciones inválidas.
            #
            # None indica que no se obtuvo
            # una autorización utilizable.
            return None

        # ----------------------------------------------------
        # 3.3. REGISTRO DE LA AUTORIZACIÓN
        # ----------------------------------------------------

        # Almacena la autorización válida
        # y devuelve su identificador opaco.
        #
        # Este identificador permite intentar
        # consumir la autorización posteriormente.
        return self._registro.registrar(autorizacion)

    # --------------------------------------------------------
    # 4. VERIFICACIÓN Y CONSUMO DE AUTORIZACIONES
    # --------------------------------------------------------

    def verificar_y_consumir(
        self,
        identificador: str,
        numero_solicitud: str,
    ) -> bool:
        """Consume una autorización para la solicitud indicada.

        Args:
            identificador:
                Identificador opaco de la autorización
                previamente registrada.

            numero_solicitud:
                Número de la solicitud municipal
                cuya cancelación se desea ejecutar.

        Returns:
            bool:
                True cuando la autorización existe
                y cumple las condiciones de:

                - Aprobación humana.
                - Herramienta autorizada.
                - Coincidencia de solicitud.
                - Vigencia temporal.

                False cuando alguna condición falla.

        El método delega la verificación
        en RegistroAutorizaciones.consumir().

        La autorización se elimina del registro
        durante el intento de consumo.

        Por lo tanto, un mismo identificador
        no puede utilizarse nuevamente.

        IMPORTANTE:
            La autorización se consume incluso
            cuando posteriormente resulta inválida.

            Este método verifica el permiso,
            pero no ejecuta la cancelación.
        """

        # ----------------------------------------------------
        # 4.1. CONSUMO DE LA AUTORIZACIÓN
        # ----------------------------------------------------

        # Solicita al registro recuperar y eliminar
        # la autorización identificada.
        #
        # El registro comprueba que la autorización
        # corresponda a cancelar_solicitud_simulada
        # y al número de solicitud indicado.
        #
        # Devuelve True solo si la autorización
        # consumida supera todas las validaciones.
        return self._registro.consumir(
            identificador=identificador,
            herramienta="cancelar_solicitud_simulada",
            identificador_solicitud=numero_solicitud,
        )
