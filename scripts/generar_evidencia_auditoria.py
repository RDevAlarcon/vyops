
"""Genera evidencia ficticia de auditoría para VyOps."""

from pathlib import Path

from langchain_core.agents import AgentAction

from src.trazas_agente import (
    marcar_repeticiones_sospechosas,
    registrar_traza,
)


def main() -> None:
    """Registra dos escenarios simulados de autonomía."""
    ruta = Path("evidencias/trazas_bloque_23.jsonl")

    if ruta.exists():
        raise FileExistsError(
            "La evidencia ya existe. No se sobrescribirá."
        )

    consulta = AgentAction(
        tool="consultar_estado_solicitud",
        tool_input={"numero_solicitud": "SOL-12345"},
        log="Consulta ficticia de bajo riesgo.",
    )

    registrar_traza(
        session_id="demo-bajo-riesgo",
        entrada="Consulta el estado de SOL-12345.",
        resultado={
            "output": "La solicitud ficticia está en revisión.",
            "intermediate_steps": [
                (consulta, {"estado": "en_revision"}),
            ],
        },
        ruta_archivo=ruta,
    )

    cancelacion = AgentAction(
        tool="cancelar_solicitud_simulada",
        tool_input={"numero_solicitud": "SOL-12345"},
        log="Cancelación ficticia de alto riesgo.",
    )

    registrar_traza(
        session_id="demo-alto-riesgo",
        entrada="Cancela la solicitud ficticia SOL-12345.",
        resultado={
            "output": "Cancelación bloqueada por falta de aprobación.",
            "intermediate_steps": [
                (cancelacion, {"estado": "bloqueada"}),
            ],
        },
        ruta_archivo=ruta,
    )

    alertas = marcar_repeticiones_sospechosas(ruta)

    print(f"Evidencia generada: {ruta}")
    print("Ejecuciones registradas: 2")
    print(f"Alertas por repeticiones: {len(alertas)}")


if __name__ == "__main__":
    main()
