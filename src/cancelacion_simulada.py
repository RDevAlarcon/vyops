
"""Operación municipal ficticia con supervisión humana.

Este módulo implementa una cancelación simulada
de solicitudes municipales dentro de VyOps.

Su objetivo es demostrar cómo una operación sensible
puede quedar condicionada a una autorización humana
externa al agente de inteligencia artificial.

El flujo contempla las siguientes validaciones:

    1. Verificar que el número de solicitud no esté vacío.
    2. Comprobar que exista un identificador de autorización.
    3. Solicitar al supervisor la verificación y el consumo
       de la autorización.
    4. Bloquear la operación cuando la autorización
       sea inválida, esté vencida o haya sido consumida.
    5. Devolver un resultado simulado cuando
       la autorización sea válida.

La función utiliza SupervisorHumano para verificar
que la autorización corresponda a la solicitud indicada.

El consumo de la autorización permite evitar
su reutilización, según las reglas implementadas
por el supervisor.

IMPORTANTE:
    Este módulo no cancela solicitudes reales.

    No modifica expedientes municipales,
    bases de datos ni sistemas externos.

    La operación únicamente devuelve un resultado
    que representa una cancelación ficticia autorizada.
"""

# ============================================================
# 1. DEPENDENCIAS
# ============================================================

# Componente responsable de verificar y consumir
# las autorizaciones humanas de operaciones sensibles.
from src.supervisor_humano import SupervisorHumano


# ============================================================
# 2. CANCELACIÓN MUNICIPAL SIMULADA
# ============================================================

def cancelar_solicitud_simulada(
    numero_solicitud: str,
    supervisor: SupervisorHumano,
    identificador_autorizacion: str | None,
) -> dict[str, str]:
    """Simula una cancelación solo con autorización válida.

    Evalúa las condiciones necesarias para representar
    una cancelación ficticia de una solicitud municipal.

    Args:
        numero_solicitud:
            Identificador de la solicitud municipal
            sobre la que se desea simular la cancelación.

        supervisor:
            Instancia de SupervisorHumano encargada
            de verificar y consumir la autorización.

        identificador_autorizacion:
            Identificador de una autorización humana
            previamente registrada.

            Puede ser None cuando no existe
            una autorización disponible.

    Returns:
        dict[str, str]:
            Diccionario con el resultado de la operación.

            Posibles estados:

            - rechazada:
              El número de solicitud está vacío
              o contiene únicamente espacios.

            - bloqueada:
              No existe una autorización humana
              o la autorización no supera la verificación.

            - simulada:
              La autorización fue validada y consumida
              correctamente por el supervisor.

            Según el resultado, el diccionario incluye
            los campos estado, motivo, numero_solicitud
            o mensaje.

    Flujo de seguridad:
        La función valida primero el identificador
        de la solicitud y la presencia de autorización.

        Posteriormente delega la verificación
        y el consumo en SupervisorHumano.

        La operación solo alcanza el estado simulada
        cuando verificar_y_consumir() devuelve True.

    Esta función no ejecuta una cancelación real.
    """

    # --------------------------------------------------------
    # 2.1. VALIDACIÓN DEL NÚMERO DE SOLICITUD
    # --------------------------------------------------------

    # Rechaza identificadores vacíos o compuestos
    # únicamente por espacios en blanco.
    #
    # Esta validación se realiza antes de consultar
    # al supervisor para evitar procesar solicitudes
    # sin un identificador válido.
    if not numero_solicitud.strip():
        return {
            "estado": "rechazada",
            "motivo": "Número de solicitud vacío.",
        }

    # --------------------------------------------------------
    # 2.2. VALIDACIÓN DE LA AUTORIZACIÓN HUMANA
    # --------------------------------------------------------

    # Bloquea la operación cuando no se proporciona
    # un identificador de autorización.
    #
    # La ausencia de autorización impide continuar
    # hacia la simulación de cancelación.
    if identificador_autorizacion is None:
        return {
            "estado": "bloqueada",
            "motivo": "Falta autorización humana.",
        }

    # --------------------------------------------------------
    # 2.3. VERIFICACIÓN Y CONSUMO DE LA AUTORIZACIÓN
    # --------------------------------------------------------

    # Solicita al supervisor que valide la autorización
    # para el número de solicitud indicado.
    #
    # El método verificar_y_consumir() centraliza
    # las reglas de validez y consumo de autorizaciones.
    autorizada = supervisor.verificar_y_consumir(
        identificador=identificador_autorizacion,
        numero_solicitud=numero_solicitud,
    )

    # --------------------------------------------------------
    # 2.4. BLOQUEO DE AUTORIZACIONES NO VÁLIDAS
    # --------------------------------------------------------

    # Impide continuar cuando el supervisor
    # no autoriza la operación.
    #
    # El mensaje contempla autorizaciones inválidas,
    # vencidas o previamente consumidas.
    if not autorizada:
        return {
            "estado": "bloqueada",
            "motivo": "Autorización inválida, vencida o consumida.",
        }

    # --------------------------------------------------------
    # 2.5. RESULTADO DE LA CANCELACIÓN SIMULADA
    # --------------------------------------------------------

    # Devuelve un resultado ficticio cuando
    # todas las validaciones anteriores se cumplen.
    #
    # Este retorno no modifica el estado real
    # de ninguna solicitud municipal.
    return {
        "estado": "simulada",
        "numero_solicitud": numero_solicitud,
        "mensaje": "Cancelación ficticia autorizada y simulada.",
    }
