"""Verifica las dependencias necesarias para el servicio HTTP de VyOps."""

from importlib.metadata import PackageNotFoundError, version

DEPENDENCIAS = {
    "fastapi": "0.143.0",
    "uvicorn": "0.54.0",
    "pydantic": "2.14.3",
    "httpx2": "2.16.0",
}


def main() -> int:
    """Comprueba las versiones y las importaciones requeridas."""
    for paquete, esperada in DEPENDENCIAS.items():
        try:
            instalada = version(paquete)
        except PackageNotFoundError:
            print(f"Falta la dependencia: {paquete}")
            return 1

        print(f"{paquete}: {instalada}")

        if instalada != esperada:
            print(f"Version esperada: {esperada}")
            return 1

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from pydantic import BaseModel, Field

    print("Importaciones correctas")
    print("RESULTADO: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())