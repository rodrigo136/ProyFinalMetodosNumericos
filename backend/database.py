"""Conexión y operaciones de persistencia para SIMTELE-RISK (SQLite)."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR.parent / "database" / "schema.sql"

_DB_PATH_ENV = os.environ.get("SIMTELE_RISK_DB")
DB_PATH = Path(_DB_PATH_ENV) if _DB_PATH_ENV else BASE_DIR / "simtele_risk.db"

MATRIZ_A_MODULO_2 = [
    [10, 2, 1, 0],
    [2, 10, 1, 1],
    [1, 1, 8, 2],
    [0, 1, 2, 9],
]

VECTOR_B_MODULO_2 = [13, 24, 31, 28]

CASOS_ESTUDIO = (
    {
        "codigo": "CE-001",
        "nombre": "Detención de emergencia de cabinas",
        "descripcion": (
            "Evaluación de la detención automática y manual de cabinas "
            "ante condiciones de emergencia."
        ),
        "sector": "Operación de Cabinas",
        "responsable": "Centro de Control de Operaciones",
        "estado": "activo",
        "fecha_inicio": "2026-01-15",
    },
    {
        "codigo": "CE-002",
        "nombre": "Deterioro mecánico y mantenimiento",
        "descripcion": (
            "Análisis del desgaste mecánico y de las acciones de "
            "mantenimiento preventivo y correctivo."
        ),
        "sector": "Mantenimiento Mecánico",
        "responsable": "Dirección de Mantenimiento",
        "estado": "activo",
        "fecha_inicio": "2026-02-01",
    },
    {
        "codigo": "CE-003",
        "nombre": "Oscilación por viento",
        "descripcion": (
            "Simulación de la oscilación de cabinas y estructuras por "
            "efecto del viento."
        ),
        "sector": "Operación y Clima",
        "responsable": "Dirección de Operaciones",
        "estado": "activo",
        "fecha_inicio": "2026-03-01",
    },
    {
        "codigo": "CE-004",
        "nombre": "Reconstrucción de señales de sensores",
        "descripcion": (
            "Reconstrucción de señales de sensores a partir de lecturas "
            "incompletas o con ruido."
        ),
        "sector": "Instrumentación y Sensores",
        "responsable": "Área de Instrumentación",
        "estado": "activo",
        "fecha_inicio": "2026-04-01",
    },
)

ESCENARIOS_CASO = (
    {
        "codigo": "NORMAL",
        "nombre": "Normal",
        "descripcion": "Condiciones normales de operación del sistema.",
        "tipo": "base",
        "probabilidad": 0.70,
        "severidad": "baja",
        "parametros": {"A": MATRIZ_A_MODULO_2, "b": VECTOR_B_MODULO_2},
    },
    {
        "codigo": "ESTRES",
        "nombre": "Estres",
        "descripcion": "Condiciones exigentes que llevan el sistema al límite.",
        "tipo": "estres",
        "probabilidad": 0.25,
        "severidad": "alta",
        "parametros": {},
    },
    {
        "codigo": "MAL_CONDICIONADO",
        "nombre": "Mal condicionado",
        "descripcion": (
            "Condiciones adversas con alta sensibilidad a pequeños cambios."
        ),
        "tipo": "personalizado",
        "probabilidad": 0.05,
        "severidad": "critica",
        "parametros": {},
    },
)


def get_connection() -> sqlite3.Connection:
    """Crea una conexión SQLite con claves foráneas habilitadas."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _tabla_existe(connection: sqlite3.Connection, nombre: str) -> bool:
    fila = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (nombre,),
    ).fetchone()
    return fila is not None


def _serializar_json(valor: Any) -> str:
    if valor is None:
        return "{}"
    if isinstance(valor, str):
        try:
            json.loads(valor)
        except json.JSONDecodeError as exc:
            raise ValueError("El valor debe contener JSON válido") from exc
        return valor
    return json.dumps(valor, ensure_ascii=False)


def _deserializar_json(valor: Any, por_defecto: Any = None) -> Any:
    if valor is None:
        return por_defecto
    try:
        return json.loads(valor)
    except (TypeError, json.JSONDecodeError):
        return por_defecto


def _insertar_datos_iniciales(connection: sqlite3.Connection) -> Dict[str, int]:
    casos_insertados = 0
    escenarios_insertados = 0

    for caso in CASOS_ESTUDIO:
        fila = connection.execute(
            "SELECT id FROM caso_estudio WHERE codigo = ?",
            (caso["codigo"],),
        ).fetchone()

        if fila is None:
            cursor = connection.execute(
                """
                INSERT INTO caso_estudio
                    (codigo, nombre, descripcion, sector, responsable,
                     estado, fecha_inicio)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    caso["codigo"],
                    caso["nombre"],
                    caso["descripcion"],
                    caso["sector"],
                    caso["responsable"],
                    caso["estado"],
                    caso["fecha_inicio"],
                ),
            )
            casos_insertados += cursor.rowcount
            caso_estudio_id = int(cursor.lastrowid)
        else:
            caso_estudio_id = int(fila["id"])
            connection.execute(
                """
                UPDATE caso_estudio
                SET nombre = ?, descripcion = ?, sector = ?, responsable = ?,
                    estado = ?, fecha_inicio = ?
                WHERE id = ?
                """,
                (
                    caso["nombre"],
                    caso["descripcion"],
                    caso["sector"],
                    caso["responsable"],
                    caso["estado"],
                    caso["fecha_inicio"],
                    caso_estudio_id,
                ),
            )

        normal = ESCENARIOS_CASO[0]
        normal_existente = connection.execute(
            "SELECT id FROM escenario WHERE caso_estudio_id = ? AND codigo = ?",
            (caso_estudio_id, normal["codigo"]),
        ).fetchone()
        if normal_existente is None:
            base_legado = connection.execute(
                "SELECT id FROM escenario WHERE caso_estudio_id = ? AND codigo = 'BASE'",
                (caso_estudio_id,),
            ).fetchone()
            if base_legado is not None:
                connection.execute(
                    """
                    UPDATE escenario
                    SET codigo = ?, nombre = ?, descripcion = ?, tipo = ?,
                        probabilidad = ?, severidad = ?, parametros = ?
                    WHERE id = ?
                    """,
                    (
                        normal["codigo"],
                        normal["nombre"],
                        normal["descripcion"],
                        normal["tipo"],
                        normal["probabilidad"],
                        normal["severidad"],
                        _serializar_json(normal["parametros"]),
                        base_legado["id"],
                    ),
                )
        else:
            connection.execute(
                "DELETE FROM escenario WHERE caso_estudio_id = ? AND codigo = 'BASE'",
                (caso_estudio_id,),
            )

        for escenario in ESCENARIOS_CASO:
            existente = connection.execute(
                "SELECT id FROM escenario WHERE caso_estudio_id = ? AND codigo = ?",
                (caso_estudio_id, escenario["codigo"]),
            ).fetchone()
            valores = (
                escenario["nombre"],
                escenario["descripcion"],
                escenario["tipo"],
                escenario["probabilidad"],
                escenario["severidad"],
                _serializar_json(escenario["parametros"]),
            )
            if existente is None:
                cursor = connection.execute(
                    """
                    INSERT INTO escenario
                        (caso_estudio_id, codigo, nombre, descripcion, tipo,
                         probabilidad, severidad, parametros)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (caso_estudio_id, escenario["codigo"]) + valores,
                )
                escenarios_insertados += cursor.rowcount
            else:
                connection.execute(
                    """
                    UPDATE escenario
                    SET nombre = ?, descripcion = ?, tipo = ?, probabilidad = ?,
                        severidad = ?, parametros = ?
                    WHERE id = ?
                    """,
                    valores + (existente["id"],),
                )

        codigos_validos = [escenario["codigo"] for escenario in ESCENARIOS_CASO]
        marcadores = ", ".join("?" for _ in codigos_validos)
        connection.execute(
            f"""
            DELETE FROM escenario
            WHERE caso_estudio_id = ? AND codigo NOT IN ({marcadores})
            """,
            (caso_estudio_id, *codigos_validos),
        )

    return {
        "casos_insertados": casos_insertados,
        "escenarios_insertados": escenarios_insertados,
    }


def inicializar_base_datos(sembrar: bool = True) -> Dict[str, int]:
    """Crea el esquema si no existe y carga los casos de estudio iniciales."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No se encontró el esquema: {SCHEMA_PATH}")

    with closing(get_connection()) as connection:
        esquema_creado = 0
        if not _tabla_existe(connection, "caso_estudio"):
            connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            esquema_creado = 1

        resultado = {"casos_insertados": 0, "escenarios_insertados": 0}
        if sembrar:
            resultado = _insertar_datos_iniciales(connection)
            connection.commit()

        resultado["esquema_creado"] = esquema_creado
        return resultado


def obtener_casos_estudio() -> List[Dict[str, Any]]:
    with closing(get_connection()) as connection:
        filas = connection.execute(
            "SELECT * FROM caso_estudio ORDER BY codigo"
        ).fetchall()
        return [dict(fila) for fila in filas]


def obtener_escenarios(caso_estudio_id: Optional[int] = None) -> List[Dict[str, Any]]:
    sql = """
        SELECT e.*, c.codigo AS caso_codigo, c.nombre AS caso_nombre
        FROM escenario e
        JOIN caso_estudio c ON c.id = e.caso_estudio_id
    """
    parametros: List[Any] = []
    if caso_estudio_id is not None:
        sql += " WHERE e.caso_estudio_id = ?"
        parametros.append(caso_estudio_id)
    sql += " ORDER BY c.codigo, e.codigo"

    with closing(get_connection()) as connection:
        filas = connection.execute(sql, parametros).fetchall()
        escenarios = []
        for fila in filas:
            escenario = dict(fila)
            escenario["parametros"] = _deserializar_json(escenario["parametros"], {})
            escenarios.append(escenario)
        return escenarios


def crear_escenario(
    caso_estudio_id: int,
    codigo: str,
    nombre: str,
    *,
    descripcion: Optional[str] = None,
    tipo: str = "base",
    probabilidad: Optional[float] = None,
    severidad: Optional[str] = None,
    parametros: Any = None,
    activo: bool = True,
) -> int:
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO escenario
                    (caso_estudio_id, codigo, nombre, descripcion, tipo,
                     probabilidad, severidad, parametros, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    caso_estudio_id,
                    codigo,
                    nombre,
                    descripcion,
                    tipo,
                    probabilidad,
                    severidad,
                    _serializar_json(parametros),
                    int(activo),
                ),
            )
        return int(cursor.lastrowid)


def guardar_simulacion(
    escenario_id: int,
    codigo: str,
    nombre: str,
    metodo: str,
    *,
    descripcion: Optional[str] = None,
    version_modelo: Optional[str] = None,
    numero_iteraciones: int = 10000,
    semilla: Optional[int] = None,
    nivel_confianza: float = 0.95,
    parametros: Any = None,
    estado: str = "pendiente",
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
) -> int:
    """Guarda una simulación y devuelve su identificador."""
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO simulacion
                    (escenario_id, codigo, nombre, descripcion, metodo,
                     version_modelo, numero_iteraciones, semilla,
                     nivel_confianza, parametros, estado, fecha_inicio, fecha_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    escenario_id,
                    codigo,
                    nombre,
                    descripcion,
                    metodo,
                    version_modelo,
                    numero_iteraciones,
                    semilla,
                    nivel_confianza,
                    _serializar_json(parametros),
                    estado,
                    fecha_inicio,
                    fecha_fin,
                ),
            )
        return int(cursor.lastrowid)


_SQL_SIMULACION = """
    SELECT
        s.*,
        e.codigo AS escenario_codigo,
        e.nombre AS escenario_nombre,
        e.tipo AS escenario_tipo,
        e.probabilidad AS escenario_probabilidad,
        e.severidad AS escenario_severidad,
        e.parametros AS escenario_parametros,
        c.id AS caso_estudio_id,
        c.codigo AS caso_codigo,
        c.nombre AS caso_nombre
    FROM simulacion s
    JOIN escenario e ON e.id = s.escenario_id
    JOIN caso_estudio c ON c.id = e.caso_estudio_id
"""


def _simulacion_desde_fila(fila: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": fila["id"],
        "codigo": fila["codigo"],
        "nombre": fila["nombre"],
        "descripcion": fila["descripcion"],
        "metodo": fila["metodo"],
        "version_modelo": fila["version_modelo"],
        "numero_iteraciones": fila["numero_iteraciones"],
        "semilla": fila["semilla"],
        "nivel_confianza": fila["nivel_confianza"],
        "parametros": _deserializar_json(fila["parametros"], {}),
        "estado": fila["estado"],
        "fecha_inicio": fila["fecha_inicio"],
        "fecha_fin": fila["fecha_fin"],
        "created_at": fila["created_at"],
        "updated_at": fila["updated_at"],
        "escenario": {
            "id": fila["escenario_id"],
            "codigo": fila["escenario_codigo"],
            "nombre": fila["escenario_nombre"],
            "tipo": fila["escenario_tipo"],
            "probabilidad": fila["escenario_probabilidad"],
            "severidad": fila["escenario_severidad"],
            "parametros": _deserializar_json(fila["escenario_parametros"], {}),
        },
        "caso_estudio": {
            "id": fila["caso_estudio_id"],
            "codigo": fila["caso_codigo"],
            "nombre": fila["caso_nombre"],
        },
    }


def recuperar_simulacion(simulacion_id: int) -> Optional[Dict[str, Any]]:
    with closing(get_connection()) as connection:
        fila = connection.execute(
            f"{_SQL_SIMULACION} WHERE s.id = ?",
            (simulacion_id,),
        ).fetchone()
        return _simulacion_desde_fila(fila) if fila is not None else None


def listar_simulaciones(
    escenario_id: Optional[int] = None,
    estado: Optional[str] = None,
    limite: Optional[int] = None,
) -> List[Dict[str, Any]]:
    sql = f"{_SQL_SIMULACION} WHERE 1 = 1"
    parametros: List[Any] = []

    if escenario_id is not None:
        sql += " AND s.escenario_id = ?"
        parametros.append(escenario_id)
    if estado is not None:
        sql += " AND s.estado = ?"
        parametros.append(estado)
    sql += " ORDER BY s.id DESC"
    if limite is not None:
        if limite < 1:
            raise ValueError("El límite debe ser mayor que cero")
        sql += " LIMIT ?"
        parametros.append(limite)

    with closing(get_connection()) as connection:
        filas = connection.execute(sql, parametros).fetchall()
        return [_simulacion_desde_fila(fila) for fila in filas]


init_db = inicializar_base_datos
save_simulation = guardar_simulacion
get_simulation = recuperar_simulacion
list_simulations = listar_simulaciones


if __name__ == "__main__":
    resultado = inicializar_base_datos()
    print(f"Base de datos: {DB_PATH}")
    print(f"Esquema creado: {bool(resultado['esquema_creado'])}")
    print(f"Casos insertados: {resultado['casos_insertados']}")
    print(f"Escenarios insertados: {resultado['escenarios_insertados']}")
    for caso in obtener_casos_estudio():
        print(f"- {caso['codigo']}: {caso['nombre']}")
