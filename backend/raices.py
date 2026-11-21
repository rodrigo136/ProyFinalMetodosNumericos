"""Métodos reproducibles para resolver ecuaciones escalares no lineales."""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional

try:
    from .errores import error_absoluto, error_porcentual, error_relativo
except ImportError:
    from errores import error_absoluto, error_porcentual, error_relativo

Funcion = Callable[[float], float]
Derivada = Callable[[float], float]


def _evaluar(funcion: Funcion, x: float) -> float:
    valor = float(funcion(x))
    if not math.isfinite(valor):
        raise ValueError("La función produjo un valor no finito")
    return valor


def _error_entre(actual: float, anterior: Optional[float]) -> tuple[float, float, float]:
    if anterior is None:
        return 0.0, 0.0, 0.0
    absoluto = error_absoluto(anterior, actual)
    relativo = absoluto / abs(actual) if actual != 0.0 else (0.0 if absoluto == 0.0 else math.inf)
    return absoluto, relativo, relativo * 100.0


def _errores_referencia(referencia: Optional[float], aproximacion: float) -> Dict[str, Optional[float]]:
    if referencia is None or not math.isfinite(referencia):
        return {"error_absoluto_final": None, "error_relativo_final": None, "error_porcentual_final": None}
    absoluto = error_absoluto(referencia, aproximacion)
    try:
        relativo = error_relativo(referencia, aproximacion)
        porcentual = error_porcentual(referencia, aproximacion)
    except ValueError:
        relativo = porcentual = None
    return {
        "error_absoluto_final": absoluto,
        "error_relativo_final": relativo,
        "error_porcentual_final": porcentual,
    }


def _resultado(
    metodo: str,
    raiz: float,
    referencia: Optional[float],
    filas: List[Dict[str, Any]],
    convergio: bool,
    mensaje: str,
    funcion: Funcion,
) -> Dict[str, Any]:
    ultima = filas[-1] if filas else {}
    return {
        "metodo": metodo,
        "raiz_aproximada": raiz,
        "valor_referencia": referencia,
        "residual_final": abs(_evaluar(funcion, raiz)),
        "iteraciones": filas,
        "iteraciones_totales": len(filas),
        "convergio": convergio,
        "mensaje": mensaje,
        **_errores_referencia(referencia, raiz),
        "error_iteracion_final": ultima.get("error_absoluto", 0.0),
    }


def _fila(
    iteracion: int,
    aproximacion: float,
    anterior: Optional[float],
    residual: float,
) -> Dict[str, Any]:
    absoluto, relativo, porcentual = _error_entre(aproximacion, anterior)
    return {
        "iteracion": iteracion,
        "aproximacion": aproximacion,
        "error_absoluto": absoluto,
        "error_relativo": relativo,
        "error_porcentual": porcentual,
        "residual": residual,
    }


def _validar(tolerancia: float, max_iteraciones: int) -> None:
    if not math.isfinite(tolerancia) or tolerancia <= 0.0:
        raise ValueError("La tolerancia debe ser finita y mayor que cero")
    if max_iteraciones < 1:
        raise ValueError("El máximo de iteraciones debe ser positivo")


def biseccion(
    funcion: Funcion,
    a: float,
    b: float,
    *,
    tolerancia: float = 1e-10,
    max_iteraciones: int = 200,
    referencia: Optional[float] = None,
) -> Dict[str, Any]:
    """Calcula una raíz en un intervalo que debe encerrar un cambio de signo."""
    _validar(tolerancia, max_iteraciones)
    a, b = float(a), float(b)
    if not math.isfinite(a) or not math.isfinite(b) or a >= b:
        raise ValueError("El intervalo debe contener extremos finitos con a < b")
    fa, fb = _evaluar(funcion, a), _evaluar(funcion, b)
    if fa == 0.0:
        return _resultado("Bisección", a, referencia, [_fila(0, a, None, 0.0)], True, "Raíz encontrada en el extremo izquierdo.", funcion)
    if fb == 0.0:
        return _resultado("Bisección", b, referencia, [_fila(0, b, None, 0.0)], True, "Raíz encontrada en el extremo derecho.", funcion)
    if fa * fb > 0.0:
        raise ValueError("El intervalo no encierra un cambio de signo")

    filas: List[Dict[str, Any]] = []
    anterior: Optional[float] = None
    convergio = False
    raiz = (a + b) / 2.0
    for k in range(1, max_iteraciones + 1):
        raiz = a + (b - a) / 2.0
        fr = _evaluar(funcion, raiz)
        filas.append(_fila(k, raiz, anterior, abs(fr)))
        if abs(fr) <= tolerancia or (b - a) / 2.0 <= tolerancia:
            convergio = True
            break
        if fa * fr < 0.0:
            b, fb = raiz, fr
        else:
            a, fa = raiz, fr
        anterior = raiz
    return _resultado("Bisección", raiz, referencia, filas, convergio, "Convergió dentro de la tolerancia." if convergio else "Se alcanzó el máximo de iteraciones.", funcion)


def newton_raphson(
    funcion: Funcion,
    derivada: Derivada,
    x0: float,
    *,
    tolerancia: float = 1e-10,
    max_iteraciones: int = 100,
    referencia: Optional[float] = None,
) -> Dict[str, Any]:
    """Resuelve con Newton-Raphson; rechaza derivadas nulas o no finitas."""
    _validar(tolerancia, max_iteraciones)
    x = float(x0)
    if not math.isfinite(x):
        raise ValueError("La aproximación inicial debe ser finita")
    filas: List[Dict[str, Any]] = []
    convergio = False
    for k in range(1, max_iteraciones + 1):
        fx = _evaluar(funcion, x)
        dfx = float(derivada(x))
        if not math.isfinite(dfx):
            raise ValueError("La derivada produjo un valor no finito")
        if dfx == 0.0:
            raise ValueError("La derivada es cero; Newton-Raphson no puede continuar")
        siguiente = x - fx / dfx
        if not math.isfinite(siguiente):
            raise ValueError("Newton-Raphson produjo una aproximación no finita")
        residual = abs(_evaluar(funcion, siguiente))
        filas.append(_fila(k, siguiente, x, residual))
        cambio = abs(siguiente - x)
        x = siguiente
        if cambio <= tolerancia * max(1.0, abs(x)) or residual <= tolerancia:
            convergio = True
            break
    return _resultado("Newton-Raphson", x, referencia, filas, convergio, "Convergió dentro de la tolerancia." if convergio else "Se alcanzó el máximo de iteraciones.", funcion)


def secante(
    funcion: Funcion,
    x0: float,
    x1: float,
    *,
    tolerancia: float = 1e-10,
    max_iteraciones: int = 100,
    referencia: Optional[float] = None,
) -> Dict[str, Any]:
    """Resuelve con secante sin requerir una derivada explícita."""
    _validar(tolerancia, max_iteraciones)
    anterior, actual = float(x0), float(x1)
    if not math.isfinite(anterior) or not math.isfinite(actual) or anterior == actual:
        raise ValueError("Las aproximaciones iniciales deben ser finitas y distintas")
    f_anterior, f_actual = _evaluar(funcion, anterior), _evaluar(funcion, actual)
    filas: List[Dict[str, Any]] = []
    convergio = False
    for k in range(1, max_iteraciones + 1):
        denominador = f_actual - f_anterior
        if denominador == 0.0:
            raise ValueError("Las evaluaciones de la función coinciden; la secante no puede continuar")
        siguiente = actual - f_actual * (actual - anterior) / denominador
        if not math.isfinite(siguiente):
            raise ValueError("La secante produjo una aproximación no finita")
        f_siguiente = _evaluar(funcion, siguiente)
        filas.append(_fila(k, siguiente, actual, abs(f_siguiente)))
        cambio = abs(siguiente - actual)
        anterior, actual = actual, siguiente
        f_anterior, f_actual = f_actual, f_siguiente
        if cambio <= tolerancia * max(1.0, abs(actual)) or abs(f_actual) <= tolerancia:
            convergio = True
            break
    return _resultado("Secante", actual, referencia, filas, convergio, "Convergió dentro de la tolerancia." if convergio else "Se alcanzó el máximo de iteraciones.", funcion)
