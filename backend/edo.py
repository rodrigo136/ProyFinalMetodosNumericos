"""Integradores de EDO: Heun de segundo orden y Runge-Kutta clásico de orden 4."""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

try:
    from .errores import error_absoluto, error_porcentual
except ImportError:
    from errores import error_absoluto, error_porcentual

Estado = Union[float, Sequence[float]]
FuncionEDO = Callable[[float, List[float]], Estado]
ReferenciaEDO = Callable[[float], Estado]


def _vector(valor: Estado) -> List[float]:
    resultado = [float(valor)] if isinstance(valor, (int, float)) else [float(x) for x in valor]
    if not resultado or any(not math.isfinite(x) for x in resultado):
        raise ValueError("El estado debe contener valores finitos")
    return resultado


def _derivada(funcion: FuncionEDO, t: float, y: List[float]) -> List[float]:
    salida = _vector(funcion(t, y[:]))
    if len(salida) != len(y):
        raise ValueError("La derivada debe tener la misma dimensión que el estado")
    return salida


def _combinar(y: List[float], h: float, terminos: Sequence[tuple[float, List[float]]]) -> List[float]:
    resultado = [y[i] + h * math.fsum(coeficiente * valor[i] for coeficiente, valor in terminos) for i in range(len(y))]
    if any(not math.isfinite(x) for x in resultado):
        raise ValueError("La integración produjo un estado no finito")
    return resultado


def _errores(ref: Optional[List[float]], y: List[float]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    if ref is None:
        return None, None, None
    diferencias = [error_absoluto(ref[i], y[i]) for i in range(len(y))]
    absoluto = math.sqrt(math.fsum(x * x for x in diferencias))
    norma_ref = math.sqrt(math.fsum(x * x for x in ref))
    if norma_ref == 0.0:
        return absoluto, None, None
    relativo = absoluto / norma_ref
    return absoluto, relativo, error_porcentual(1.0, 1.0 + relativo)


def resolver_edo(
    funcion: FuncionEDO,
    intervalo: Sequence[float],
    inicial: Estado,
    pasos: int,
    *,
    metodo: str = "rk4",
    referencia: Optional[ReferenciaEDO] = None,
) -> Dict[str, Any]:
    """Resuelve una EDO/sistema en una malla uniforme, con método Heun o RK4."""
    if len(intervalo) != 2:
        raise ValueError("El intervalo debe tener dos extremos")
    t0, tf = float(intervalo[0]), float(intervalo[1])
    if not math.isfinite(t0) or not math.isfinite(tf) or tf <= t0:
        raise ValueError("El intervalo debe ser finito y cumplir t_final > t_inicial")
    if not isinstance(pasos, int) or pasos < 1 or pasos > 10000:
        raise ValueError("El número de pasos debe estar entre 1 y 10000")
    clave = metodo.strip().lower()
    if clave not in {"rk2", "heun", "rk4"}:
        raise ValueError("El método debe ser rk2 (Heun) o rk4")
    h = (tf - t0) / pasos
    y = _vector(inicial)
    filas: List[Dict[str, Any]] = []

    def agregar(fila_t: float, estado: List[float]) -> None:
        ref = _vector(referencia(fila_t)) if referencia is not None else None
        if ref is not None and len(ref) != len(estado):
            raise ValueError("La referencia debe tener la misma dimensión que el estado")
        ea, er, ep = _errores(ref, estado)
        filas.append({
            "t": fila_t,
            "aproximacion": estado[0] if len(estado) == 1 else estado[:],
            "referencia": None if ref is None else (ref[0] if len(ref) == 1 else ref),
            "error_absoluto": ea,
            "error_relativo": er,
            "error_porcentual": ep,
        })

    agregar(t0, y)
    for i in range(pasos):
        t = t0 + i * h
        k1 = _derivada(funcion, t, y)
        if clave in {"rk2", "heun"}:
            predictor = _combinar(y, h, [(1.0, k1)])
            k2 = _derivada(funcion, t + h, predictor)
            y = _combinar(y, h, [(0.5, k1), (0.5, k2)])
        else:
            k2 = _derivada(funcion, t + h / 2.0, _combinar(y, h, [(0.5, k1)]))
            k3 = _derivada(funcion, t + h / 2.0, _combinar(y, h, [(0.5, k2)]))
            k4 = _derivada(funcion, t + h, _combinar(y, h, [(1.0, k3)]))
            y = _combinar(y, h, [(1.0 / 6.0, k1), (1.0 / 3.0, k2), (1.0 / 3.0, k3), (1.0 / 6.0, k4)])
        agregar(t0 + (i + 1) * h, y)

    estados = [
        valor
        for fila in filas
        for valor in (
            fila["aproximacion"]
            if isinstance(fila["aproximacion"], list)
            else [fila["aproximacion"]]
        )
    ]
    escala_inicial = max((abs(valor) for valor in _vector(inicial)), default=1.0)
    estable = all(math.isfinite(valor) for valor in estados) and max(
        (abs(valor) for valor in estados), default=0.0
    ) <= max(1.0, escala_inicial) * 1e6
    fila_final = filas[-1]
    return {
        "metodo": "Heun (Runge-Kutta de 2.º orden)" if clave in {"rk2", "heun"} else "Runge-Kutta clásico de 4.º orden",
        "tabla_temporal": filas,
        "valor_final": fila_final["aproximacion"],
        "valor_referencia": fila_final["referencia"],
        "error_absoluto_final": fila_final["error_absoluto"],
        "error_relativo_final": fila_final["error_relativo"],
        "error_porcentual_final": fila_final["error_porcentual"],
        "iteraciones_totales": pasos,
        "convergio": True,
        "estable": estable,
        "mensaje": "Integración completada; la trayectoria permanece acotada en la escala inicial." if estable else "La integración completó los pasos, pero presenta crecimiento excesivo; esto se informa como inestabilidad numérica, no como falta de convergencia iterativa.",
    }
