
"""Pruebas del bloqueo multiplataforma de indexación de VyOps.

Utiliza directorios temporales y bloqueos reales del sistema
operativo, sin modificar el índice vectorial del proyecto.

No requiere Gemini ni realiza llamadas a servicios externos.
"""

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.bloqueo_indexacion import (
    IndexacionEnCursoError,
    bloqueo_indexacion,
)


class TestBloqueoIndexacion(unittest.TestCase):
    """Verifica las garantías del mecanismo de coordinación."""

    def setUp(self):
        """Prepara un directorio aislado para cada prueba."""

        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)

        self.directorio = Path(temporal.name)

    def test_crea_directorio_y_archivo(self):
        """Comprueba la creación del archivo de coordinación."""

        directorio = self.directorio / "indice"

        with bloqueo_indexacion(directorio):
            self.assertTrue(directorio.is_dir())

            self.assertTrue(
                (directorio / ".vyops_indexacion.lock").is_file()
            )

    def test_rechaza_segundo_bloqueo(self):
        """Impide adquirir dos bloqueos sobre el mismo archivo."""

        with bloqueo_indexacion(self.directorio):
            with self.assertRaises(IndexacionEnCursoError):
                with bloqueo_indexacion(self.directorio):
                    self.fail("Se adquirió un segundo bloqueo.")

    def test_libera_bloqueo_despues_de_excepcion(self):
        """Permite reutilizar el bloqueo tras una excepción."""

        with self.assertRaisesRegex(RuntimeError, "Fallo simulado"):
            with bloqueo_indexacion(self.directorio):
                raise RuntimeError("Fallo simulado")

        with bloqueo_indexacion(self.directorio):
            self.assertTrue(True)

    def test_directorios_independientes(self):
        """Permite operaciones sobre directorios diferentes."""

        primero = self.directorio / "primero"
        segundo = self.directorio / "segundo"

        with bloqueo_indexacion(primero):
            with bloqueo_indexacion(segundo):
                self.assertTrue(primero.is_dir())
                self.assertTrue(segundo.is_dir())

    def test_archivo_no_crece(self):
        """Evita agregar bytes en cada adquisición del bloqueo."""

        for _ in range(10):
            with bloqueo_indexacion(self.directorio):
                pass

        archivo = self.directorio / ".vyops_indexacion.lock"

        self.assertEqual(archivo.stat().st_size, 0)

    def test_exclusion_entre_procesos(self):
        """Comprueba que dos procesos no compartan el bloqueo."""

        codigo = """
import sys
from pathlib import Path

from src.bloqueo_indexacion import (
    bloqueo_indexacion,
    IndexacionEnCursoError,
)

try:
    with bloqueo_indexacion(Path(sys.argv[1])):
        print("ADQUIRIDO")
except IndexacionEnCursoError:
    print("BLOQUEADO")
    sys.exit(10)
"""

        comando = [
            sys.executable,
            "-c",
            codigo,
            str(self.directorio),
        ]

        # El proceso principal conserva el bloqueo mientras
        # el proceso secundario intenta adquirirlo.
        with bloqueo_indexacion(self.directorio):
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.assertEqual(
                resultado.returncode,
                10,
                resultado.stderr,
            )

            self.assertIn("BLOQUEADO", resultado.stdout)

        # Después de liberarlo, el proceso secundario
        # debe poder adquirir el mismo bloqueo.
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=60,
        )

        self.assertEqual(
            resultado.returncode,
            0,
            resultado.stderr,
        )

        self.assertIn("ADQUIRIDO", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
