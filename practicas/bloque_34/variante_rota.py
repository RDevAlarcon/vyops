"""
Bloque 34: variante defectuosa del servicio simulado.

Comprueba que los criterios de aceptación detecten
incumplimientos en el contrato de respuesta del servicio.
"""

import criterios_demo as cd


def consultar_roto(pregunta: str) -> dict:
    """
    Simula un servicio que incumple su contrato de respuesta.

    Devuelve una respuesta fija y omite deliberadamente
    el campo fuentes.

    Args:
        pregunta: Consulta recibida por el servicio.

    Returns:
        Diccionario incompleto con el campo respuesta.
    """

    return {
        "respuesta": "Tienes 30 dias desde la compra para devolver."
    }


if __name__ == "__main__":
    # Conserva la referencia a la implementación original.
    consultar_original = cd.consultar

    try:
        # Sustituye temporalmente el servicio correcto.
        cd.consultar = consultar_roto

        # Ejecuta los mismos criterios sin modificarlos.
        cd.ejecutar(cd.CRITERIOS)

    finally:
        # Restaura la implementación original del servicio.
        cd.consultar = consultar_original