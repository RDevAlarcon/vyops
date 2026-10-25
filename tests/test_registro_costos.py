
"""Pruebas unitarias del registro de costos por sesión de VyOps."""

import unittest

from src.registro_costos import RegistroCostosSesion


class TestRegistroCostosSesion(unittest.TestCase):
    """Verifica el registro, acumulación y aislamiento de costos."""

    def test_sesion_inicia_sin_costos(self):
        """Comprueba que una sesión nueva no tenga operaciones."""
        registro = RegistroCostosSesion()

        self.assertEqual(registro.obtener_total(), 0.0)
        self.assertEqual(registro.obtener_operaciones(), [])

    def test_registra_costo_por_operacion(self):
        """Comprueba que cada operación conserve su costo."""
        registro = RegistroCostosSesion()

        registro.registrar_operacion(0.001)
        registro.registrar_operacion(0.002)

        self.assertEqual(
            registro.obtener_operaciones(),
            [0.001, 0.002],
        )
        self.assertAlmostEqual(registro.obtener_total(), 0.003)

    def test_rechaza_costos_invalidos(self):
        """Impide registrar costos negativos o no finitos."""
        registro = RegistroCostosSesion()

        for costo in (-1, float("nan"), float("inf"), True, "1"):
            with self.subTest(costo=costo):
                with self.assertRaises(ValueError):
                    registro.registrar_operacion(costo)

        self.assertEqual(registro.obtener_operaciones(), [])

    def test_sesiones_independientes(self):
        """Comprueba que dos sesiones no compartan operaciones."""
        sesion_a = RegistroCostosSesion()
        sesion_b = RegistroCostosSesion()

        sesion_a.registrar_operacion(0.01)
        sesion_b.registrar_operacion(0.02)

        self.assertAlmostEqual(sesion_a.obtener_total(), 0.01)
        self.assertAlmostEqual(sesion_b.obtener_total(), 0.02)

    def test_historial_no_se_modifica_externamente(self):
        """Comprueba que el historial devuelto sea una copia."""
        registro = RegistroCostosSesion()
        registro.registrar_operacion(0.01)

        historial = registro.obtener_operaciones()
        historial.append(999)

        self.assertEqual(registro.obtener_operaciones(), [0.01])


if __name__ == "__main__":
    unittest.main()
