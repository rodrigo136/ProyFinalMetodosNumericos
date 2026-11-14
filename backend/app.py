"""API Flask para SIMTELE-RISK: métodos lineales y simulaciones."""

from __future__ import annotations

import math
import os
import sqlite3
from typing import Any, Callable, Dict, List

from flask import Flask, Response, jsonify, request, send_from_directory

if __package__:
    from .database import (
        DB_PATH,
        crear_escenario,
        guardar_simulacion,
        inicializar_base_datos,
        listar_simulaciones,
        obtener_casos_estudio,
        obtener_escenarios,
        recuperar_simulacion,
    )
    from .sistemas_lineales import (
        A_REFERENCIA,
        B_REFERENCIA,
        factorizacion_lu,
        gauss_seidel,
        gradiente_conjugado,
        jacobi,
        solucion_exacta,
    )
else:
    from database import (
        DB_PATH,
        crear_escenario,
        guardar_simulacion,
        inicializar_base_datos,
        listar_simulaciones,
        obtener_casos_estudio,
        obtener_escenarios,
        recuperar_simulacion,
    )
    from sistemas_lineales import (
        A_REFERENCIA,
        B_REFERENCIA,
        factorizacion_lu,
        gauss_seidel,
        gradiente_conjugado,
        jacobi,
        solucion_exacta,
    )

app = Flask(__name__, static_folder="../frontend", static_url_path="")
app.config["JSON_SORT_KEYS"] = False
inicializar_base_datos()


@app.after_request
def permitir_frontend(respuesta: Response) -> Response:
    respuesta.headers["Access-Control-Allow-Origin"] = "*"
    respuesta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    respuesta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return respuesta


def _json_seguro(valor: Any) -> Any:
    if isinstance(valor, float) and not math.isfinite(valor):
        return None
    if isinstance(valor, dict):
        return {clave: _json_seguro(contenido) for clave, contenido in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(contenido) for contenido in valor]
    return valor


def _responder(datos: Any, estado: int = 200) -> tuple[Response, int]:
    return jsonify(_json_seguro(datos)), estado


def _obtener_payload() -> Dict[str, Any]:
    if request.content_length in (None, 0):
        return {}
    datos = request.get_json(silent=True)
    if datos is None:
        raise ValueError("El cuerpo de la solicitud debe ser JSON válido")
    if not isinstance(datos, dict):
        raise ValueError("El cuerpo JSON debe ser un objeto")
    return datos


def _requerir_campos(datos: Dict[str, Any], campos: List[str]) -> None:
    faltantes = [campo for campo in campos if datos.get(campo) in (None, "")]
    if faltantes:
        raise ValueError(f"Faltan campos obligatorios: {', '.join(faltantes)}")


def _entero_opcional(valor: Any, nombre: str) -> Any:
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"El campo {nombre} debe ser un entero") from exc


def _resolver_metodo(
    funcion: Callable[..., Dict[str, Any]],
    *,
    iterativo: bool = False,
) -> tuple[Response, int]:
    try:
        datos = _obtener_payload()
        opciones: Dict[str, Any] = {
            "A": datos.get("A"),
            "b": datos.get("b"),
        }
        if iterativo:
            if datos.get("x0") is not None:
                opciones["x0"] = datos["x0"]
            if datos.get("tolerancia") is not None:
                opciones["tolerancia"] = float(datos["tolerancia"])
            if datos.get("max_iteraciones") is not None:
                opciones["max_iteraciones"] = int(datos["max_iteraciones"])

        resultado = funcion(**opciones)
        return _responder(resultado)
    except (ValueError, TypeError) as exc:
        return _responder({"error": str(exc)}, 400)
    except Exception:
        app.logger.exception("Error al ejecutar un método lineal")
        return _responder({"error": "Error interno al ejecutar el método"}, 500)


@app.route("/")
def servir_index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/salud")
@app.get("/api/health")
def salud() -> tuple[Response, int]:
    return _responder(
        {
            "estado": "ok",
            "base_datos": str(DB_PATH),
            "sistema_referencia": {"A": A_REFERENCIA, "b": B_REFERENCIA},
        }
    )


@app.get("/api/metodos")
def listar_metodos() -> tuple[Response, int]:
    return _responder(
        {
            "metodos": [
                {"nombre": "Solución exacta", "ruta": "/api/metodos/exacta", "tipo": "directo"},
                {"nombre": "Factorización LU", "ruta": "/api/metodos/lu", "tipo": "directo"},
                {"nombre": "Jacobi", "ruta": "/api/metodos/jacobi", "tipo": "iterativo"},
                {"nombre": "Gauss-Seidel", "ruta": "/api/metodos/gauss-seidel", "tipo": "iterativo"},
                {"nombre": "Gradiente conjugado", "ruta": "/api/metodos/gradiente-conjugado", "tipo": "iterativo"},
            ],
            "sistema_referencia": {"A": A_REFERENCIA, "b": B_REFERENCIA},
        }
    )


@app.post("/api/metodos/exacta")
def api_solucion_exacta() -> tuple[Response, int]:
    return _resolver_metodo(solucion_exacta)


@app.post("/api/metodos/lu")
def api_factorizacion_lu() -> tuple[Response, int]:
    return _resolver_metodo(factorizacion_lu)


@app.post("/api/metodos/jacobi")
def api_jacobi() -> tuple[Response, int]:
    return _resolver_metodo(jacobi, iterativo=True)


@app.post("/api/metodos/gauss-seidel")
def api_gauss_seidel() -> tuple[Response, int]:
    return _resolver_metodo(gauss_seidel, iterativo=True)


@app.post("/api/metodos/gradiente-conjugado")
def api_gradiente_conjugado() -> tuple[Response, int]:
    return _resolver_metodo(gradiente_conjugado, iterativo=True)


@app.get("/api/casos-estudio")
def api_casos_estudio() -> tuple[Response, int]:
    return _responder(obtener_casos_estudio())


@app.get("/api/escenarios")
def api_escenarios() -> tuple[Response, int]:
    try:
        caso_estudio_id = _entero_opcional(
            request.args.get("caso_estudio_id"), "caso_estudio_id"
        )
    except ValueError as exc:
        return _responder({"error": str(exc)}, 400)
    return _responder(obtener_escenarios(caso_estudio_id))


@app.post("/api/escenarios")
def api_crear_escenario() -> tuple[Response, int]:
    try:
        datos = _obtener_payload()
        _requerir_campos(datos, ["caso_estudio_id", "codigo", "nombre", "tipo"])

        activo = datos.get("activo", True)
        if not isinstance(activo, bool):
            raise ValueError("El campo activo debe ser booleano")

        escenario_id = crear_escenario(
            caso_estudio_id=int(datos["caso_estudio_id"]),
            codigo=str(datos["codigo"]),
            nombre=str(datos["nombre"]),
            descripcion=datos.get("descripcion"),
            tipo=str(datos["tipo"]),
            probabilidad=(
                None if datos.get("probabilidad") is None else float(datos["probabilidad"])
            ),
            severidad=datos.get("severidad"),
            parametros=datos.get("parametros"),
            activo=activo,
        )
        return _responder({"id": escenario_id}, 201)
    except (ValueError, TypeError) as exc:
        return _responder({"error": str(exc)}, 400)
    except sqlite3.IntegrityError as exc:
        return _responder(
            {"error": "No se pudo crear el escenario", "detalle": str(exc)}, 409
        )


@app.get("/api/simulaciones")
def api_listar_simulaciones() -> tuple[Response, int]:
    try:
        escenario_id = _entero_opcional(
            request.args.get("escenario_id"), "escenario_id"
        )
        limite = _entero_opcional(request.args.get("limite"), "limite")
        estado = request.args.get("estado") or None
        simulaciones = listar_simulaciones(
            escenario_id=escenario_id,
            estado=estado,
            limite=limite,
        )
    except ValueError as exc:
        return _responder({"error": str(exc)}, 400)
    return _responder(simulaciones)


@app.get("/api/simulaciones/<int:simulacion_id>")
def api_recuperar_simulacion(simulacion_id: int) -> tuple[Response, int]:
    simulacion = recuperar_simulacion(simulacion_id)
    if simulacion is None:
        return _responder({"error": "Simulación no encontrada"}, 404)
    return _responder(simulacion)


@app.post("/api/simulaciones")
def api_guardar_simulacion() -> tuple[Response, int]:
    try:
        datos = _obtener_payload()
        _requerir_campos(datos, ["escenario_id", "codigo", "nombre", "metodo"])

        simulacion_id = guardar_simulacion(
            escenario_id=int(datos["escenario_id"]),
            codigo=str(datos["codigo"]),
            nombre=str(datos["nombre"]),
            metodo=str(datos["metodo"]),
            descripcion=datos.get("descripcion"),
            version_modelo=datos.get("version_modelo"),
            numero_iteraciones=int(datos.get("numero_iteraciones", 10000)),
            semilla=_entero_opcional(datos.get("semilla"), "semilla"),
            nivel_confianza=float(datos.get("nivel_confianza", 0.95)),
            parametros=datos.get("parametros"),
            estado=datos.get("estado", "pendiente"),
            fecha_inicio=datos.get("fecha_inicio"),
            fecha_fin=datos.get("fecha_fin"),
        )
        simulacion = recuperar_simulacion(simulacion_id)
        return _responder(simulacion, 201)
    except (ValueError, TypeError) as exc:
        return _responder({"error": str(exc)}, 400)
    except sqlite3.IntegrityError as exc:
        return _responder(
            {"error": "No se pudo guardar la simulación", "detalle": str(exc)}, 409
        )


@app.errorhandler(404)
def recurso_no_encontrado(_: Any) -> tuple[Response, int]:
    return _responder({"error": "Recurso no encontrado"}, 404)


@app.errorhandler(405)
def metodo_no_permitido(_: Any) -> tuple[Response, int]:
    return _responder({"error": "Método HTTP no permitido"}, 405)


if __name__ == "__main__":
    app.run(
        host=os.environ.get("SIMTELE_HOST", "127.0.0.1"),
        port=int(os.environ.get("SIMTELE_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
