
import ast
import hashlib
import subprocess
from datetime import datetime, timezone
import difflib

VERSIONES = {
    "v1": {
        "commit": "7c3c204",
        "nota": "Prompt municipal original con citas.",
    },
    "v2": {
        "commit": "04706ff",
        "nota": "Incorpora protección contra inyección de prompt.",
    },
}


def obtener_prompt_historico(commit):
    """Recupera el texto del prompt desde una versión de Git."""
    contenido = subprocess.check_output(
        ["git", "show", f"{commit}:recuperacion.py"]
    ).decode("utf-8")

    arbol = ast.parse(contenido)

    for nodo in arbol.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == "construir_prompt":
            for instruccion in ast.walk(nodo):
                if isinstance(instruccion, ast.JoinedStr):
                    return ast.get_source_segment(contenido, instruccion)

    raise ValueError("No se encontró el prompt histórico.")


def calcular_huella(texto):
    """Calcula la huella SHA-256 del texto del prompt."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def registrar_version(version, autor="Ricardo Alarcón"):
    datos = VERSIONES[version]
    prompt = obtener_prompt_historico(datos["commit"])

    return {
        "version": version,
        "commit": datos["commit"],
        "autor": autor,
        "fecha_registro": datetime.now(timezone.utc).isoformat(),
        "nota_cambio": datos["nota"],
        "sha256": calcular_huella(prompt),
        "prompt": prompt,
        "modelo": "gemini-3.5-flash-lite",
        "parametros": {
            "temperatura": None,
            "max_tokens": None,
        },
    }

class RegistroDePrompts:
    """Gestiona las versiones registradas de un prompt."""

    def __init__(self):
        self.versiones = []

    def agregar(self, registro):
        if any(
            version["version"] == registro["version"]
            for version in self.versiones
        ):
            raise ValueError("La versión ya está registrada.")

        self.versiones.append(registro)

    def ultima(self):
        if not self.versiones:
            raise ValueError("No existen versiones registradas.")

        return self.versiones[-1]

    

if __name__ == "__main__":
    for version in VERSIONES:
        registro = registrar_version(version)

        print(f"\nVersión: {registro['version']}")
        print(f"Commit: {registro['commit']}")
        print(f"Autor: {registro['autor']}")
        print(f"SHA-256: {registro['sha256']}")
        print(f"Cambio: {registro['nota_cambio']}")
        print(f"Modelo: {registro['modelo']}")
        print(f"Parámetros: {registro['parametros']}")
    
    print("\n=== DIFERENCIAS ENTRE V1 Y V2 ===")

    prompt_v1 = obtener_prompt_historico("7c3c204")
    prompt_v2 = obtener_prompt_historico("04706ff")

    diferencias = difflib.unified_diff(
        prompt_v1.splitlines(),
        prompt_v2.splitlines(),
        fromfile="v1_prompt_original",
        tofile="v2_prompt_protegido",
        lineterm="",
    )

    for linea in diferencias:
        print(linea)

    registro_prompts = RegistroDePrompts()
    registro_prompts.agregar(registrar_version("v1"))
    registro_prompts.agregar(registrar_version("v2"))

    ultima_version = registro_prompts.ultima()

    print("\n=== ÚLTIMA VERSIÓN REGISTRADA ===")
    print("Versión:", ultima_version["version"])
    print("SHA-256:", ultima_version["sha256"][:12])
    print("Cambio:", ultima_version["nota_cambio"])