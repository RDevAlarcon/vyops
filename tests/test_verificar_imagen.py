"""Pruebas unitarias del verificador dinamico de Docker."""

import subprocess
import unittest
import httpx2
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from unittest.mock import MagicMock, call, patch

import verificar_imagen as vi


class TestFuncionesAuxiliares(unittest.TestCase):
    """Verifica las funciones auxiliares sin utilizar Docker real."""

    @patch("verificar_imagen.subprocess.run")
    def test_docker_ejecucion_correcta(self, ejecutar):
        """Devuelve el codigo y la salida de Docker."""

        ejecutar.return_value = subprocess.CompletedProcess(
            args=["docker", "version"],
            returncode=0,
            stdout="Docker disponible\n",
            stderr="",
        )

        codigo, salida = vi.docker("version")

        self.assertEqual(codigo, 0)
        self.assertEqual(salida, "Docker disponible")

        ejecutar.assert_called_once_with(
            ["docker", "version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=vi.TIMEOUT_DOCKER,
            check=False,
        )

    @patch("verificar_imagen.subprocess.run")
    def test_docker_error_de_ejecucion(self, ejecutar):
        """Conserva el codigo de error devuelto por Docker."""

        ejecutar.return_value = subprocess.CompletedProcess(
            args=["docker", "inspect"],
            returncode=1,
            stdout="",
            stderr="Error de inspeccion",
        )

        codigo, salida = vi.docker("inspect")

        self.assertEqual(codigo, 1)
        self.assertEqual(salida, "Error de inspeccion")

    @patch("verificar_imagen.subprocess.run")
    def test_docker_no_disponible(self, ejecutar):
        """Controla la ausencia del ejecutable Docker."""

        ejecutar.side_effect = FileNotFoundError()

        codigo, salida = vi.docker("version")

        self.assertEqual(codigo, 127)
        self.assertIn("no se encuentra disponible", salida)

    @patch("verificar_imagen.subprocess.run")
    def test_docker_timeout(self, ejecutar):
        """Controla el agotamiento del tiempo de espera."""

        ejecutar.side_effect = subprocess.TimeoutExpired(
            cmd=["docker", "version"],
            timeout=vi.TIMEOUT_DOCKER,
        )

        codigo, salida = vi.docker("version")

        self.assertEqual(codigo, 124)
        self.assertIn("agotado", salida)

    @patch("verificar_imagen.subprocess.run")
    def test_docker_error_sistema(self, ejecutar):
        """Controla errores del sistema operativo."""

        ejecutar.side_effect = OSError()

        codigo, salida = vi.docker("version")

        self.assertEqual(codigo, 1)
        self.assertIn("No fue posible", salida)

    def test_nombres_contenedores_unicos(self):
        """Comprueba la generacion de nombres sin duplicados."""

        nombres = {
            vi.generar_nombre_contenedor()
            for _ in range(100)
        }

        self.assertEqual(len(nombres), 100)

        for nombre in nombres:
            with self.subTest(nombre=nombre):
                self.assertRegex(
                    nombre,
                    r"^vyops-verificacion-[a-f0-9]{32}$",
                )

class TestEliminacionContenedores(unittest.TestCase):
    """Verifica las restricciones de eliminacion de contenedores."""

    def setUp(self):
        self.nombre = vi.generar_nombre_contenedor()

    @patch("verificar_imagen.docker")
    def test_rechaza_nombre_ajeno(self, docker):
        """No permite eliminar contenedores de otros proyectos."""

        aprobado, evidencia = vi.eliminar_contenedor(
            "contenedor-ajeno"
        )

        self.assertFalse(aprobado)
        self.assertIn("no autorizado", evidencia)

        docker.assert_not_called()

    @patch("verificar_imagen.docker")
    def test_rechaza_identificador_invalido(self, docker):
        """Rechaza nombres con prefijo correcto pero ID invalido."""

        aprobado, evidencia = vi.eliminar_contenedor(
            "vyops-verificacion-invalido"
        )

        self.assertFalse(aprobado)
        self.assertIn("no valido", evidencia)

        docker.assert_not_called()

    @patch("verificar_imagen.docker")
    def test_error_inspeccion(self, docker):
        """No elimina cuando falla la inspeccion de propiedad."""

        docker.return_value = (1, "Error de inspeccion")

        aprobado, evidencia = vi.eliminar_contenedor(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("verificar la propiedad", evidencia)

        self.assertEqual(docker.call_count, 1)

    @patch("verificar_imagen.docker")
    def test_etiqueta_ausente(self, docker):
        """Rechaza contenedores sin etiqueta de propiedad."""

        docker.return_value = (0, "")

        aprobado, evidencia = vi.eliminar_contenedor(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("no confirmada", evidencia)

        self.assertEqual(docker.call_count, 1)

    @patch("verificar_imagen.docker")
    def test_etiqueta_incorrecta(self, docker):
        """Rechaza una etiqueta que pertenece a otro identificador."""

        docker.return_value = (
            0,
            vi.generar_nombre_contenedor(),
        )

        aprobado, evidencia = vi.eliminar_contenedor(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("no confirmada", evidencia)

        self.assertEqual(docker.call_count, 1)

    @patch("verificar_imagen.docker")
    def test_eliminacion_autorizada(self, docker):
        """Elimina cuando se confirma la propiedad."""

        docker.side_effect = [
            (0, self.nombre),
            (0, self.nombre),
        ]

        aprobado, evidencia = vi.eliminar_contenedor(
            self.nombre
        )

        self.assertTrue(aprobado)
        self.assertIn("eliminado", evidencia)

        self.assertEqual(docker.call_count, 2)

        docker.assert_called_with(
            "container",
            "rm",
            "--force",
            self.nombre,
        )

    @patch("verificar_imagen.docker")
    def test_error_eliminacion(self, docker):
        """Detecta errores al eliminar un contenedor autorizado."""

        docker.side_effect = [
            (0, self.nombre),
            (1, "Error de eliminacion"),
        ]

        aprobado, evidencia = vi.eliminar_contenedor(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible eliminar", evidencia)

        self.assertEqual(docker.call_count, 2)


class TestExistenciaImagen(unittest.TestCase):
    """Verifica la resolucion de identificadores de imagen."""

    def setUp(self):
        self.imagen = "vyops:0.2"
        self.imagen_id = "sha256:" + "a" * 64

    @patch("verificar_imagen.docker")
    def test_resolver_imagen_correcta(self, docker):
        """Obtiene el identificador inmutable de la imagen."""

        docker.return_value = (0, self.imagen_id)

        aprobado, resultado = vi.resolver_imagen(
            self.imagen
        )

        self.assertTrue(aprobado)
        self.assertEqual(resultado, self.imagen_id)

        docker.assert_called_once_with(
            "image",
            "inspect",
            self.imagen,
            "--format",
            "{{.Id}}",
        )

    @patch("verificar_imagen.docker")
    def test_imagen_inexistente(self, docker):
        """Rechaza una imagen que no existe localmente."""

        docker.return_value = (1, "No such image")

        aprobado, resultado = vi.resolver_imagen(
            self.imagen
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible inspeccionar", resultado)

    @patch("verificar_imagen.docker")
    def test_identificadores_invalidos(self, docker):
        """Rechaza identificadores incompletos o mal formados."""

        identificadores = (
            "",
            "sha256:",
            "sha256:abc",
            "sha256:" + "g" * 64,
            "sha256:" + "a" * 63,
            "sha256:" + "a" * 65,
            "md5:" + "a" * 64,
            "vyops:0.2",
        )

        for identificador in identificadores:
            with self.subTest(identificador=identificador):
                docker.return_value = (0, identificador)

                aprobado, resultado = vi.resolver_imagen(
                    self.imagen
                )

                self.assertFalse(aprobado)
                self.assertIn("no valido", resultado)

    @patch("verificar_imagen.docker")
    def test_identificador_con_espacios(self, docker):
        """Normaliza los espacios externos de la salida."""

        docker.return_value = (
            0,
            f"  {self.imagen_id}\n",
        )

        aprobado, resultado = vi.resolver_imagen(
            self.imagen
        )

        self.assertTrue(aprobado)
        self.assertEqual(resultado, self.imagen_id)

    @patch("verificar_imagen.resolver_imagen")
    def test_img1_aprobada(self, resolver):
        """Presenta la evidencia cuando la imagen es valida."""

        resolver.return_value = (True, self.imagen_id)

        aprobado, evidencia = vi.verificar_img1(
            self.imagen
        )

        self.assertTrue(aprobado)
        self.assertIn(self.imagen_id, evidencia)

        resolver.assert_called_once_with(self.imagen)

    @patch("verificar_imagen.resolver_imagen")
    def test_img1_rechazada(self, resolver):
        """Conserva la evidencia de una resolucion fallida."""

        resolver.return_value = (
            False,
            "Imagen no disponible.",
        )

        aprobado, evidencia = vi.verificar_img1(
            self.imagen
        )

        self.assertFalse(aprobado)
        self.assertEqual(
            evidencia,
            "Imagen no disponible.",
        )

class TestArranqueContenedores(unittest.TestCase):
    """Verifica los comandos de arranque sin ejecutar Docker."""

    def setUp(self):
        self.imagen = "sha256:" + "a" * 64
        self.nombre = vi.generar_nombre_contenedor()

    @patch("verificar_imagen.docker")
    def test_arranque_original_correcto(self, docker):
        """Comprueba los argumentos del contenedor original."""

        docker.return_value = (0, "contenedor-simulado")

        aprobado, evidencia = vi.arrancar_contenedor(
            self.imagen,
            self.nombre,
        )

        self.assertTrue(aprobado)
        self.assertEqual(evidencia, "contenedor-simulado")

        docker.assert_called_once_with(
            "run",
            "--detach",
            "--pull=never",
            "--name",
            self.nombre,
            "--label",
            f"{vi.ETIQUETA_PROPIEDAD}={self.nombre}",
            "--publish",
            f"{vi.HOST}:{vi.PUERTO}:{vi.PUERTO_INTERNO}",
            self.imagen,
        )

    @patch("verificar_imagen.docker")
    def test_arranque_original_fallido(self, docker):
        """Controla un error durante el arranque original."""

        docker.return_value = (1, "Error simulado")

        aprobado, evidencia = vi.arrancar_contenedor(
            self.imagen,
            self.nombre,
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible iniciar", evidencia)

    @patch("verificar_imagen.Path.is_file", return_value=True)
    @patch("verificar_imagen.docker")
    def test_arranque_integracion_correcto(
        self,
        docker,
        existe_archivo,
    ):
        """Comprueba el arranque con RAG simulado."""

        docker.return_value = (0, "integracion-simulada")

        aprobado, evidencia = (
            vi.arrancar_contenedor_integracion(
                self.imagen,
                self.nombre,
            )
        )

        self.assertTrue(aprobado)
        self.assertEqual(evidencia, "integracion-simulada")

        docker.assert_called_once()

        argumentos = docker.call_args.args

        self.assertEqual(argumentos[0], "run")
        self.assertIn("--detach", argumentos)
        self.assertIn("--pull=never", argumentos)
        self.assertIn(self.nombre, argumentos)
        self.assertIn(self.imagen, argumentos)
        self.assertIn(
            f"{vi.ETIQUETA_PROPIEDAD}={self.nombre}",
            argumentos,
        )
        self.assertIn(
            f"{vi.HOST}:{vi.PUERTO}:{vi.PUERTO_INTERNO}",
            argumentos,
        )

        # Los archivos de prueba deben montarse como solo lectura.
        for archivo in ("servidor_pruebas.py", "casos.py"):
            with self.subTest(archivo=archivo):
                ruta = vi.BASE_DIR / archivo

                self.assertIn(
                    f"type=bind,source={ruta},"
                    f"target=/app/{archivo},readonly",
                    argumentos,
                )

        self.assertEqual(argumentos.count("--mount"), 2)

        # Comprueba que se utiliza el proveedor RAG simulado.
        self.assertEqual(argumentos[-3:-1], ("python", "-c"))

        codigo_simulacion = argumentos[-1]

        self.assertIn(
            "servicio.logica.responder",
            codigo_simulacion,
        )

        self.assertIn(
            "responder_simulado",
            codigo_simulacion,
        )

    @patch("verificar_imagen.Path.is_file", return_value=False)
    @patch("verificar_imagen.docker")
    def test_integracion_archivo_ausente(
        self,
        docker,
        existe_archivo,
    ):
        """Impide el arranque si faltan archivos de prueba."""

        aprobado, evidencia = (
            vi.arrancar_contenedor_integracion(
                self.imagen,
                self.nombre,
            )
        )

        self.assertFalse(aprobado)
        self.assertIn("Falta el archivo de pruebas", evidencia)

        docker.assert_not_called()

    @patch("verificar_imagen.Path.is_file", return_value=True)
    @patch("verificar_imagen.docker")
    def test_arranque_integracion_fallido(
        self,
        docker,
        existe_archivo,
    ):
        """Controla un error de Docker durante la integracion."""

        docker.return_value = (1, "Error simulado")

        aprobado, evidencia = (
            vi.arrancar_contenedor_integracion(
                self.imagen,
                self.nombre,
            )
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible iniciar", evidencia)

        docker.assert_called_once()

class TestDisponibilidadHTTP(unittest.TestCase):
    """Verifica la disponibilidad HTTP sin conexiones reales."""

    @patch("verificar_imagen.httpx2.Client")
    def test_servicio_disponible(self, cliente):
        """Acepta una respuesta HTTP 200 con estado correcto."""

        respuesta = MagicMock()
        respuesta.status_code = 200
        respuesta.json.return_value = {"estado": "ok"}

        sesion = cliente.return_value.__enter__.return_value
        sesion.get.return_value = respuesta

        aprobado, evidencia = vi.esperar_servicio()

        self.assertTrue(aprobado)
        self.assertIn("Servicio HTTP disponible", evidencia)

        sesion.get.assert_called_once_with(
            f"{vi.URL_BASE}/salud"
        )

        cliente.assert_called_once_with(
            timeout=2.0,
            trust_env=False,
        )

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.httpx2.Client")
    def test_respuesta_http_incorrecta(
        self,
        cliente,
        reloj,
        pausa,
    ):
        """Rechaza una respuesta HTTP distinta de 200."""

        reloj.side_effect = [0.0, 0.0, 31.0]

        respuesta = MagicMock()
        respuesta.status_code = 503

        sesion = cliente.return_value.__enter__.return_value
        sesion.get.return_value = respuesta

        aprobado, evidencia = vi.esperar_servicio()

        self.assertFalse(aprobado)
        self.assertIn("agotado", evidencia)

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.httpx2.Client")
    def test_estado_incorrecto(
        self,
        cliente,
        reloj,
        pausa,
    ):
        """Rechaza HTTP 200 cuando el estado no es correcto."""

        reloj.side_effect = [0.0, 0.0, 31.0]

        respuesta = MagicMock()
        respuesta.status_code = 200
        respuesta.json.return_value = {"estado": "error"}

        sesion = cliente.return_value.__enter__.return_value
        sesion.get.return_value = respuesta

        aprobado, evidencia = vi.esperar_servicio()

        self.assertFalse(aprobado)
        self.assertIn("agotado", evidencia)

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.httpx2.Client")
    def test_json_invalido(
        self,
        cliente,
        reloj,
        pausa,
    ):
        """Controla respuestas con contenido JSON invalido."""

        reloj.side_effect = [0.0, 0.0, 31.0]

        respuesta = MagicMock()
        respuesta.status_code = 200
        respuesta.json.side_effect = ValueError(
            "JSON invalido"
        )

        sesion = cliente.return_value.__enter__.return_value
        sesion.get.return_value = respuesta

        aprobado, evidencia = vi.esperar_servicio()

        self.assertFalse(aprobado)
        self.assertIn("agotado", evidencia)

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.httpx2.Client")
    def test_error_conexion(
        self,
        cliente,
        reloj,
        pausa,
    ):
        """Controla errores de conexion con el servicio."""

        reloj.side_effect = [0.0, 0.0, 31.0]

        sesion = cliente.return_value.__enter__.return_value

        sesion.get.side_effect = httpx2.ConnectError(
            "Conexion rechazada"
        )

        aprobado, evidencia = vi.esperar_servicio()

        self.assertFalse(aprobado)
        self.assertIn("agotado", evidencia)

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.httpx2.Client")
    def test_recuperacion_servicio(
        self,
        cliente,
        reloj,
        pausa,
    ):
        """Acepta un servicio disponible tras un reintento."""

        reloj.side_effect = [0.0, 0.0, 1.0]

        respuesta = MagicMock()
        respuesta.status_code = 200
        respuesta.json.return_value = {"estado": "ok"}

        sesion = cliente.return_value.__enter__.return_value

        sesion.get.side_effect = [
            httpx2.ConnectError("Servicio iniciando"),
            respuesta,
        ]

        aprobado, evidencia = vi.esperar_servicio()

        self.assertTrue(aprobado)
        self.assertIn("Servicio HTTP disponible", evidencia)
        self.assertEqual(sesion.get.call_count, 2)

        pausa.assert_called_once_with(
            vi.INTERVALO_ESPERA
        )

    @patch("verificar_imagen.esperar_servicio")
    def test_img2_aprobada(self, esperar):
        """Confirma la delegacion de IMG-2."""

        esperar.return_value = (
            True,
            "Servicio HTTP disponible.",
        )

        aprobado, evidencia = vi.verificar_img2()

        self.assertTrue(aprobado)
        self.assertIn("disponible", evidencia)

        esperar.assert_called_once_with(vi.URL_BASE)

    @patch("verificar_imagen.esperar_servicio")
    def test_img2_rechazada(self, esperar):
        """Conserva el resultado negativo de disponibilidad."""

        esperar.return_value = (
            False,
            "Tiempo de espera agotado.",
        )

        aprobado, evidencia = vi.verificar_img2()

        self.assertFalse(aprobado)
        self.assertIn("agotado", evidencia)

class TestUsuarioContenedor(unittest.TestCase):
    """Verifica el usuario efectivo del contenedor."""

    def setUp(self):
        self.nombre = vi.generar_nombre_contenedor()

    @patch("verificar_imagen.docker")
    def test_usuario_no_root(self, docker):
        """Acepta un usuario sin privilegios de root."""

        docker.return_value = (0, "10001")

        aprobado, evidencia = vi.verificar_img3(
            self.nombre
        )

        self.assertTrue(aprobado)
        self.assertIn("10001", evidencia)

        docker.assert_called_once_with(
            "exec",
            self.nombre,
            "id",
            "-u",
        )

    @patch("verificar_imagen.docker")
    def test_usuario_root(self, docker):
        """Rechaza un contenedor ejecutado como root."""

        docker.return_value = (0, "0")

        aprobado, evidencia = vi.verificar_img3(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("root", evidencia)

    @patch("verificar_imagen.docker")
    def test_uid_root_con_ceros(self, docker):
        """Rechaza el UID cero aunque tenga ceros adicionales."""

        docker.return_value = (0, "0000")

        aprobado, evidencia = vi.verificar_img3(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("root", evidencia)

    @patch("verificar_imagen.docker")
    def test_uid_invalido(self, docker):
        """Rechaza salidas que no representan un UID valido."""

        valores = (
            "",
            "root",
            "vyops",
            "-1",
            "10001.5",
            "10001\n10002",
            "Error de ejecucion",
            "\u0661\u0662\u0663",
        )

        for valor in valores:
            with self.subTest(uid=valor):
                docker.return_value = (0, valor)

                aprobado, evidencia = vi.verificar_img3(
                    self.nombre
                )

                self.assertFalse(aprobado)
                self.assertIn("no valido", evidencia)

    @patch("verificar_imagen.docker")
    def test_uid_con_espacios(self, docker):
        """Normaliza los espacios externos del UID."""

        docker.return_value = (0, "  10001\n")

        aprobado, evidencia = vi.verificar_img3(
            self.nombre
        )

        self.assertTrue(aprobado)
        self.assertIn("10001", evidencia)

    @patch("verificar_imagen.docker")
    def test_error_consulta_uid(self, docker):
        """Rechaza una inspeccion fallida del usuario."""

        docker.return_value = (
            1,
            "Error de inspeccion",
        )

        aprobado, evidencia = vi.verificar_img3(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible consultar", evidencia)

    @patch("verificar_imagen.docker")
    def test_error_con_uid_aparentemente_valido(self, docker):
        """No acepta un UID si Docker devuelve un error."""

        docker.return_value = (1, "10001")

        aprobado, evidencia = vi.verificar_img3(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible consultar", evidencia)

class TestArchivosProhibidos(unittest.TestCase):
    """Verifica la inspeccion de archivos dentro del contenedor."""

    def setUp(self):
        self.nombre = vi.generar_nombre_contenedor()

    @patch("verificar_imagen.docker")
    def test_inspeccion_correcta(self, docker):
        """Aprueba una inspeccion sin archivos prohibidos."""

        docker.return_value = (0, "INSPECCION_OK")

        aprobado, evidencia = vi.verificar_img4(
            self.nombre
        )

        self.assertTrue(aprobado)
        self.assertIn("Sin archivos prohibidos", evidencia)

        docker.assert_called_once()

        argumentos = docker.call_args.args

        self.assertEqual(
            argumentos[:4],
            ("exec", self.nombre, "python", "-c"),
        )

    @patch("verificar_imagen.docker")
    def test_archivos_prohibidos_detectados(self, docker):
        """Rechaza una imagen con archivos prohibidos."""

        archivos = (
            ".env",
            ".git/config",
            "config/.env.local",
            "credenciales.pem",
            "datos.sqlite3",
            "src/__pycache__/modulo.pyc",
            "registros/resultados.jsonl",
        )

        for archivo in archivos:
            with self.subTest(archivo=archivo):
                docker.return_value = (1, archivo)

                aprobado, evidencia = vi.verificar_img4(
                    self.nombre
                )

                self.assertFalse(aprobado)
                self.assertIn("archivos prohibidos", evidencia)

    @patch("verificar_imagen.docker")
    def test_error_inspeccion(self, docker):
        """Rechaza una inspeccion que no pudo ejecutarse."""

        docker.return_value = (
            2,
            "Directorio no disponible",
        )

        aprobado, evidencia = vi.verificar_img4(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible inspeccionar", evidencia)

    @patch("verificar_imagen.docker")
    def test_salida_invalida(self, docker):
        """Rechaza resultados sin confirmacion de inspeccion."""

        salidas = (
            "",
            "OK",
            "Resultado desconocido",
            "INSPECCION_OK\nError adicional",
        )

        for salida in salidas:
            with self.subTest(salida=salida):
                docker.return_value = (0, salida)

                aprobado, evidencia = vi.verificar_img4(
                    self.nombre
                )

                self.assertFalse(aprobado)
                self.assertIn("no valido", evidencia)

    @patch("verificar_imagen.docker")
    def test_confirmacion_con_espacios(self, docker):
        """Normaliza espacios externos de la confirmacion."""

        docker.return_value = (
            0,
            "  INSPECCION_OK\n",
        )

        aprobado, evidencia = vi.verificar_img4(
            self.nombre
        )

        self.assertTrue(aprobado)

    @patch("verificar_imagen.docker")
    def test_confirmacion_con_codigo_error(self, docker):
        """No aprueba una inspeccion que termina con error."""

        docker.return_value = (1, "INSPECCION_OK")

        aprobado, evidencia = vi.verificar_img4(
            self.nombre
        )

        self.assertFalse(aprobado)

    @patch("verificar_imagen.docker")
    def test_no_expone_salida_sensible(self, docker):
        """Evita propagar informacion sensible de Docker."""

        dato_simulado = "SECRETO_FICTICIO_DE_PRUEBA"

        docker.return_value = (
            1,
            dato_simulado,
        )

        aprobado, evidencia = vi.verificar_img4(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertNotIn(dato_simulado, evidencia)

class TestIntegracionHTTP(unittest.TestCase):
    """Verifica la ejecucion de los casos de integracion HTTP."""

    @patch("verificar_imagen.httpx2.Client")
    @patch("verificar_imagen.ejecutar_caso")
    def test_todos_los_casos_aprobados(
        self,
        ejecutar_caso,
        cliente,
    ):
        """Aprueba cuando todos los casos HTTP son exitosos."""

        ejecutar_caso.return_value = (True, 200, "")

        aprobado, evidencia = vi.verificar_img5()

        self.assertTrue(aprobado)

        total = len(vi.CASOS)

        self.assertIn(
            f"{total} de {total}",
            evidencia,
        )

        self.assertEqual(
            ejecutar_caso.call_count,
            total,
        )

        cliente.assert_called_once_with(
            base_url=vi.URL_BASE,
            timeout=10.0,
            trust_env=False,
        )

    @patch("verificar_imagen.httpx2.Client")
    @patch("verificar_imagen.ejecutar_caso")
    def test_un_caso_fallido(
        self,
        ejecutar_caso,
        cliente,
    ):
        """Rechaza la integracion si falla un solo caso."""

        total = len(vi.CASOS)

        ejecutar_caso.side_effect = [
            (False, 500, ""),
            *[(True, 200, "")] * (total - 1),
        ]

        aprobado, evidencia = vi.verificar_img5()

        self.assertFalse(aprobado)

        self.assertIn(
            f"{total - 1} de {total}",
            evidencia,
        )

        # Debe continuar ejecutando los casos restantes.
        self.assertEqual(
            ejecutar_caso.call_count,
            total,
        )

    @patch("verificar_imagen.httpx2.Client")
    @patch("verificar_imagen.ejecutar_caso")
    def test_todos_los_casos_fallidos(
        self,
        ejecutar_caso,
        cliente,
    ):
        """Rechaza una integracion completamente fallida."""

        ejecutar_caso.return_value = (False, 500, "")

        aprobado, evidencia = vi.verificar_img5()

        self.assertFalse(aprobado)

        self.assertIn(
            f"0 de {len(vi.CASOS)}",
            evidencia,
        )

    @patch("verificar_imagen.httpx2.Client")
    @patch("verificar_imagen.ejecutar_caso")
    def test_error_comunicacion_http(
        self,
        ejecutar_caso,
        cliente,
    ):
        """Controla errores HTTP sin detener los casos restantes."""

        total = len(vi.CASOS)

        ejecutar_caso.side_effect = [
            httpx2.ConnectError("Conexion rechazada"),
            *[(True, 200, "")] * (total - 1),
        ]

        aprobado, evidencia = vi.verificar_img5()

        self.assertFalse(aprobado)

        self.assertIn(
            f"{total - 1} de {total}",
            evidencia,
        )

        self.assertEqual(
            ejecutar_caso.call_count,
            total,
        )

    @patch("verificar_imagen.CASOS", [])
    @patch("verificar_imagen.httpx2.Client")
    @patch("verificar_imagen.ejecutar_caso")
    def test_sin_casos_disponibles(
        self,
        ejecutar_caso,
        cliente,
    ):
        """Impide aprobar una integracion sin casos de prueba."""

        aprobado, evidencia = vi.verificar_img5()

        self.assertFalse(aprobado)
        self.assertIn("No existen casos HTTP", evidencia)

        cliente.assert_not_called()
        ejecutar_caso.assert_not_called()

    @patch("builtins.print")
    @patch("verificar_imagen.httpx2.Client")
    @patch("verificar_imagen.ejecutar_caso")
    def test_no_expone_contenido_respuesta(
        self,
        ejecutar_caso,
        cliente,
        imprimir,
    ):
        """Evita imprimir contenido sensible de las respuestas."""

        dato_simulado = "SECRETO_FICTICIO_DE_PRUEBA"

        ejecutar_caso.return_value = (
            False,
            500,
            dato_simulado,
        )

        aprobado, evidencia = vi.verificar_img5()

        self.assertFalse(aprobado)
        self.assertNotIn(dato_simulado, evidencia)

        for llamada in imprimir.call_args_list:
            self.assertNotIn(
                dato_simulado,
                str(llamada),
            )

    @patch("verificar_imagen.httpx2.Client")
    @patch("verificar_imagen.ejecutar_caso")
    def test_ejecuta_casos_en_orden(
        self,
        ejecutar_caso,
        cliente,
    ):
        """Comprueba que todos los casos se ejecutan en orden."""

        ejecutar_caso.return_value = (True, 200, "")

        aprobado, _ = vi.verificar_img5()

        self.assertTrue(aprobado)

        sesion = (
            cliente.return_value.__enter__.return_value
        )

        self.assertEqual(
            ejecutar_caso.call_count,
            len(vi.CASOS),
        )

        for indice, caso in enumerate(vi.CASOS):
            with self.subTest(caso=caso["id"]):
                argumentos = (
                    ejecutar_caso.call_args_list[indice].args
                )

                self.assertEqual(
                    argumentos,
                    (sesion, caso),
                )

class TestHealthcheck(unittest.TestCase):
    """Verifica los estados de salud del contenedor."""

    def setUp(self):
        self.nombre = vi.generar_nombre_contenedor()

    @patch("verificar_imagen.docker")
    def test_contenedor_saludable(self, docker):
        """Aprueba un contenedor en estado healthy."""

        docker.return_value = (0, "healthy")

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertTrue(aprobado)
        self.assertIn("healthy", evidencia)

        docker.assert_called_once()

        argumentos = docker.call_args.args

        self.assertEqual(
            argumentos[:4],
            (
                "container",
                "inspect",
                self.nombre,
                "--format",
            ),
        )

        self.assertIn(
            ".State.Health.Status",
            argumentos[4],
        )

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.docker")
    def test_transicion_starting_healthy(
        self,
        docker,
        reloj,
        pausa,
    ):
        """Espera hasta que el contenedor este saludable."""

        reloj.side_effect = [0.0, 0.0, 1.0]

        docker.side_effect = [
            (0, "starting"),
            (0, "healthy"),
        ]

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertTrue(aprobado)
        self.assertIn("healthy", evidencia)
        self.assertEqual(docker.call_count, 2)

        pausa.assert_called_once_with(
            vi.INTERVALO_ESPERA
        )

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.docker")
    def test_contenedor_unhealthy(
        self,
        docker,
        reloj,
        pausa,
    ):
        """Rechaza un contenedor que permanece unhealthy."""

        reloj.side_effect = [0.0, 0.0, 31.0]

        docker.return_value = (0, "unhealthy")

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("agotado", evidencia)
        self.assertIn("unhealthy", evidencia)

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.docker")
    def test_starting_persistente(
        self,
        docker,
        reloj,
        pausa,
    ):
        """Rechaza un arranque que supera el tiempo permitido."""

        reloj.side_effect = [0.0, 0.0, 31.0]

        docker.return_value = (0, "starting")

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("agotado", evidencia)
        self.assertIn("starting", evidencia)

    @patch("verificar_imagen.docker")
    def test_sin_healthcheck(self, docker):
        """Rechaza un contenedor sin healthcheck configurado."""

        docker.return_value = (0, "sin healthcheck")

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("no tiene healthcheck", evidencia)

        docker.assert_called_once()

    @patch("verificar_imagen.docker")
    def test_error_inspeccion(self, docker):
        """Controla errores al consultar el estado de salud."""

        docker.return_value = (1, "Error de inspeccion")

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible consultar", evidencia)

    @patch("verificar_imagen.docker")
    def test_estado_desconocido(self, docker):
        """Rechaza estados de salud no reconocidos."""

        estados = (
            "",
            "running",
            "stopped",
            "unknown",
            "healthy\nError adicional",
        )

        for estado in estados:
            with self.subTest(estado=estado):
                docker.return_value = (0, estado)

                aprobado, evidencia = vi.verificar_img6(
                    self.nombre
                )

                self.assertFalse(aprobado)
                self.assertIn("no reconocido", evidencia)

    @patch("verificar_imagen.docker")
    def test_healthy_con_codigo_error(self, docker):
        """No aprueba un estado healthy si Docker falla."""

        docker.return_value = (1, "healthy")

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertFalse(aprobado)
        self.assertIn("No fue posible consultar", evidencia)

    @patch("verificar_imagen.docker")
    def test_healthy_con_espacios(self, docker):
        """Normaliza los espacios externos del estado."""

        docker.return_value = (0, "  healthy\n")

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertTrue(aprobado)
        self.assertIn("healthy", evidencia)

    @patch("verificar_imagen.time.sleep")
    @patch("verificar_imagen.time.monotonic")
    @patch("verificar_imagen.docker")
    def test_recuperacion_desde_unhealthy(
        self,
        docker,
        reloj,
        pausa,
    ):
        """Permite recuperarse dentro del tiempo establecido."""

        reloj.side_effect = [0.0, 0.0, 1.0]

        docker.side_effect = [
            (0, "unhealthy"),
            (0, "healthy"),
        ]

        aprobado, evidencia = vi.verificar_img6(
            self.nombre
        )

        self.assertTrue(aprobado)
        self.assertIn("healthy", evidencia)
        self.assertEqual(docker.call_count, 2)

class TestLimpiezaContenedores(unittest.TestCase):
    """Verifica la limpieza segura de contenedores temporales."""

    def setUp(self):
        self.nombre = vi.generar_nombre_contenedor()

        self.argumentos_listado = (
            "container",
            "ls",
            "--all",
            "--filter",
            f"name=^/{self.nombre}$",
            "--format",
            "{{.Names}}",
        )

    @patch("verificar_imagen.eliminar_contenedor")
    @patch("verificar_imagen.docker")
    def test_contenedor_ausente(self, docker, eliminar):
        """Aprueba la limpieza cuando el contenedor no existe."""

        docker.return_value = (0, "")

        aprobado = vi.limpiar_contenedor(self.nombre)

        self.assertTrue(aprobado)

        docker.assert_called_once_with(
            *self.argumentos_listado
        )

        eliminar.assert_not_called()

    @patch("verificar_imagen.eliminar_contenedor")
    @patch("verificar_imagen.docker")
    def test_limpieza_correcta(self, docker, eliminar):
        """Confirma que el contenedor desaparece tras eliminarlo."""

        docker.side_effect = [
            (0, self.nombre),
            (0, ""),
        ]

        eliminar.return_value = (
            True,
            "Contenedor temporal eliminado.",
        )

        aprobado = vi.limpiar_contenedor(self.nombre)

        self.assertTrue(aprobado)

        eliminar.assert_called_once_with(self.nombre)

        self.assertEqual(
            docker.call_args_list,
            [
                call(*self.argumentos_listado),
                call(*self.argumentos_listado),
            ],
        )

    @patch("verificar_imagen.eliminar_contenedor")
    @patch("verificar_imagen.docker")
    def test_nombre_no_autorizado(self, docker, eliminar):
        """Rechaza la limpieza de contenedores ajenos."""

        aprobado = vi.limpiar_contenedor(
            "contenedor-otro-proyecto"
        )

        self.assertFalse(aprobado)

        docker.assert_not_called()
        eliminar.assert_not_called()

    @patch("verificar_imagen.eliminar_contenedor")
    @patch("verificar_imagen.docker")
    def test_error_listado_inicial(self, docker, eliminar):
        """No elimina cuando falla la comprobacion inicial."""

        docker.return_value = (
            1,
            "Error de Docker",
        )

        aprobado = vi.limpiar_contenedor(self.nombre)

        self.assertFalse(aprobado)

        eliminar.assert_not_called()

    @patch("verificar_imagen.eliminar_contenedor")
    @patch("verificar_imagen.docker")
    def test_error_eliminacion(self, docker, eliminar):
        """Rechaza una limpieza cuya eliminacion ha fallado."""

        docker.return_value = (0, self.nombre)

        eliminar.return_value = (
            False,
            "No fue posible eliminar el contenedor.",
        )

        aprobado = vi.limpiar_contenedor(self.nombre)

        self.assertFalse(aprobado)

        eliminar.assert_called_once_with(self.nombre)

        self.assertEqual(docker.call_count, 1)

    @patch("verificar_imagen.eliminar_contenedor")
    @patch("verificar_imagen.docker")
    def test_contenedor_residual(self, docker, eliminar):
        """Detecta un contenedor que permanece tras eliminarlo."""

        docker.side_effect = [
            (0, self.nombre),
            (0, self.nombre),
        ]

        eliminar.return_value = (
            True,
            "Contenedor temporal eliminado.",
        )

        aprobado = vi.limpiar_contenedor(self.nombre)

        self.assertFalse(aprobado)
        self.assertEqual(docker.call_count, 2)

    @patch("verificar_imagen.eliminar_contenedor")
    @patch("verificar_imagen.docker")
    def test_error_verificacion_final(self, docker, eliminar):
        """Rechaza la limpieza si no puede confirmar su resultado."""

        docker.side_effect = [
            (0, self.nombre),
            (1, "Error de Docker"),
        ]

        eliminar.return_value = (
            True,
            "Contenedor temporal eliminado.",
        )

        aprobado = vi.limpiar_contenedor(self.nombre)

        self.assertFalse(aprobado)
        self.assertEqual(docker.call_count, 2)

class TestOrquestador(unittest.TestCase):
    """Verifica la coordinacion integral del verificador dinamico."""

    def setUp(self):
        self.imagen = "vyops:0.2"
        self.imagen_id = "sha256:" + "a" * 64
        self.nombre_original = vi.generar_nombre_contenedor()
        self.nombre_integracion = vi.generar_nombre_contenedor()

        # Sustituye las dependencias externas durante cada prueba.
        funciones = (
            "resolver_imagen",
            "generar_nombre_contenedor",
            "arrancar_contenedor",
            "arrancar_contenedor_integracion",
            "ejecutar_comprobacion",
            "esperar_servicio",
            "limpiar_contenedor",
        )

        self.mocks = {}

        for nombre in funciones:
            parche = patch.object(vi, nombre)

            self.mocks[nombre] = parche.start()

            self.addCleanup(parche.stop)

        # Evita imprimir los resultados simulados en la terminal.
        parche_impresion = patch("builtins.print")

        self.imprimir = parche_impresion.start()

        self.addCleanup(parche_impresion.stop)

        # Configuracion predeterminada: flujo completamente exitoso.
        self.mocks["resolver_imagen"].return_value = (
            True,
            self.imagen_id,
        )

        self.mocks["generar_nombre_contenedor"].side_effect = [
            self.nombre_original,
            self.nombre_integracion,
        ]

        self.mocks["arrancar_contenedor"].return_value = (
            True,
            "original-simulado",
        )

        self.mocks[
            "arrancar_contenedor_integracion"
        ].return_value = (
            True,
            "integracion-simulada",
        )

        self.mocks["ejecutar_comprobacion"].return_value = True

        self.mocks["esperar_servicio"].return_value = (
            True,
            "Servicio HTTP disponible.",
        )

        self.mocks["limpiar_contenedor"].return_value = True

    def test_ejecucion_completa_correcta(self):
        """Aprueba cuando todas las verificaciones son exitosas."""

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 0)

        self.mocks["resolver_imagen"].assert_called_once_with(
            self.imagen
        )

        self.mocks["arrancar_contenedor"].assert_called_once_with(
            self.imagen_id,
            self.nombre_original,
        )

        self.mocks[
            "arrancar_contenedor_integracion"
        ].assert_called_once_with(
            self.imagen_id,
            self.nombre_integracion,
        )

        self.assertEqual(
            self.mocks["ejecutar_comprobacion"].call_count,
            5,
        )

        self.assertEqual(
            self.mocks["limpiar_contenedor"].call_args_list,
            [
                call(self.nombre_original),
                call(self.nombre_integracion),
            ],
        )

        self.imprimir.assert_any_call("RESULTADO: PASS")

    def test_imagen_inexistente(self):
        """No inicia contenedores cuando la imagen no existe."""

        self.mocks["resolver_imagen"].return_value = (
            False,
            "Imagen no disponible.",
        )

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.mocks["arrancar_contenedor"].assert_not_called()

        self.mocks[
            "arrancar_contenedor_integracion"
        ].assert_not_called()

        self.mocks["limpiar_contenedor"].assert_not_called()

        self.mocks["ejecutar_comprobacion"].assert_not_called()

        self.imprimir.assert_any_call("RESULTADO: FAIL")

    def test_arranque_original_fallido(self):
        """Limpia el contenedor aunque su arranque haya fallado."""

        self.mocks["arrancar_contenedor"].return_value = (
            False,
            "No fue posible iniciar el contenedor.",
        )

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.assertEqual(
            self.mocks["limpiar_contenedor"].call_args_list,
            [
                call(self.nombre_original),
                call(self.nombre_integracion),
            ],
        )

        # Solo debe ejecutarse IMG-5.
        self.mocks[
            "ejecutar_comprobacion"
        ].assert_called_once_with(
            "IMG-5",
            "Integracion HTTP con RAG simulado",
            vi.verificar_img5,
        )

    def test_comprobacion_individual_fallida(self):
        """Rechaza el resultado si falla una comprobacion."""

        self.mocks["ejecutar_comprobacion"].side_effect = [
            True,
            False,
            True,
            True,
            True,
        ]

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.assertEqual(
            self.mocks["ejecutar_comprobacion"].call_count,
            5,
        )

        self.imprimir.assert_any_call("RESULTADO: FAIL")

    def test_limpieza_original_fallida(self):
        """Impide iniciar la integracion si falla la limpieza."""

        self.mocks["limpiar_contenedor"].return_value = False

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.mocks[
            "arrancar_contenedor_integracion"
        ].assert_not_called()

        self.mocks["limpiar_contenedor"].assert_called_once_with(
            self.nombre_original
        )

        self.imprimir.assert_any_call(
            "Limpieza de contenedores: FAIL"
        )

    def test_arranque_integracion_fallido(self):
        """Rechaza la ejecucion si falla el segundo contenedor."""

        self.mocks[
            "arrancar_contenedor_integracion"
        ].return_value = (
            False,
            "No fue posible iniciar la integracion.",
        )

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.mocks["esperar_servicio"].assert_not_called()

        self.assertEqual(
            self.mocks["ejecutar_comprobacion"].call_count,
            4,
        )

        self.assertEqual(
            self.mocks["limpiar_contenedor"].call_count,
            2,
        )

    def test_integracion_no_disponible(self):
        """No ejecuta IMG-5 si el servicio no esta disponible."""

        self.mocks["esperar_servicio"].return_value = (
            False,
            "Tiempo de espera agotado.",
        )

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.assertEqual(
            self.mocks["ejecutar_comprobacion"].call_count,
            4,
        )

        self.assertEqual(
            self.mocks["limpiar_contenedor"].call_count,
            2,
        )

    def test_limpieza_integracion_fallida(self):
        """Rechaza el resultado aunque las seis IMG sean exitosas."""

        self.mocks["limpiar_contenedor"].side_effect = [
            True,
            False,
        ]

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.imprimir.assert_any_call(
            "6 de 6 comprobaciones cumplidas"
        )

        self.imprimir.assert_any_call(
            "Limpieza de contenedores: FAIL"
        )

        self.imprimir.assert_any_call("RESULTADO: FAIL")

    def test_excepcion_durante_arranque_original(self):
        """Controla la excepcion y garantiza la limpieza."""

        self.mocks["arrancar_contenedor"].side_effect = (
            RuntimeError("Error simulado")
        )

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.assertEqual(
            self.mocks["limpiar_contenedor"].call_args_list,
            [
                call(self.nombre_original),
                call(self.nombre_integracion),
            ],
        )

        self.imprimir.assert_any_call("RESULTADO: FAIL")

    def test_excepcion_durante_arranque_integracion(self):
        """Controla la excepcion y limpia el segundo contenedor."""

        self.mocks[
            "arrancar_contenedor_integracion"
        ].side_effect = RuntimeError("Error simulado")

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.assertEqual(
            self.mocks["limpiar_contenedor"].call_args_list,
            [
                call(self.nombre_original),
                call(self.nombre_integracion),
            ],
        )

        self.imprimir.assert_any_call("RESULTADO: FAIL")

    def test_excepcion_resolucion_imagen(self):
        """Controla errores inesperados al resolver la imagen."""

        self.mocks["resolver_imagen"].side_effect = (
            RuntimeError("Error simulado")
        )

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.mocks["arrancar_contenedor"].assert_not_called()

        self.mocks[
            "arrancar_contenedor_integracion"
        ].assert_not_called()

        self.mocks["limpiar_contenedor"].assert_not_called()

        self.imprimir.assert_any_call("RESULTADO: FAIL")

    def test_excepcion_limpieza_original(self):
        """Bloquea la integracion si ocurre un error de limpieza."""

        self.mocks["limpiar_contenedor"].side_effect = (
            RuntimeError("Error simulado")
        )

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.mocks[
            "arrancar_contenedor_integracion"
        ].assert_not_called()

        self.imprimir.assert_any_call(
            "Limpieza de contenedores: FAIL"
        )

        self.imprimir.assert_any_call("RESULTADO: FAIL")

    def test_excepcion_limpieza_integracion(self):
        """Rechaza el resultado si falla la limpieza final."""

        self.mocks["limpiar_contenedor"].side_effect = [
            True,
            RuntimeError("Error simulado"),
        ]

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        self.imprimir.assert_any_call(
            "6 de 6 comprobaciones cumplidas"
        )

        self.imprimir.assert_any_call(
            "Limpieza de contenedores: FAIL"
        )

        self.imprimir.assert_any_call("RESULTADO: FAIL")

    def test_no_expone_excepcion_orquestador(self):
        """Evita exponer informacion sensible de una excepcion."""

        secreto = "CREDENCIAL_FICTICIA_DE_PRUEBA"

        self.mocks["arrancar_contenedor"].side_effect = (
            RuntimeError(secreto)
        )

        resultado = vi.ejecutar(self.imagen)

        self.assertEqual(resultado, 1)

        for llamada in self.imprimir.call_args_list:
            self.assertNotIn(secreto, str(llamada))

class TestAlgoritmoInspeccion(unittest.TestCase):
    """Ejecuta el algoritmo de inspeccion sobre archivos temporales."""

    def setUp(self):
        self.temporal = TemporaryDirectory()

        self.addCleanup(self.temporal.cleanup)

        self.raiz = Path(self.temporal.name)

        # Obtiene el codigo real enviado al contenedor.
        with patch("verificar_imagen.docker") as docker:
            docker.return_value = (0, "INSPECCION_OK")

            vi.verificar_img4(
                vi.generar_nombre_contenedor()
            )

            self.codigo = docker.call_args.args[-1]

        # Redirige la inspeccion al directorio temporal.
        self.assertIn('Path("/app")', self.codigo)

        self.codigo = self.codigo.replace(
            'Path("/app")',
            f"Path({str(self.raiz)!r})",
            1,
        )

    def crear_archivo(self, ruta_relativa):
        """Crea un archivo ficticio dentro del entorno temporal."""

        ruta = self.raiz / ruta_relativa

        ruta.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        ruta.write_text(
            "Contenido ficticio de prueba",
            encoding="utf-8",
        )

        return ruta

    def ejecutar_inspeccion(self):
        """Ejecuta el codigo real en un proceso Python aislado."""

        return subprocess.run(
            [sys.executable, "-c", self.codigo],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )

    def test_directorio_limpio(self):
        """Aprueba un directorio con archivos permitidos."""

        self.crear_archivo("servicio/main.py")
        self.crear_archivo("requirements.txt")
        self.crear_archivo("corpus/documento.md")

        resultado = self.ejecutar_inspeccion()

        self.assertEqual(resultado.returncode, 0)
        self.assertEqual(
            resultado.stdout.strip(),
            "INSPECCION_OK",
        )

    def test_detecta_dockerfile(self):
        """Detecta Dockerfile independientemente de sus mayusculas."""

        self.crear_archivo("Dockerfile")

        resultado = self.ejecutar_inspeccion()

        self.assertEqual(resultado.returncode, 1)
        self.assertIn("Dockerfile", resultado.stdout)

    def test_detecta_archivo_bak(self):
        """Detecta archivos de respaldo dentro de subdirectorios."""

        self.crear_archivo("config/respaldo.bak")

        resultado = self.ejecutar_inspeccion()

        self.assertEqual(resultado.returncode, 1)

        self.assertIn(
            "config/respaldo.bak",
            resultado.stdout,
        )

    def test_detecta_archivos_env(self):
        """Detecta archivos de entorno en distintos niveles."""

        self.crear_archivo(".env")
        self.crear_archivo("config/.env.local")

        resultado = self.ejecutar_inspeccion()

        self.assertEqual(resultado.returncode, 1)
        self.assertIn(".env", resultado.stdout)

        self.assertIn(
            "config/.env.local",
            resultado.stdout,
        )

    def test_detecta_extensiones_mayusculas(self):
        """Detecta extensiones prohibidas sin distinguir mayusculas."""

        self.crear_archivo("config/credencial.PEM")
        self.crear_archivo("config/respaldo.BAK")

        resultado = self.ejecutar_inspeccion()

        self.assertEqual(resultado.returncode, 1)
        self.assertIn("credencial.PEM", resultado.stdout)
        self.assertIn("respaldo.BAK", resultado.stdout)

    def test_detecta_directorios_prohibidos(self):
        """Detecta directorios excluidos dentro de la imagen."""

        self.crear_archivo(".git/config")
        self.crear_archivo("src/__pycache__/modulo.pyc")
        self.crear_archivo("vectorstore_prueba/datos.txt")

        resultado = self.ejecutar_inspeccion()

        self.assertEqual(resultado.returncode, 1)
        self.assertIn(".git", resultado.stdout)
        self.assertIn("__pycache__", resultado.stdout)
        self.assertIn("vectorstore_prueba", resultado.stdout)

    def test_directorio_inexistente(self):
        """Rechaza una inspeccion si el directorio no existe."""

        self.raiz.rmdir()

        resultado = self.ejecutar_inspeccion()

        self.assertEqual(resultado.returncode, 2)
        self.assertNotIn("INSPECCION_OK", resultado.stdout)

    def test_error_acceso_durante_recorrido(self):
        """Rechaza una inspeccion incompleta por errores de acceso."""

        def recorrido_fallido(*args, **kwargs):
            kwargs["on_error"](
                PermissionError("Acceso denegado simulado")
            )

        with patch.object(
            Path,
            "walk",
            side_effect=recorrido_fallido,
        ):
            with self.assertRaises(SystemExit) as error:
                exec(self.codigo, {})

        self.assertEqual(error.exception.code, 2)

    def test_no_expone_contenido_archivos(self):
        """Comprueba que la inspeccion no imprime credenciales."""

        secreto = "CREDENCIAL_FICTICIA_NO_REAL"

        ruta = self.crear_archivo(".env")

        ruta.write_text(
            secreto,
            encoding="utf-8",
        )

        resultado = self.ejecutar_inspeccion()

        self.assertEqual(resultado.returncode, 1)
        self.assertNotIn(secreto, resultado.stdout)
        self.assertNotIn(secreto, resultado.stderr)

class TestEjecutarComprobacion(unittest.TestCase):
    """Verifica el control de resultados y excepciones individuales."""

    @patch("builtins.print")
    def test_comprobacion_aprobada(self, imprimir):
        """Devuelve True cuando la comprobacion es exitosa."""

        funcion = MagicMock(
            return_value=(True, "Evidencia correcta.")
        )

        resultado = vi.ejecutar_comprobacion(
            "IMG-PRUEBA",
            "Comprobacion simulada",
            funcion,
        )

        self.assertTrue(resultado)

        funcion.assert_called_once_with()

        imprimir.assert_any_call(
            "PASA IMG-PRUEBA - Comprobacion simulada"
        )

        imprimir.assert_any_call(
            "    Evidencia: Evidencia correcta."
        )

    @patch("builtins.print")
    def test_comprobacion_rechazada(self, imprimir):
        """Devuelve False cuando la comprobacion falla."""

        funcion = MagicMock(
            return_value=(False, "Evidencia incorrecta.")
        )

        resultado = vi.ejecutar_comprobacion(
            "IMG-PRUEBA",
            "Comprobacion simulada",
            funcion,
        )

        self.assertFalse(resultado)

        imprimir.assert_any_call(
            "FALLA IMG-PRUEBA - Comprobacion simulada"
        )

    @patch("builtins.print")
    def test_transmite_argumentos(self, imprimir):
        """Entrega correctamente los argumentos a la funcion."""

        funcion = MagicMock(
            return_value=(True, "Correcto.")
        )

        resultado = vi.ejecutar_comprobacion(
            "IMG-PRUEBA",
            "Comprobacion con argumentos",
            funcion,
            "contenedor-simulado",
            30,
        )

        self.assertTrue(resultado)

        funcion.assert_called_once_with(
            "contenedor-simulado",
            30,
        )

    @patch("builtins.print")
    def test_excepcion_inesperada(self, imprimir):
        """Convierte una excepcion inesperada en un fallo controlado."""

        funcion = MagicMock(
            side_effect=RuntimeError("Error simulado")
        )

        resultado = vi.ejecutar_comprobacion(
            "IMG-PRUEBA",
            "Comprobacion simulada",
            funcion,
        )

        self.assertFalse(resultado)

        imprimir.assert_any_call(
            "FALLA IMG-PRUEBA - Comprobacion simulada"
        )

        imprimir.assert_any_call(
            "    Evidencia: Error inesperado durante la comprobacion."
        )

    @patch("builtins.print")
    def test_no_expone_detalles_excepcion(self, imprimir):
        """Impide exponer datos sensibles incluidos en una excepcion."""

        secreto = "CREDENCIAL_FICTICIA_DE_PRUEBA"

        funcion = MagicMock(
            side_effect=RuntimeError(secreto)
        )

        resultado = vi.ejecutar_comprobacion(
            "IMG-PRUEBA",
            "Comprobacion simulada",
            funcion,
        )

        self.assertFalse(resultado)

        for llamada in imprimir.call_args_list:
            self.assertNotIn(secreto, str(llamada))

    @patch("builtins.print")
    def test_resultado_mal_formado(self, imprimir):
        """Rechaza una funcion que devuelve un resultado incorrecto."""

        funcion = MagicMock(return_value=None)

        resultado = vi.ejecutar_comprobacion(
            "IMG-PRUEBA",
            "Comprobacion simulada",
            funcion,
        )

        self.assertFalse(resultado)

        imprimir.assert_any_call(
            "    Evidencia: Error inesperado durante la comprobacion."
        )



if __name__ == "__main__":
    unittest.main()