
"""Herramienta de cancelación ficticia con supervisión externa.

Este módulo integra el mecanismo de cancelación simulada
de VyOps con el sistema de herramientas de LangChain.

Su propósito es permitir que un agente solicite
la simulación de una cancelación municipal sin
concederle autonomía para aprobar la operación.

Componentes principales:

    1. ArgumentosCancelacion:
       Modelo Pydantic que define los argumentos
       aceptados por la herramienta.

    2. construir_herramienta_cancelacion:
       Función que construye una herramienta LangChain
       asociada a un supervisor humano.

    3. herramienta_cancelacion:
       Función interna registrada mediante @tool,
       encargada de solicitar la autorización
       y delegar la cancelación simulada.

Flujo general:

    Agente LangChain
        |
        v
    Herramienta de cancelación
        |
        v
    Validación de argumentos con Pydantic
        |
        v
    Solicitud de autorización humana
        |
        v
    SupervisorHumano
        |
        v
    cancelar_solicitud_simulada()
        |
        v
    Resultado de la operación ficticia

La decisión humana se obtiene mediante una función
externa proporcionada al construir la herramienta.

El agente puede solicitar la operación, pero no
determina directamente su autorización.

IMPORTANTE:
    Este módulo no cancela solicitudes municipales reales.

    No modifica expedientes, bases de datos
    ni sistemas administrativos externos.

    Su finalidad es demostrar un mecanismo
    de supervisión humana sobre operaciones sensibles.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Permite declarar el tipo de la función externa
# que obtiene la decisión de aprobación humana.
from collections.abc import Callable

# BaseTool representa una herramienta de LangChain.
# El decorador tool registra funciones como herramientas
# disponibles para un agente.
from langchain_core.tools import BaseTool, tool

# BaseModel define el esquema de argumentos.
# Field permite establecer restricciones y descripciones.
from pydantic import BaseModel, Field

# Función que ejecuta la lógica de cancelación ficticia
# después de verificar la autorización correspondiente.
from src.cancelacion_simulada import cancelar_solicitud_simulada

# Componente que administra las autorizaciones humanas.
from src.supervisor_humano import SupervisorHumano


# ============================================================
# 2. ESQUEMA DE ARGUMENTOS DE CANCELACIÓN
# ============================================================

class ArgumentosCancelacion(BaseModel):
    """Define los argumentos que puede proporcionar el agente.

    Este modelo Pydantic establece la estructura
    de entrada de la herramienta de cancelación.

    Attributes:
        numero_solicitud:
            Identificador de la solicitud municipal
            ficticia que se desea cancelar.

    Validaciones:
        - El valor debe ser una cadena de texto.
        - Debe contener al menos un carácter.

    La descripción del campo también proporciona
    información sobre el argumento esperado
    por la herramienta LangChain.

    Este esquema no incluye identificadores
    de autorización ni decisiones humanas.

    La autorización se gestiona mediante
    SupervisorHumano, fuera de los argumentos
    que puede proporcionar el agente.
    """

    # Identificador de la solicitud ficticia.
    #
    # min_length=1 impide recibir una cadena vacía.
    #
    # La validación de espacios en blanco corresponde
    # a la función cancelar_solicitud_simulada().
    numero_solicitud: str = Field(
        min_length=1,
        description="Número de solicitud municipal ficticia.",
    )


# ============================================================
# 3. CONSTRUCCIÓN DE LA HERRAMIENTA SUPERVISADA
# ============================================================

def construir_herramienta_cancelacion(
    solicitar_decision: Callable[[], bool],
) -> BaseTool:
    """Construye una herramienta con aprobación externa.

    Crea una instancia de SupervisorHumano y registra
    una herramienta de LangChain para solicitar
    cancelaciones ficticias.

    Args:
        solicitar_decision:
            Función externa que solicita una decisión
            de aprobación humana.

            No recibe argumentos y devuelve un booleano:

            - True: decisión favorable.
            - False: decisión desfavorable.

    Returns:
        BaseTool:
            Herramienta LangChain registrada con el nombre
            cancelar_solicitud_simulada.

            Utiliza ArgumentosCancelacion como esquema
            de validación de entrada.

    Flujo de ejecución de la herramienta:

        1. Recibir el número de solicitud.
        2. Solicitar autorización al supervisor.
        3. Recuperar el identificador de autorización.
        4. Delegar la operación a cancelar_solicitud_simulada().
        5. Devolver el resultado de la simulación.

    La instancia del supervisor se crea una vez
    por cada llamada al constructor.

    La herramienta interna conserva una referencia
    a esa instancia mediante el cierre de la función.

    La autorización humana no se solicita
    durante la construcción de la herramienta,
    sino cuando esta se ejecuta.
    """

    # --------------------------------------------------------
    # 3.1. CREACIÓN DEL SUPERVISOR HUMANO
    # --------------------------------------------------------

    # Construye el supervisor utilizando la función
    # externa que obtiene la decisión humana.
    #
    # El supervisor administra las autorizaciones
    # utilizadas por las cancelaciones simuladas.
    supervisor = SupervisorHumano(
        solicitar_decision=solicitar_decision,
    )

    # --------------------------------------------------------
    # 3.2. DEFINICIÓN DE LA HERRAMIENTA LANGCHAIN
    # --------------------------------------------------------

    # Registra la función interna como herramienta.
    #
    # El nombre identifica la operación ante el agente.
    #
    # args_schema utiliza el modelo Pydantic
    # para validar los argumentos proporcionados.
    @tool(
        "cancelar_solicitud_simulada",
        args_schema=ArgumentosCancelacion,
    )
    def herramienta_cancelacion(
        numero_solicitud: str,
    ) -> dict[str, str]:
        """Simula cancelar una solicitud con aprobación humana.

        Args:
            numero_solicitud:
                Identificador de la solicitud municipal
                ficticia proporcionado por el agente.

        Returns:
            dict[str, str]:
                Resultado generado por
                cancelar_solicitud_simulada().

                El resultado puede indicar:

                - rechazada: número de solicitud vacío.
                - bloqueada: autorización ausente o inválida.
                - simulada: cancelación ficticia autorizada.

        La función no acepta una decisión de aprobación
        proporcionada directamente por el agente.

        Solicita la autorización mediante SupervisorHumano
        y posteriormente delega la verificación
        y la operación simulada.
        """

        # ----------------------------------------------------
        # 3.3. SOLICITUD DE AUTORIZACIÓN
        # ----------------------------------------------------

        # Solicita al supervisor una autorización
        # asociada al número de solicitud indicado.
        #
        # El supervisor utiliza el mecanismo externo
        # de decisión humana configurado al construirse.
        autorizacion = supervisor.autorizar_cancelacion(
            numero_solicitud=numero_solicitud,
        )

        # ----------------------------------------------------
        # 3.4. EJECUCIÓN DE LA CANCELACIÓN SIMULADA
        # ----------------------------------------------------

        # Delega la operación a la función especializada.
        #
        # Esta función verifica y consume la autorización
        # antes de devolver el resultado ficticio.
        return cancelar_solicitud_simulada(
            numero_solicitud=numero_solicitud,
            supervisor=supervisor,
            identificador_autorizacion=autorizacion,
        )

    # --------------------------------------------------------
    # 3.5. DEVOLUCIÓN DE LA HERRAMIENTA
    # --------------------------------------------------------

    # Devuelve la herramienta registrada y lista
    # para incorporarse a un agente LangChain.
    #
    # Su ejecución posterior utilizará el supervisor
    # creado durante la construcción.
    return herramienta_cancelacion
