"""Pruebas unitarias del verificador estatico de Docker."""

import io
import tempfile
import unittest

from contextlib import redirect_stdout
from pathlib import Path

from verificar_dockerfile import (
    ejecutar,
    leer_archivo,
    obtener_instrucciones,
    verificar_df1,
    verificar_df2,
    verificar_df3,
    verificar_df4,
    verificar_df5,
    verificar_df6,
    verificar_df7,
)


class TestFuncionesAuxiliares(unittest.TestCase):
    """Comprueba la lectura y procesamiento de archivos."""

    def test_lectura_archivo_existente(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "Dockerfile"

            ruta.write_text(
                "FROM python:3.13.10-slim",
                encoding="utf-8",
            )

            self.assertEqual(
                leer_archivo(ruta),
                "FROM python:3.13.10-slim",
            )

    def test_lectura_archivo_inexistente(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "Dockerfile"

            self.assertIsNone(leer_archivo(ruta))

    def test_lectura_archivo_con_bom(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "Dockerfile"

            ruta.write_text(
                "FROM python:3.13.10-slim",
                encoding="utf-8-sig",
            )

            self.assertEqual(
                leer_archivo(ruta),
                "FROM python:3.13.10-slim",
            )

    def test_ignora_comentarios_y_lineas_vacias(self):
        contenido = (
            "# Comentario\n"
            "\n"
            "FROM python:3.13.10-slim\n"
            "USER vyops\n"
        )

        self.assertEqual(
            obtener_instrucciones(contenido),
            [
                ("FROM", "python:3.13.10-slim"),
                ("USER", "vyops"),
            ],
        )

    def test_procesa_instrucciones_multilinea(self):
        contenido = (
            "ENV APP_MODE=dev \\\n"
            "    APP_PORT=8000\n"
        )

        instrucciones = obtener_instrucciones(contenido)

        self.assertEqual(len(instrucciones), 1)
        self.assertEqual(instrucciones[0][0], "ENV")
        self.assertIn("APP_MODE=dev", instrucciones[0][1])
        self.assertIn("APP_PORT=8000", instrucciones[0][1])

    def test_normaliza_nombre_de_instruccion(self):
        self.assertEqual(
            obtener_instrucciones("from python:3.13.10-slim"),
            [("FROM", "python:3.13.10-slim")],
        )

class TestImagenBase(unittest.TestCase):
    """Comprueba la deteccion de imagenes base versionadas."""

    def test_imagen_versionada(self):
        casos = (
            "FROM python:3.13.10-slim",
            "FROM python:3.12.10-slim",
            "FROM localhost:5000/python:3.13",
            "FROM python@sha256:" + "a" * 64,
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df1(
                    obtener_instrucciones(contenido)
                )

                self.assertTrue(aprobado)

    def test_imagen_sin_version_valida(self):
        casos = (
            "FROM python",
            "FROM python:latest",
            "FROM python:",
            "FROM python:${VERSION}",
            "FROM localhost:5000/python",
            "FROM",
            "",
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df1(
                    obtener_instrucciones(contenido)
                )

                self.assertFalse(aprobado)


class TestOrdenCapas(unittest.TestCase):
    """Comprueba el orden de instalacion y copia del codigo."""

    def test_orden_correcto(self):
        contenido = (
            "COPY requirements.txt .\n"
            "RUN pip install -r requirements.txt\n"
            "COPY . .\n"
        )

        aprobado, _ = verificar_df2(
            obtener_instrucciones(contenido)
        )

        self.assertTrue(aprobado)

    def test_orden_incorrecto(self):
        contenido = (
            "COPY . .\n"
            "COPY requirements.txt .\n"
            "RUN pip install -r requirements.txt\n"
        )

        aprobado, _ = verificar_df2(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)

    def test_falta_copia_dependencias(self):
        contenido = (
            "RUN pip install -r requirements.txt\n"
            "COPY . .\n"
        )

        aprobado, _ = verificar_df2(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)

    def test_falta_instalacion_dependencias(self):
        contenido = (
            "COPY requirements.txt .\n"
            "COPY . .\n"
        )

        aprobado, _ = verificar_df2(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)

    def test_falta_copia_codigo(self):
        contenido = (
            "COPY requirements.txt .\n"
            "RUN pip install -r requirements.txt\n"
        )

        aprobado, _ = verificar_df2(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)

class TestEscuchaHTTP(unittest.TestCase):
    """Comprueba la configuracion de escucha HTTP."""

    def test_configuraciones_validas(self):
        casos = (
            'CMD ["uvicorn", "servicio.main:app", "--host", "0.0.0.0"]',
            "CMD uvicorn servicio.main:app --host 0.0.0.0",
            "CMD uvicorn servicio.main:app --host=0.0.0.0",
            'ENTRYPOINT ["uvicorn", "servicio.main:app", "--host", "0.0.0.0"]',
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df3(
                    obtener_instrucciones(contenido)
                )

                self.assertTrue(aprobado)

    def test_configuraciones_invalidas(self):
        casos = (
            "CMD uvicorn servicio.main:app --host 127.0.0.1",
            "CMD uvicorn servicio.main:app",
            "CMD uvicorn servicio.main:app --host 0.0.0.01",
            'CMD ["echo", "0.0.0.0"]',
            "EXPOSE 8000",
            "",
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df3(
                    obtener_instrucciones(contenido)
                )

                self.assertFalse(aprobado)

    def test_utiliza_ultimo_cmd(self):
        contenido = (
            "CMD uvicorn servicio.main:app --host 0.0.0.0\n"
            "CMD uvicorn servicio.main:app --host 127.0.0.1\n"
        )

        aprobado, _ = verificar_df3(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)

class TestUsuarioEjecucion(unittest.TestCase):
    """Comprueba la declaracion de un usuario distinto de root."""

    def test_usuarios_validos(self):
        casos = (
            "USER vyops",
            "USER 10001",
            "USER vyops:vyops",
            "USER 10001:10001",
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df4(
                    obtener_instrucciones(contenido)
                )

                self.assertTrue(aprobado)

    def test_usuarios_invalidos(self):
        casos = (
            "USER root",
            "USER ROOT",
            "USER 0",
            "USER 00",
            "USER root:root",
            "USER 0:0",
            "USER 0:10001",
            "USER ${USUARIO}",
            "USER",
            "",
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df4(
                    obtener_instrucciones(contenido)
                )

                self.assertFalse(aprobado)

    def test_cambio_final_a_root(self):
        contenido = (
            "USER vyops\n"
            "USER root\n"
        )

        aprobado, _ = verificar_df4(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)

    def test_cambio_final_a_usuario_no_root(self):
        contenido = (
            "USER root\n"
            "USER vyops\n"
        )

        aprobado, _ = verificar_df4(
            obtener_instrucciones(contenido)
        )

        self.assertTrue(aprobado)

class TestVariablesSensibles(unittest.TestCase):
    """Comprueba la deteccion de variables potencialmente sensibles."""

    def test_variables_permitidas(self):
        casos = (
            "ENV PYTHONUNBUFFERED=1",
            "ENV VYOPS_VECTORSTORE_DIR=/data/vectorstore",
            "ENV VYOPS_REGISTROS_DIR=/data/registros",
            "ARG VERSION=3.13.10",
            'ENV APP_NAME="VyOps Municipal"',
            "ENV APP_MODE=dev APP_PORT=8000",
            "",
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df5(
                    obtener_instrucciones(contenido)
                )

                self.assertTrue(aprobado)

    def test_variables_sensibles(self):
        casos = (
            "ENV GEMINI_API_KEY=valor_ficticio",
            "ARG GEMINI_API_KEY",
            "ARG API_TOKEN=valor_ficticio",
            "ENV DATABASE_PASSWORD=valor_ficticio",
            "ENV APP_SECRET=valor_ficticio",
            "ENV api_key=valor_ficticio",
            "ENV GEMINI_API_KEY valor_ficticio",
            "ENV APP_MODE=dev API_TOKEN=valor_ficticio",
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df5(
                    obtener_instrucciones(contenido)
                )

                self.assertFalse(aprobado)

    def test_detecta_variables_multilinea(self):
        contenido = (
            "ENV APP_MODE=dev \\\n"
            "    GEMINI_API_KEY=valor_ficticio\n"
        )

        aprobado, evidencia = verificar_df5(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)
        self.assertIn("GEMINI_API_KEY", evidencia)

    def test_no_expone_valores_sensibles(self):
        contenido = (
            "ENV GEMINI_API_KEY=credencial_ficticia_123"
        )

        aprobado, evidencia = verificar_df5(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)
        self.assertIn("GEMINI_API_KEY", evidencia)
        self.assertNotIn("credencial_ficticia_123", evidencia)

    def test_instruccion_mal_formada(self):
        contenido = 'ENV APP_NAME="sin_cierre'

        aprobado, _ = verificar_df5(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)

    def test_instruccion_sin_argumentos(self):
        for contenido in ("ENV", "ARG"):
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df5(
                    obtener_instrucciones(contenido)
                )

                self.assertFalse(aprobado)

class TestExclusionesDockerignore(unittest.TestCase):
    """Comprueba las exclusiones obligatorias de Docker."""

    def test_exclusiones_completas(self):
        contenido = ".env\n.git\n.venv\n"

        aprobado, _ = verificar_df6(contenido)

        self.assertTrue(aprobado)

    def test_exclusiones_incompletas(self):
        casos = (
            ".git\n.venv\n",
            ".env\n.venv\n",
            ".env\n.git\n",
            "",
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df6(contenido)

                self.assertFalse(aprobado)

    def test_archivo_inexistente(self):
        aprobado, _ = verificar_df6(None)

        self.assertFalse(aprobado)

    def test_ignora_comentarios(self):
        contenido = (
            "# .env\n"
            ".git\n"
            ".venv\n"
        )

        aprobado, _ = verificar_df6(contenido)

        self.assertFalse(aprobado)

    def test_exclusion_revertida(self):
        contenido = (
            ".env\n"
            ".git\n"
            ".venv\n"
            "!.env\n"
        )

        aprobado, evidencia = verificar_df6(contenido)

        self.assertFalse(aprobado)
        self.assertIn(".env", evidencia)

    def test_exclusion_restaurada(self):
        contenido = (
            ".env\n"
            ".git\n"
            ".venv\n"
            "!.env\n"
            ".env\n"
        )

        aprobado, _ = verificar_df6(contenido)

        self.assertTrue(aprobado)

    def test_normaliza_rutas_simples(self):
        contenido = (
            "./.env\n"
            "/.git/\n"
            ".venv/\n"
        )

        aprobado, _ = verificar_df6(contenido)

        self.assertTrue(aprobado)

class TestHealthcheck(unittest.TestCase):
    """Comprueba la declaracion de un healthcheck habilitado."""

    def test_healthcheck_valido(self):
        casos = (
            "HEALTHCHECK CMD python verificar.py",
            "HEALTHCHECK --interval=5s CMD python verificar.py",
            'HEALTHCHECK CMD ["python", "verificar.py"]',
            (
                "HEALTHCHECK --interval=5s "
                "--timeout=3s --retries=3 "
                "CMD python verificar.py"
            ),
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df7(
                    obtener_instrucciones(contenido)
                )

                self.assertTrue(aprobado)

    def test_healthcheck_invalido(self):
        casos = (
            "HEALTHCHECK NONE",
            "HEALTHCHECK none",
            "HEALTHCHECK CMD",
            "HEALTHCHECK",
            "HEALTHCHECK --interval=5s",
            "EXPOSE 8000",
            "",
        )

        for contenido in casos:
            with self.subTest(contenido=contenido):
                aprobado, _ = verificar_df7(
                    obtener_instrucciones(contenido)
                )

                self.assertFalse(aprobado)

    def test_healthcheck_deshabilitado_al_final(self):
        contenido = (
            "HEALTHCHECK CMD python verificar.py\n"
            "HEALTHCHECK NONE\n"
        )

        aprobado, _ = verificar_df7(
            obtener_instrucciones(contenido)
        )

        self.assertFalse(aprobado)

    def test_healthcheck_habilitado_al_final(self):
        contenido = (
            "HEALTHCHECK NONE\n"
            "HEALTHCHECK CMD python verificar.py\n"
        )

        aprobado, _ = verificar_df7(
            obtener_instrucciones(contenido)
        )

        self.assertTrue(aprobado)

class TestOrquestador(unittest.TestCase):
    """Comprueba la ejecucion integral del verificador estatico."""

    def setUp(self):
        """Prepara una configuracion Docker aislada y temporal."""

        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)

        self.directorio = Path(temporal.name)
        self.dockerfile = self.directorio / "Dockerfile"
        self.dockerignore = self.directorio / ".dockerignore"

        self.contenido_valido = (
            "FROM python:3.13.10-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt .\n"
            "RUN pip install -r requirements.txt\n"
            "COPY . .\n"
            "USER vyops\n"
            "HEALTHCHECK CMD python verificar.py\n"
            "CMD uvicorn servicio.main:app --host 0.0.0.0\n"
        )

        self.dockerfile.write_text(
            self.contenido_valido,
            encoding="utf-8",
        )

        self.dockerignore.write_text(
            ".env\n.git\n.venv\n",
            encoding="utf-8",
        )

    def ejecutar_verificador(self):
        """Captura el codigo de salida y la evidencia generada."""

        salida = io.StringIO()

        with redirect_stdout(salida):
            codigo = ejecutar(self.directorio)

        return codigo, salida.getvalue()

    def test_configuracion_correcta(self):
        codigo, salida = self.ejecutar_verificador()

        self.assertEqual(codigo, 0)
        self.assertIn("7 de 7 comprobaciones cumplidas", salida)
        self.assertIn("RESULTADO: PASS", salida)

        for numero in range(1, 8):
            self.assertIn(f"PASA DF-{numero}", salida)

    def test_configuracion_con_usuario_root(self):
        contenido = self.contenido_valido.replace(
            "USER vyops",
            "USER root",
        )

        self.dockerfile.write_text(
            contenido,
            encoding="utf-8",
        )

        codigo, salida = self.ejecutar_verificador()

        self.assertEqual(codigo, 1)
        self.assertIn("FALLA DF-4", salida)
        self.assertIn("6 de 7 comprobaciones cumplidas", salida)
        self.assertIn("RESULTADO: FAIL", salida)

    def test_configuracion_con_multiples_fallos(self):
        contenido = (
            self.contenido_valido
            .replace("python:3.13.10-slim", "python:latest")
            .replace("USER vyops", "USER root")
            .replace(
                "HEALTHCHECK CMD python verificar.py",
                "HEALTHCHECK NONE",
            )
        )

        self.dockerfile.write_text(
            contenido,
            encoding="utf-8",
        )

        codigo, salida = self.ejecutar_verificador()

        self.assertEqual(codigo, 1)
        self.assertIn("FALLA DF-1", salida)
        self.assertIn("FALLA DF-4", salida)
        self.assertIn("FALLA DF-7", salida)
        self.assertIn("4 de 7 comprobaciones cumplidas", salida)
        self.assertIn("RESULTADO: FAIL", salida)

    def test_dockerfile_inexistente(self):
        self.dockerfile.unlink()

        codigo, salida = self.ejecutar_verificador()

        self.assertEqual(codigo, 1)
        self.assertIn(
            "No existe el archivo Dockerfile",
            salida,
        )

    def test_dockerignore_inexistente(self):
        self.dockerignore.unlink()

        codigo, salida = self.ejecutar_verificador()

        self.assertEqual(codigo, 1)
        self.assertIn("FALLA DF-6", salida)
        self.assertIn("6 de 7 comprobaciones cumplidas", salida)

    def test_no_expone_credenciales_en_salida(self):
        contenido = (
            self.contenido_valido
            + "\nENV GEMINI_API_KEY=credencial_ficticia_123\n"
        )

        self.dockerfile.write_text(
            contenido,
            encoding="utf-8",
        )

        codigo, salida = self.ejecutar_verificador()

        self.assertEqual(codigo, 1)
        self.assertIn("FALLA DF-5", salida)
        self.assertIn("GEMINI_API_KEY", salida)
        self.assertNotIn("credencial_ficticia_123", salida)

    def test_archivo_con_codificacion_invalida(self):
        self.dockerfile.write_bytes(b"\xff\xfe\xff")

        codigo, salida = self.ejecutar_verificador()

        self.assertEqual(codigo, 1)
        self.assertIn(
            "No fue posible leer los archivos",
            salida,
        )


if __name__ == "__main__":
    unittest.main()