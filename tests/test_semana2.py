import math
import unittest

from backend import edo, integracion, interpolacion, raices


class MetodosSemanaDosTest(unittest.TestCase):
    def test_metodos_de_raices_convergen_y_validan_singularidades(self):
        funcion = lambda x: x * x - 2.0
        raiz = math.sqrt(2.0)
        bis = raices.biseccion(funcion, 1.0, 2.0, referencia=raiz)
        newton = raices.newton_raphson(funcion, lambda x: 2.0 * x, 1.5, referencia=raiz)
        secante = raices.secante(funcion, 1.0, 2.0, referencia=raiz)
        for resultado in (bis, newton, secante):
            self.assertTrue(resultado["convergio"])
            self.assertAlmostEqual(resultado["raiz_aproximada"], raiz, places=8)
            self.assertGreaterEqual(resultado["residual_final"], 0.0)
        with self.assertRaises(ValueError):
            raices.biseccion(funcion, 2.0, 3.0)
        with self.assertRaises(ValueError):
            raices.newton_raphson(lambda x: x * x + 1.0, lambda _: 0.0, 1.0)

    def test_cuadraturas_reportan_refinamiento_y_rechazan_simpson_impar(self):
        referencia = 1.0 / 3.0
        trapecio = integracion.trapecio_compuesto(lambda x: x * x, 0.0, 1.0, 32, referencia=referencia)
        simpson = integracion.simpson_13_compuesto(lambda x: x * x, 0.0, 1.0, 32, referencia=referencia)
        romberg = integracion.romberg(lambda x: x * x, 0.0, 1.0, niveles=5, referencia=referencia)
        self.assertGreater(len(trapecio["tabla_refinamiento"]), 1)
        self.assertGreater(len(simpson["tabla_refinamiento"]), 1)
        self.assertAlmostEqual(simpson["integral_aproximada"], referencia, places=12)
        self.assertAlmostEqual(romberg["integral_aproximada"], referencia, places=12)
        self.assertEqual(len(romberg["tabla_romberg"]), 5)
        with self.assertRaises(ValueError):
            integracion.simpson_13_compuesto(lambda x: x, 0.0, 1.0, 3)

    def test_runge_kutta_clasico_supera_heun_y_reporta_referencia(self):
        funcion = lambda _, y: [y[0]]
        referencia = lambda t: [math.exp(t)]
        heun = edo.resolver_edo(funcion, (0.0, 1.0), [1.0], 10, metodo="rk2", referencia=referencia)
        rk4 = edo.resolver_edo(funcion, (0.0, 1.0), [1.0], 10, metodo="rk4", referencia=referencia)
        self.assertLess(rk4["error_absoluto_final"], heun["error_absoluto_final"])
        self.assertEqual(len(rk4["tabla_temporal"]), 11)
        self.assertTrue(rk4["estable"])

    def test_interpoladores_reconstruyen_nodos_ocultos(self):
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [2.0 * x + 1.0 for x in xs]
        puntos = [0.5, 1.5, 2.5]
        referencias = [2.0 * x + 1.0 for x in puntos]
        metodos = (
            interpolacion.lagrange,
            interpolacion.newton_diferencias_divididas,
            interpolacion.splines_cubicos_naturales,
        )
        for metodo in metodos:
            resultado = metodo(xs, ys, puntos, referencia=referencias)
            self.assertLess(resultado["error_absoluto_final"], 1e-10)
            self.assertEqual(len(resultado["evaluaciones"]), len(puntos))
        diferencias = interpolacion.newton_diferencias_divididas(xs, ys, puntos)
        self.assertEqual(len(diferencias["tabla_diferencias"]), len(xs))


if __name__ == "__main__":
    unittest.main()
