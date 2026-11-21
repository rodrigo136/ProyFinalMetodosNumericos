"""Cuadraturas compuestas y extrapolación de Richardson."""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional

try:
    from .errores import error_absoluto, error_porcentual, error_relativo
except ImportError:
    from errores import error_absoluto, error_porcentual, error_relativo

Funcion = Callable[[float], float]


def _evaluar(funcion: Funcion, x: float) -> float:
    valor = float(funcion(x))
    if not math.isfinite(valor):
        raise ValueError("La función integranda produjo un valor no finito")
    return valor


def _validar(a: float, b: float, n: int) -> tuple[float, float]:
    a, b = float(a), float(b)
    if not math.isfinite(a) or not math.isfinite(b) or a == b:
        raise ValueError("Los extremos deben ser finitos y distintos")
    if not isinstance(n, int) or n < 1:
        raise ValueError("El número de subintervalos debe ser un entero positivo")
    return a, b


def _errores(referencia: Optional[float], aproximacion: float) -> Dict[str, Optional[float]]:
    if referencia is None:
        return {"error_absoluto_final": None, "error_relativo_final": None, "error_porcentual_final": None}
    referencia = float(referencia)
    if not math.isfinite(referencia):
        raise ValueError("La referencia debe ser finita")
    absoluto = error_absoluto(referencia, aproximacion)
    try:
        relativo = error_relativo(referencia, aproximacion)
        porcentual = error_porcentual(referencia, aproximacion)
    except ValueError:
        relativo = porcentual = None
    return {"error_absoluto_final": absoluto, "error_relativo_final": relativo, "error_porcentual_final": porcentual}


def _fila(n: int, paso: float, nivel: int, aproximacion: float, referencia: Optional[float]) -> Dict[str, Any]:
    absoluto: Optional[float] = None
    relativo: Optional[float] = None
    porcentual: Optional[float] = None
    if referencia is not None:
        absoluto = error_absoluto(referencia, aproximacion)
        try:
            relativo = error_relativo(referencia, aproximacion)
            porcentual = error_porcentual(referencia, aproximacion)
        except ValueError:
            pass
    return {
        "subintervalos": n,
        "paso": paso,
        "nivel": nivel,
        "aproximacion": aproximacion,
        "error_absoluto": absoluto,
        "error_relativo": relativo,
        "error_porcentual": porcentual,
    }


def _resultado(metodo: str, valor: float, filas: List[Dict[str, Any]], referencia: Optional[float]) -> Dict[str, Any]:
    return {
        "metodo": metodo,
        "integral_aproximada": valor,
        "valor_referencia": referencia,
        "tabla_refinamiento": filas,
        "convergio": bool(filas),
        "iteraciones_totales": len(filas),
        **_errores(referencia, valor),
    }


def _nodos_refinamiento(n: int, par: bool = False) -> List[int]:
    minimo = 2 if par else 1
    valores = []
    actual = minimo
    while actual < n:
        valores.append(actual)
        actual *= 2
    if not valores or valores[-1] != n:
        valores.append(n)
    return valores


def _trapecio(funcion: Funcion, a: float, b: float, n: int) -> float:
    h = (b - a) / n
    interior = math.fsum(_evaluar(funcion, a + i * h) for i in range(1, n))
    return h * ((_evaluar(funcion, a) + _evaluar(funcion, b)) / 2.0 + interior)


def _simpson(funcion: Funcion, a: float, b: float, n: int) -> float:
    h = (b - a) / n
    suma_impares = math.fsum(_evaluar(funcion, a + i * h) for i in range(1, n, 2))
    suma_pares = math.fsum(_evaluar(funcion, a + i * h) for i in range(2, n, 2))
    return h / 3.0 * (_evaluar(funcion, a) + _evaluar(funcion, b) + 4.0 * suma_impares + 2.0 * suma_pares)


def trapecio_compuesto(
    funcion: Funcion,
    a: float,
    b: float,
    n: int,
    *,
    referencia: Optional[float] = None,
) -> Dict[str, Any]:
    """Integra con la regla compuesta del trapecio."""
    a, b = _validar(a, b, n)
    filas = []
    for nivel, cantidad in enumerate(_nodos_refinamiento(n)):
        h = (b - a) / cantidad
        valor_nivel = _trapecio(funcion, a, b, cantidad)
        if not math.isfinite(valor_nivel):
            raise ValueError("La cuadratura produjo un resultado no finito")
        filas.append(_fila(cantidad, h, nivel, valor_nivel, referencia))
    return _resultado("Trapecio compuesto", filas[-1]["aproximacion"], filas, referencia)


def simpson_13_compuesto(
    funcion: Funcion,
    a: float,
    b: float,
    n: int,
    *,
    referencia: Optional[float] = None,
) -> Dict[str, Any]:
    """Integra mediante Simpson 1/3 compuesto, con n par."""
    a, b = _validar(a, b, n)
    if n % 2:
        raise ValueError("Simpson 1/3 compuesto requiere un número par de subintervalos")
    filas = []
    for nivel, cantidad in enumerate(_nodos_refinamiento(n, par=True)):
        h = (b - a) / cantidad
        valor_nivel = _simpson(funcion, a, b, cantidad)
        if not math.isfinite(valor_nivel):
            raise ValueError("La cuadratura produjo un resultado no finito")
        filas.append(_fila(cantidad, h, nivel, valor_nivel, referencia))
    return _resultado("Simpson 1/3 compuesto", filas[-1]["aproximacion"], filas, referencia)


def romberg(
    funcion: Funcion,
    a: float,
    b: float,
    *,
    niveles: int = 6,
    referencia: Optional[float] = None,
) -> Dict[str, Any]:
    """Construye la tabla de Romberg con pasos sucesivamente divididos por dos."""
    a, b = float(a), float(b)
    if not math.isfinite(a) or not math.isfinite(b) or a == b:
        raise ValueError("Los extremos deben ser finitos y distintos")
    if not isinstance(niveles, int) or niveles < 1 or niveles > 12:
        raise ValueError("Los niveles de Romberg deben estar entre 1 y 12")
    if referencia is not None and not math.isfinite(float(referencia)):
        raise ValueError("La referencia debe ser finita")

    tabla: List[List[float]] = []
    filas: List[Dict[str, Any]] = []
    for nivel in range(niveles):
        n = 2 ** nivel
        h = (b - a) / n
        if nivel == 0:
            actual = [h * (_evaluar(funcion, a) + _evaluar(funcion, b)) / 2.0]
        else:
            suma_nuevos = math.fsum(_evaluar(funcion, a + (2 * j - 1) * h) for j in range(1, n // 2 + 1))
            actual = [tabla[-1][0] / 2.0 + h * suma_nuevos]
            for orden in range(1, nivel + 1):
                factor = 4 ** orden
                actual.append(actual[orden - 1] + (actual[orden - 1] - tabla[-1][orden - 1]) / (factor - 1))
        if any(not math.isfinite(valor) for valor in actual):
            raise ValueError("La extrapolación de Romberg produjo valores no finitos")
        tabla.append(actual)
        filas.append(_fila(n, h, nivel, actual[-1], referencia))

    return {
        **_resultado("Romberg", tabla[-1][-1], filas, referencia),
        "tabla_romberg": tabla,
    }
