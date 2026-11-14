"""Funciones de cálculo de errores y análisis numérico para SIMTELE-RISK."""

from __future__ import annotations

import math
from typing import Any, List, Optional, Sequence, Union

Number = Union[int, float]
Orden = Union[int, float, str]

_TOLERANCIA = 1e-12


def error_absoluto(valor_real: Number, valor_aproximado: Number) -> float:
    """Devuelve |valor_real - valor_aproximado|."""
    return abs(float(valor_real) - float(valor_aproximado))


def error_relativo(valor_real: Number, valor_aproximado: Number) -> float:
    """Devuelve el error relativo y valida la división por cero."""
    real = float(valor_real)
    if real == 0.0:
        raise ValueError("No se puede calcular el error relativo: el valor real es cero")
    return abs(real - float(valor_aproximado)) / abs(real)


def error_porcentual(valor_real: Number, valor_aproximado: Number) -> float:
    """Devuelve el error relativo expresado en porcentaje."""
    return error_relativo(valor_real, valor_aproximado) * 100.0


def _normalizar_orden(orden: Orden) -> Union[int, float, str]:
    if isinstance(orden, str):
        valor = orden.strip().lower()
        if valor in {"inf", "infinito", "infinity"}:
            return math.inf
        if valor in {"fro", "frobenius"}:
            return "fro"
        try:
            return int(valor)
        except ValueError as exc:
            raise ValueError(f"Orden de norma no válido: {orden}") from exc
    return orden


def _norma_vector(vector: Sequence[Number], orden: Orden = 2) -> float:
    valores = [abs(float(valor)) for valor in vector]
    orden_normalizado = _normalizar_orden(orden)

    if not valores:
        return 0.0
    if orden_normalizado == math.inf:
        return max(valores)
    if orden_normalizado == 1:
        return math.fsum(valores)
    if orden_normalizado == 2:
        return math.sqrt(math.fsum(valor * valor for valor in valores))
    if isinstance(orden_normalizado, str) or orden_normalizado <= 0:
        raise ValueError(f"Orden de norma no válido: {orden}")
    return math.fsum(valor ** orden_normalizado for valor in valores) ** (
        1.0 / orden_normalizado
    )


def _matriz_a_floats(matriz: Sequence[Sequence[Number]]) -> List[List[float]]:
    try:
        resultado = [[float(valor) for valor in fila] for fila in matriz]
    except (TypeError, ValueError) as exc:
        raise ValueError("La matriz debe ser una secuencia bidimensional de números") from exc

    if not resultado or not resultado[0]:
        raise ValueError("La matriz no puede estar vacía")

    columnas = len(resultado[0])
    if any(len(fila) != columnas for fila in resultado):
        raise ValueError("Todas las filas de la matriz deben tener la misma longitud")

    return resultado


def _vector_a_floats(vector: Sequence[Number]) -> List[float]:
    try:
        return [float(valor) for valor in vector]
    except (TypeError, ValueError) as exc:
        raise ValueError("El vector debe ser una secuencia de números") from exc


def norma_residual(
    A: Any,
    x: Optional[Sequence[Number]] = None,
    b: Optional[Sequence[Number]] = None,
    orden: Orden = 2,
) -> float:
    """Calcula ||b - A*x||.

    Si se omiten x y b, A se interpreta como el vector de residuales y se
    devuelve directamente su norma.
    """
    if x is None and b is None:
        return _norma_vector(A, orden)
    if x is None or b is None:
        raise ValueError("Debe proporcionar tanto x como b para calcular el residual")

    matriz = _matriz_a_floats(A)
    vector_x = _vector_a_floats(x)
    vector_b = _vector_a_floats(b)

    filas = len(matriz)
    columnas = len(matriz[0])
    if len(vector_x) != columnas:
        raise ValueError("La longitud de x no coincide con las columnas de A")
    if len(vector_b) != filas:
        raise ValueError("La longitud de b no coincide con las filas de A")

    residual = [
        vector_b[i] - math.fsum(matriz[i][j] * vector_x[j] for j in range(columnas))
        for i in range(filas)
    ]
    return _norma_vector(residual, orden)


def _inversa_matriz(matriz: List[List[float]]) -> List[List[float]]:
    n = len(matriz)
    if any(len(fila) != n for fila in matriz):
        raise ValueError("La matriz debe ser cuadrada para calcular su inversa")

    escala = max(abs(valor) for fila in matriz for valor in fila)
    umbral = max(escala, 1.0) * _TOLERANCIA

    aumentada = [
        fila[:] + [1.0 if i == j else 0.0 for j in range(n)]
        for i, fila in enumerate(matriz)
    ]

    for columna in range(n):
        pivote = max(range(columna, n), key=lambda fila: abs(aumentada[fila][columna]))
        if abs(aumentada[pivote][columna]) <= umbral:
            raise ValueError("La matriz es singular y no se puede invertir")

        if pivote != columna:
            aumentada[columna], aumentada[pivote] = aumentada[pivote], aumentada[columna]

        factor_pivote = aumentada[columna][columna]
        for j in range(columna, 2 * n):
            aumentada[columna][j] /= factor_pivote

        for fila in range(n):
            if fila == columna:
                continue
            factor = aumentada[fila][columna]
            if factor == 0.0:
                continue
            for j in range(columna, 2 * n):
                aumentada[fila][j] -= factor * aumentada[columna][j]

    return [fila[n:] for fila in aumentada]


def _eigenvalores_simetricos(
    matriz: List[List[float]],
    max_barridos: int = 100,
) -> List[float]:
    n = len(matriz)
    A = [fila[:] for fila in matriz]

    for _ in range(max_barridos):
        mayor = 0.0
        p = 0
        q = 0
        for i in range(n):
            for j in range(i + 1, n):
                valor = abs(A[i][j])
                if valor > mayor:
                    mayor = valor
                    p, q = i, j

        if mayor <= _TOLERANCIA:
            break

        app = A[p][p]
        aqq = A[q][q]
        apq = A[p][q]
        tau = (aqq - app) / (2.0 * apq)
        if tau >= 0.0:
            t = 1.0 / (tau + math.sqrt(1.0 + tau * tau))
        else:
            t = -1.0 / (-tau + math.sqrt(1.0 + tau * tau))

        c = 1.0 / math.sqrt(1.0 + t * t)
        s = t * c

        for k in range(n):
            if k == p or k == q:
                continue
            akp = A[k][p]
            akq = A[k][q]
            A[k][p] = c * akp - s * akq
            A[p][k] = A[k][p]
            A[k][q] = s * akp + c * akq
            A[q][k] = A[k][q]

        A[p][p] = c * c * app - 2.0 * s * c * apq + s * s * aqq
        A[q][q] = s * s * app + 2.0 * s * c * apq + c * c * aqq
        A[p][q] = 0.0
        A[q][p] = 0.0

    return [A[i][i] for i in range(n)]


def _valores_singulares(matriz: List[List[float]]) -> List[float]:
    filas = len(matriz)
    columnas = len(matriz[0])
    at_a = [
        [
            math.fsum(matriz[k][i] * matriz[k][j] for k in range(filas))
            for j in range(columnas)
        ]
        for i in range(columnas)
    ]
    eigenvalores = _eigenvalores_simetricos(at_a)
    return [math.sqrt(max(0.0, valor)) for valor in eigenvalores]


def _norma_matriz(matriz: List[List[float]], orden: Orden = 2) -> float:
    orden_normalizado = _normalizar_orden(orden)
    filas = len(matriz)
    columnas = len(matriz[0])

    if orden_normalizado == 1:
        return max(
            math.fsum(abs(matriz[i][j]) for i in range(filas))
            for j in range(columnas)
        )
    if orden_normalizado == math.inf:
        return max(math.fsum(abs(valor) for valor in fila) for fila in matriz)
    if orden_normalizado == "fro":
        return math.sqrt(
            math.fsum(valor * valor for fila in matriz for valor in fila)
        )
    if orden_normalizado == 2:
        return max(_valores_singulares(matriz))
    raise ValueError(f"Orden de norma no válido: {orden}")


def numero_condicion(A: Sequence[Sequence[Number]], orden: Orden = 2) -> float:
    """Calcula kappa(A) = ||A|| * ||A^-1||.

    La norma 2 se calcula mediante los valores singulares y admite matrices
    rectangulares. Las normas 1, infinito y Frobenius requieren una matriz
    cuadrada. Si la matriz es singular, devuelve infinito.
    """
    matriz = _matriz_a_floats(A)
    orden_normalizado = _normalizar_orden(orden)

    if orden_normalizado == 2:
        valores = _valores_singulares(matriz)
        maximo = max(valores)
        minimo = min(valores)
        if maximo == 0.0 or minimo <= maximo * _TOLERANCIA:
            return math.inf
        return maximo / minimo

    if orden_normalizado not in (1, math.inf, "fro"):
        raise ValueError(f"Orden de norma no válido: {orden}")

    if len(matriz) != len(matriz[0]):
        raise ValueError("La matriz debe ser cuadrada para usar esta norma")

    try:
        inversa = _inversa_matriz(matriz)
    except ValueError:
        return math.inf

    return _norma_matriz(matriz, orden_normalizado) * _norma_matriz(
        inversa, orden_normalizado
    )


kappa = numero_condicion
