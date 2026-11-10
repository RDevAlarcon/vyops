
"""Operación municipal ficticia con supervisión humana."""

from src.supervisor_humano import SupervisorHumano


def cancelar_solicitud_simulada(
    numero_solicitud: str,
    supervisor: SupervisorHumano,
    identificador_autorizacion: str | None,
) -> dict[str, str]:
    """Simula una cancelación solo con autorización válida."""
    if not numero_solicitud.strip():
        return {
            "estado": "rechazada",
            "motivo": "Número de solicitud vacío.",
        }

    if identificador_autorizacion is None:
        return {
            "estado": "bloqueada",
            "motivo": "Falta autorización humana.",
        }

    autorizada = supervisor.verificar_y_consumir(
        identificador=identificador_autorizacion,
        numero_solicitud=numero_solicitud,
    )

    if not autorizada:
        return {
            "estado": "bloqueada",
            "motivo": "Autorización inválida, vencida o consumida.",
        }

    return {
        "estado": "simulada",
        "numero_solicitud": numero_solicitud,
        "mensaje": "Cancelación ficticia autorizada y simulada.",
    }
