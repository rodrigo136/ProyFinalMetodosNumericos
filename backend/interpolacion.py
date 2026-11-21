"""Interpolación polinómica y spline cúbico natural para señales tabuladas."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

try:
    from .errores import error_absoluto, error_porcentual, error_relativo
except ImportError:
    from errores import error_absoluto, error_porcentual, error_relativo


def _validar_nodos(x: Sequence[float], y: Sequence[float]) -> tuple[List[float], List[float]]:
    try:
        xs, ys = [float(v) for v in x], [float(v) for v in y]
    except (TypeError, ValueError) as exc:
        raise ValueError("Los nodos deben ser secuencias numéricas") from exc
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Se requieren al menos dos pares de nodos")
    if any(not math.isfinite(v) for v in xs + ys):
        raise ValueError("Los nodos deben ser finitos")
    if any(xs[i] >= xs[i + 1] for i in range(len(xs) - 1)):
        raise ValueError("Los nodos x deben ser estrictamente crecientes y distintos")
    return xs, ys


def _puntos(puntos: Sequence[float]) -> List[float]:
    try:
        resultado = [float(v) for v in puntos]
    except (TypeError, ValueError) as exc:
        raise ValueError("Los puntos de evaluación deben ser numéricos") from exc
    if any(not math.isfinite(v) for v in resultado):
        raise ValueError("Los puntos de evaluación deben ser finitos")
    return resultado


def _tabla_resultado(
    nombre: str,
    xs: List[float],
    ys: List[float],
    puntos: List[float],
    valores: List[float],
    referencia: Optional[Sequence[float]],
    tabla: Optional[List[List[float]]] = None,
) -> Dict[str, Any]:
    if referencia is not None:
        refs = _puntos(referencia)
        if len(refs) != len(puntos):
            raise ValueError("La referencia debe tener un valor por cada punto evaluado")
        filas = []
        for x, valor, ref in zip(puntos, valores, refs):
            absoluto = error_absoluto(ref, valor)
            try:
                relativo = error_relativo(ref, valor)
                porcentual = error_porcentual(ref, valor)
            except ValueError:
                relativo = porcentual = None
            filas.append({
                "x": x,
                "aproximacion": valor,
                "referencia": ref,
                "error_absoluto": absoluto,
                "error_relativo": relativo,
                "error_porcentual": porcentual,
            })
        errores = [fila["error_absoluto"] for fila in filas]
        error_final = math.sqrt(math.fsum(v * v for v in errores))
        norma_ref = math.sqrt(math.fsum(v * v for v in refs))
        if norma_ref:
            error_rel_final = error_relativo(norma_ref, norma_ref + error_final)
            error_pct_final = error_porcentual(norma_ref, norma_ref + error_final)
        else:
            error_rel_final = error_pct_final = None
    else:
        filas = [{"x": x, "aproximacion": valor, "referencia": None, "error_absoluto": None, "error_relativo": None, "error_porcentual": None} for x, valor in zip(puntos, valores)]
        error_final = error_rel_final = error_pct_final = None
    return {
        "metodo": nombre,
        "nodos": [{"x": x, "y": y} for x, y in zip(xs, ys)],
        "evaluaciones": filas,
        "curva": [{"x": x, "y": y} for x, y in zip(puntos, valores)],
        "tabla_diferencias": tabla,
        "valor_final": filas[-1]["aproximacion"] if filas else None,
        "valor_referencia": filas[-1]["referencia"] if filas else None,
        "error_absoluto_final": error_final,
        "error_relativo_final": error_rel_final,
        "error_porcentual_final": error_pct_final,
        "iteraciones_totales": len(puntos),
        "convergio": True,
    }


def lagrange(
    x: Sequence[float],
    y: Sequence[float],
    puntos: Sequence[float],
    *,
    referencia: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Evalúa el polinomio interpolante de Lagrange usando productos baricéntricos."""
    xs, ys = _validar_nodos(x, y)
    test = _puntos(puntos)
    pesos = []
    for i, xi in enumerate(xs):
        producto = math.prod(xi - xs[j] for j in range(len(xs)) if i != j)
        if producto == 0.0:
            raise ValueError("Los nodos deben ser distintos")
        pesos.append(1.0 / producto)

    def evaluar(z: float) -> float:
        for xi, yi in zip(xs, ys):
            if z == xi:
                return yi
        numerador = math.fsum(pesos[i] * ys[i] / (z - xs[i]) for i in range(len(xs)))
        denominador = math.fsum(pesos[i] / (z - xs[i]) for i in range(len(xs)))
        if denominador == 0.0:
            raise ValueError("No se pudo evaluar el polinomio en el punto solicitado")
        valor = numerador / denominador
        if not math.isfinite(valor):
            raise ValueError("La interpolación produjo un valor no finito")
        return valor

    valores = [evaluar(z) for z in test]
    return _tabla_resultado("Lagrange", xs, ys, test, valores, referencia)


def newton_diferencias_divididas(
    x: Sequence[float],
    y: Sequence[float],
    puntos: Sequence[float],
    *,
    referencia: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Interpola por Newton y devuelve el triángulo de diferencias divididas."""
    xs, ys = _validar_nodos(x, y)
    test = _puntos(puntos)
    n = len(xs)
    tabla = [[0.0] * n for _ in range(n)]
    for i, valor in enumerate(ys):
        tabla[i][0] = valor
    for orden in range(1, n):
        for i in range(n - orden):
            tabla[i][orden] = (tabla[i + 1][orden - 1] - tabla[i][orden - 1]) / (xs[i + orden] - xs[i])
            if not math.isfinite(tabla[i][orden]):
                raise ValueError("Las diferencias divididas produjeron un valor no finito")

    def evaluar(z: float) -> float:
        valor = tabla[0][n - 1]
        for i in range(n - 2, -1, -1):
            valor = tabla[0][i] + (z - xs[i]) * valor
        if not math.isfinite(valor):
            raise ValueError("La interpolación produjo un valor no finito")
        return valor

    resultado = _tabla_resultado("Newton por diferencias divididas", xs, ys, test, [evaluar(z) for z in test], referencia, tabla)
    resultado["coeficientes"] = [tabla[0][i] for i in range(n)]
    return resultado


def splines_cubicos_naturales(
    x: Sequence[float],
    y: Sequence[float],
    puntos: Sequence[float],
    *,
    referencia: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Evalúa splines cúbicos naturales; fuera del dominio usa extrapolación terminal."""
    xs, ys = _validar_nodos(x, y)
    test = _puntos(puntos)
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    matriz = [[0.0] * n for _ in range(n)]
    rhs = [0.0] * n
    matriz[0][0] = matriz[-1][-1] = 1.0
    for i in range(1, n - 1):
        matriz[i][i - 1] = h[i - 1]
        matriz[i][i] = 2.0 * (h[i - 1] + h[i])
        matriz[i][i + 1] = h[i]
        rhs[i] = 6.0 * ((ys[i + 1] - ys[i]) / h[i] - (ys[i] - ys[i - 1]) / h[i - 1])
    for i in range(n):
        for k in range(i + 1, n):
            if matriz[k][i] == 0.0:
                continue
            factor = matriz[k][i] / matriz[i][i]
            for j in range(i, n):
                matriz[k][j] -= factor * matriz[i][j]
            rhs[k] -= factor * rhs[i]
    segunda = [0.0] * n
    for i in range(n - 1, -1, -1):
        pivote = matriz[i][i]
        if pivote == 0.0:
            raise ValueError("El sistema del spline es singular")
        segunda[i] = (rhs[i] - math.fsum(matriz[i][j] * segunda[j] for j in range(i + 1, n))) / pivote

    def evaluar(z: float) -> float:
        indice = min(max(next((i for i in range(n - 1) if xs[i] <= z <= xs[i + 1]), n - 2), 0), n - 2)
        ancho = h[indice]
        a = (xs[indice + 1] - z) / ancho
        b = (z - xs[indice]) / ancho
        valor = a * ys[indice] + b * ys[indice + 1] + ((a ** 3 - a) * segunda[indice] + (b ** 3 - b) * segunda[indice + 1]) * ancho ** 2 / 6.0
        if not math.isfinite(valor):
            raise ValueError("El spline produjo un valor no finito")
        return valor

    resultado = _tabla_resultado("Spline cúbico natural", xs, ys, test, [evaluar(z) for z in test], referencia)
    resultado["segundas_derivadas_nodales"] = segunda
    return resultado
