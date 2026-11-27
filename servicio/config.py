"""Configuración del servicio mediante variables de entorno."""

import os


class ConfiguracionIncompleta(Exception):
    """Falta una variable de entorno obligatoria."""


def entorno() -> str:
    """Devuelve el entorno de ejecución del servicio."""
    return os.environ.get("ENTORNO", "desarrollo")


def modelo_configurado() -> bool:
    """Indica si existe una clave sin revelar su valor."""
    return bool(os.environ.get("GEMINI_API_KEY"))


def clave_modelo() -> str:
    """Obtiene la clave únicamente cuando se necesita."""
    clave = os.environ.get("GEMINI_API_KEY")

    if not clave:
        raise ConfiguracionIncompleta(
            "Falta la variable de entorno GEMINI_API_KEY."
        )

    return clave