import os
import tempfile
import unittest
import uuid
from pathlib import Path

_directorio = tempfile.TemporaryDirectory()
_db_anterior = os.environ.get("SIMTELE_RISK_DB")
os.environ["SIMTELE_RISK_DB"] = str(Path(_directorio.name) / "semana3.db")

from backend import database
from backend import escenarios_modulo
import backend.app as app_module
from backend.app import app

if _db_anterior is None:
    os.environ.pop("SIMTELE_RISK_DB", None)
else:
    os.environ["SIMTELE_RISK_DB"] = _db_anterior

class SemanaTresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path_anterior = database.DB_PATH
        cls.app_db_path_anterior = app_module.DB_PATH
        database.DB_PATH = Path(_directorio.name) / "semana3.db"
        app_module.DB_PATH = database.DB_PATH
        database.inicializar_base_datos()

    @classmethod
    def tearDownClass(cls):
        database.DB_PATH = cls.db_path_anterior
        app_module.DB_PATH = cls.app_db_path_anterior
        _directorio.cleanup()

    def setUp(self):
        self.cliente = app.test_client()

    def test_cobertura_de_metodos_por_modulo_y_escenario(self):
        catalogo = escenarios_modulo.obtener_escenarios_modulo()["modulos"]
        for modulo, datos in catalogo.items():
            numero_modulo = int(modulo)
            self.assertEqual(set(datos["escenarios"]), {"NORMAL", "ESTRES", "MAL_CONDICIONADO"})
            for escenario in datos["escenarios"]:
                metodo = "rk4" if numero_modulo in (1, 3) else ("lagrange" if numero_modulo == 4 else "biseccion")
                resultado = escenarios_modulo.ejecutar_metodo_modulo(
                    numero_modulo, escenario, metodo
                )
                self.assertEqual(resultado["modulo"], numero_modulo)
                self.assertEqual(resultado["escenario"], escenario)
                self.assertIn("parametros", resultado)
                self.assertIn("conclusion_numerica", resultado)
                self.assertIn("conclusion_problema", resultado)

    def test_referencia_frenado_y_modelo_variable(self):
        normal = escenarios_modulo.ejecutar_metodo_modulo(1, "NORMAL", "rk4")
        estres = escenarios_modulo.ejecutar_metodo_modulo(1, "ESTRES", "secante")
        self.assertAlmostEqual(normal["parametros"]["velocidad_inicial"], 6.0)
        self.assertAlmostEqual(normal["parametros"]["desaceleracion"], 1.5)
        self.assertAlmostEqual(normal["referencia_analitica"]["tiempo_parada"], 4.0)
        self.assertAlmostEqual(normal["referencia_analitica"]["distancia_frenado"], 12.0)
        self.assertGreater(estres["parametros"]["amplitud_desaceleracion"], 0.0)
        self.assertIn("distancia_total", estres)

    def test_sistemas_spd_y_condicionamiento_independiente_de_convergencia(self):
        normal = escenarios_modulo.ejecutar_metodo_modulo(2, "NORMAL", "jacobi")
        mal_condicionado = escenarios_modulo.ejecutar_metodo_modulo(
            2, "MAL_CONDICIONADO", "gradiente_conjugado"
        )
        self.assertLess(normal["numero_condicion_kappa_2"], mal_condicionado["numero_condicion_kappa_2"])
        self.assertTrue(mal_condicionado["convergio"])
        self.assertGreaterEqual(mal_condicionado["residual_final"], 0.0)
        for metodo in ("jacobi", "gauss_seidel", "lu", "gradiente_conjugado"):
            resultado = escenarios_modulo.ejecutar_metodo_modulo(2, "ESTRES", metodo)
            self.assertIn("numero_condicion_kappa_2", resultado)

    def test_oscilacion_usa_parametros_fisicos_publicados_y_malla_critica(self):
        normal = escenarios_modulo.ejecutar_metodo_modulo(3, "NORMAL", "rk4")
        critica = escenarios_modulo.ejecutar_metodo_modulo(3, "MAL_CONDICIONADO", "rk4")
        self.assertEqual(
            (normal["parametros"]["masa"], normal["parametros"]["rigidez"], normal["parametros"]["amortiguamiento"]),
            (500.0, 1200.0, 40.0),
        )
        self.assertTrue(normal["estable"])
        self.assertFalse(critica["estable"])
        self.assertTrue(critica["convergio"])

    def test_interpolacion_mide_nodos_ocultos_con_ruido_hipotetico(self):
        for metodo in ("lagrange", "newton_interpolacion", "spline"):
            resultado = escenarios_modulo.ejecutar_metodo_modulo(
                4, "ESTRES", metodo
            )
            self.assertEqual(len(resultado["nodos_ocultos"]), 5)
            self.assertIsNotNone(resultado["error_absoluto_final"])
            self.assertEqual(resultado["parametros"]["ruido"], 0.01)

    def test_guardar_recuperar_y_relanzar_calculo_con_tolerancia(self):
        resultado = escenarios_modulo.ejecutar_metodo_modulo(1, "NORMAL", "rk4")
        escenario = next(
            item for item in database.obtener_escenarios()
            if item["caso_codigo"] == "CE-001" and item["codigo"] == "NORMAL"
        )
        codigo = f"SEM3-{uuid.uuid4().hex[:12]}"
        respuesta = self.cliente.post("/api/simulaciones", json={
            "escenario_id": escenario["id"],
            "codigo": codigo,
            "nombre": "Prueba de relanzamiento hipotético",
            "metodo": "Runge-Kutta 4",
            "parametros": {
                "metodo": "rk4",
                "modulo": 1,
                "escenario_numerico": "NORMAL",
                "parametros_modelo": resultado["parametros"],
                "resultado_numerico": resultado,
            },
            "estado": "completada",
        })
        self.assertEqual(respuesta.status_code, 201)
        simulacion_id = respuesta.get_json()["id"]
        recuperada = self.cliente.get(f"/api/simulaciones/{simulacion_id}")
        self.assertEqual(recuperada.status_code, 200)
        relanzada = self.cliente.post(
            f"/api/simulaciones/{simulacion_id}/relanzar",
            json={"tolerancia": 1e-10},
        )
        self.assertEqual(relanzada.status_code, 200, relanzada.get_json())
        self.assertTrue(relanzada.get_json()["coincide"])
        self.assertLessEqual(relanzada.get_json()["diferencia_maxima"], 1e-10)

    def test_parametros_editables_validan_entradas(self):
        resultado = escenarios_modulo.ejecutar_metodo_modulo(
            1,
            "NORMAL",
            "rk4",
            {"velocidad_inicial": 7.0, "distancia_disponible": 10.0},
        )
        self.assertEqual(resultado["parametros"]["velocidad_inicial"], 7.0)
        self.assertTrue(resultado["supera_distancia_segura"])
        with self.assertRaises(ValueError):
            escenarios_modulo.ejecutar_metodo_modulo(
                3, "NORMAL", "rk4", {"rigidez": float("inf")}
            )
        with self.assertRaises(ValueError):
            escenarios_modulo.ejecutar_metodo_modulo(
                4, "NORMAL", "lagrange", {"cantidad_nodos": 2.5}
            )

    def test_api_unificada_acepta_preset_editable_y_metodos_lineales(self):
        desgaste = self.cliente.post("/api/modulos/2/ejecutar", json={
            "escenario": "NORMAL",
            "metodo": "lu",
            "parametros": {
                **escenarios_modulo.ESCENARIOS_MODULO[2]["escenarios"]["NORMAL"]["parametros"],
                "tasa": 0.04,
            },
        })
        self.assertEqual(desgaste.status_code, 200, desgaste.get_json())
        self.assertIn("numero_condicion_kappa_2", desgaste.get_json())

        frenado = self.cliente.post("/api/modulos/1/ejecutar", json={
            "escenario": "NORMAL",
            "metodo": "rk4",
            "parametros": {"velocidad_inicial": 7.0},
        })
        self.assertEqual(frenado.status_code, 200, frenado.get_json())
        self.assertEqual(frenado.get_json()["parametros"]["velocidad_inicial"], 7.0)


if __name__ == "__main__":
    unittest.main()
