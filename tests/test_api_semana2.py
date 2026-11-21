import atexit
import os
import tempfile
import unittest
import uuid
from contextlib import closing

_directorio_temporal = tempfile.TemporaryDirectory()
_base_anterior = os.environ.get("SIMTELE_RISK_DB")
os.environ["SIMTELE_RISK_DB"] = os.path.join(_directorio_temporal.name, "api_test.db")
from backend.app import app
from backend.database import DB_PATH, _deserializar_json, get_connection

if _base_anterior is None:
    os.environ.pop("SIMTELE_RISK_DB", None)
else:
    os.environ["SIMTELE_RISK_DB"] = _base_anterior
atexit.register(_directorio_temporal.cleanup)


class APIyPersistenciaSemanaDosTest(unittest.TestCase):
    def setUp(self):
        self.cliente = app.test_client()

    def test_rutas_nuevas_y_sistemas_lineales_existentes(self):
        inicio = self.cliente.get("/")
        self.assertEqual(inicio.status_code, 200)
        inicio.close()
        escenarios = self.cliente.get("/api/escenarios-modulo")
        self.assertEqual(escenarios.status_code, 200)
        self.assertEqual(len(escenarios.get_json()["modulos"]), 4)
        ejecuciones = (
            ("/api/metodos/raices", {"modulo": 1, "escenario": "NORMAL", "metodo": "biseccion"}),
            ("/api/metodos/integracion", {"modulo": 1, "escenario": "NORMAL", "metodo": "romberg"}),
            ("/api/metodos/edo", {"modulo": 3, "escenario": "ESTRES", "metodo": "rk4"}),
            ("/api/metodos/interpolacion", {"modulo": 4, "escenario": "NORMAL", "metodo": "spline"}),
        )
        for ruta, payload in ejecuciones:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.cliente.post(ruta, json=payload).status_code, 200)
        self.assertEqual(self.cliente.post("/api/metodos/exacta", json={}).status_code, 200)

    def test_guardar_y_recuperar_simulacion_sigue_funcionando(self):
        escenarios = self.cliente.get("/api/escenarios?caso_estudio_id=1").get_json()
        escenario = next(item for item in escenarios if item["codigo"] == "NORMAL")
        codigo = f"TEST-{uuid.uuid4().hex[:12]}"
        respuesta = self.cliente.post("/api/simulaciones", json={
            "escenario_id": escenario["id"],
            "codigo": codigo,
            "nombre": "Prueba de persistencia numérica",
            "metodo": "RK4",
            "parametros": {"resultado_numerico": {"valor_final": 1.0}},
        })
        self.assertEqual(respuesta.status_code, 201)
        simulacion_id = respuesta.get_json()["id"]
        recuperada = self.cliente.get(f"/api/simulaciones/{simulacion_id}")
        self.assertEqual(recuperada.status_code, 200)
        self.assertEqual(recuperada.get_json()["codigo"], codigo)

    def test_rutas_de_carga_recuperan_sqlite_eliminada_en_vivo(self):
        if DB_PATH.exists():
            DB_PATH.unlink()

        rutas = (
            "/api/salud",
            "/api/casos-estudio",
            "/api/escenarios",
            "/api/simulaciones",
            "/api/escenarios-modulo",
        )
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                respuesta = self.cliente.get(ruta)
                self.assertEqual(respuesta.status_code, 200, respuesta.get_data(as_text=True))

        self.assertEqual(len(self.cliente.get("/api/casos-estudio").get_json()), 4)
        self.assertEqual(len(self.cliente.get("/api/escenarios").get_json()), 12)

    def test_json_nulo_o_corrupto_usa_valor_por_defecto(self):
        self.assertEqual(_deserializar_json(None, {}), {})
        self.assertEqual(_deserializar_json(b"\xff", {}), {})

    def test_esquema_parcial_responde_error_json_sin_ocultar_el_fallo(self):
        with closing(get_connection()) as connection:
            connection.execute("DROP TABLE resultado_resumen")
            connection.commit()

        try:
            respuesta = self.cliente.get("/api/escenarios")
            self.assertEqual(respuesta.status_code, 503)
            self.assertEqual(
                respuesta.get_json(),
                {"error": "La base de datos no está disponible"},
            )
        finally:
            if DB_PATH.exists():
                DB_PATH.unlink()


if __name__ == "__main__":
    unittest.main()
