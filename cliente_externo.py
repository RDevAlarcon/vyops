"""Cliente externo de pruebas HTTP para VyOps.

Ejecuta la matriz compartida de casos contra un servidor
en funcionamiento y comunica el resultado mediante códigos
de salida compatibles con procesos automatizados.
"""

import sys

import httpx2

from casos import CASOS, ejecutar_caso


URL_PREDETERMINADA = "http://127.0.0.1:8000"


def main(base_url: str) -> bool:
    """Comprueba la disponibilidad y ejecuta los casos HTTP."""

    print("=== CLIENTE EXTERNO DE PRUEBAS VYOPS ===")
    print(f"Servicio: {base_url}\n")

    # Comprobar la disponibilidad antes de ejecutar la matriz.
    with httpx2.Client(
        base_url=base_url,
        timeout=5.0,
    ) as cliente:

        respuesta = cliente.get("/salud")

        if respuesta.status_code != 200:
            print(
                "FALLA - Servicio no disponible: "
                f"HTTP {respuesta.status_code}"
            )
            return False

    print("PASA - Servicio disponible\n")

    cumplidos = 0

    # Ejecutar todos los casos mediante peticiones HTTP reales.
    with httpx2.Client(
        base_url=base_url,
        timeout=10.0,
    ) as cliente:

        for caso in CASOS:
            try:
                ok, estado, _ = ejecutar_caso(cliente, caso)

                cumplidos += int(ok)

                resultado = "PASA" if ok else "FALLA"

                print(
                    f"{resultado} {caso['id']} "
                    f"{caso['metodo']} {caso['ruta']} | "
                    f"Esperado: {caso['estado']} | "
                    f"Obtenido: {estado}"
                )

            except httpx2.RequestError:
                print(
                    f"FALLA {caso['id']} - "
                    "Error de comunicación HTTP."
                )

    total = len(CASOS)
    exito = cumplidos == total

    print(f"\n{cumplidos} de {total} casos cumplidos")
    print(f"RESULTADO: {'PASS' if exito else 'FAIL'}")

    return exito


if __name__ == "__main__":
    base_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else URL_PREDETERMINADA
    )

    try:
        exito = main(base_url)

    except httpx2.ConnectError:
        print(
            "FALLA - No fue posible conectar con el servicio. "
            "Comprueba que Uvicorn esté en ejecución."
        )
        exito = False

    except httpx2.RequestError:
        print(
            "FALLA - Error de comunicación con el servicio."
        )
        exito = False

    raise SystemExit(0 if exito else 1)