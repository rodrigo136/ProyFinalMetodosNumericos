"""Métodos numéricos para resolver sistemas de ecuaciones lineales."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

A_REFERENCIA = [
    [10.0, 2.0, 1.0, 0.0],
    [2.0, 10.0, 1.0, 1.0],
    [1.0, 1.0, 8.0, 2.0],
    [0.0, 1.0, 2.0, 9.0],
]
B_REFERENCIA = [13.0, 24.0, 31.0, 28.0]

MATRIZ_A = A_REFERENCIA
VECTOR_B = B_REFERENCIA

_TOLERANCIA = 1e-12


def _matriz_a_floats(matriz: Sequence[Sequence[float]]) -> List[List[float]]:
    try:
        resultado = [[float(valor) for valor in fila] for fila in matriz]
    except (TypeError, ValueError) as exc:
        raise ValueError("A debe ser una matriz bidimensional de números") from exc

    if not resultado or not resultado[0]:
        raise ValueError("La matriz A no puede estar vacía")

    tamano = len(resultado)
    if any(len(fila) != tamano for fila in resultado):
        raise ValueError("A debe ser una matriz cuadrada")

    return resultado


def _vector_a_floats(vector: Sequence[float]) -> List[float]:
    try:
        return [float(valor) for valor in vector]
    except (TypeError, ValueError) as exc:
        raise ValueError("b debe ser un vector de números") from exc


def _preparar_sistema(
    A: Optional[Sequence[Sequence[float]]],
    b: Optional[Sequence[float]],
) -> tuple[List[List[float]], List[float]]:
    if A is None and b is None:
        matriz = [fila[:] for fila in A_REFERENCIA]
        vector = B_REFERENCIA[:]
    elif A is None or b is None:
        raise ValueError("Debe proporcionar A y b juntos, o ninguno para usar el sistema de referencia")
    else:
        matriz = _matriz_a_floats(A)
        vector = _vector_a_floats(b)

    if len(matriz) != len(vector):
        raise ValueError("La cantidad de filas de A debe coincidir con la longitud de b")

    return matriz, vector


def _producto_matriz_vector(
    A: List[List[float]], x: Sequence[float]
) -> List[float]:
    return [
        math.fsum(A[i][j] * x[j] for j in range(len(x)))
        for i in range(len(A))
    ]


def _producto_punto(a: Sequence[float], b: Sequence[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b))


def _norma_infinita(vector: Sequence[float]) -> float:
    return max((abs(valor) for valor in vector), default=0.0)


def _norma_dos(vector: Sequence[float]) -> float:
    return math.sqrt(math.fsum(valor * valor for valor in vector))


def _norma_residual(
    A: List[List[float]], x: Sequence[float], b: Sequence[float]
) -> float:
    Ax = _producto_matriz_vector(A, x)
    return _norma_dos([b[i] - Ax[i] for i in range(len(b))])


def _errores_sucesivos(
    x: Sequence[float], x_anterior: Optional[Sequence[float]]
) -> tuple[float, float, float]:
    if x_anterior is None:
        return 0.0, 0.0, 0.0

    error_absoluto = max(
        (abs(actual - previo) for actual, previo in zip(x, x_anterior)),
        default=0.0,
    )
    escala = _norma_infinita(x)
    if escala == 0.0:
        error_relativo = 0.0 if error_absoluto == 0.0 else math.inf
    else:
        error_relativo = error_absoluto / escala
    return error_absoluto, error_relativo, error_relativo * 100.0


def _entrada_iteracion(
    iteracion: int,
    x: Sequence[float],
    x_anterior: Optional[Sequence[float]],
    A: List[List[float]],
    b: List[float],
) -> Dict[str, Any]:
    error_absoluto, error_relativo, error_porcentual = _errores_sucesivos(
        x, x_anterior
    )
    return {
        "iteracion": iteracion,
        "x": list(x),
        "error_absoluto": error_absoluto,
        "error_relativo": error_relativo,
        "error_porcentual": error_porcentual,
        "residual": _norma_residual(A, x, b),
    }


def _construir_resultado(
    metodo: str,
    tipo: str,
    solucion: Sequence[float],
    iteraciones: List[Dict[str, Any]],
    convergio: bool,
    mensaje: str,
    **extras: Any,
) -> Dict[str, Any]:
    ultima = iteraciones[-1] if iteraciones else None
    resultado: Dict[str, Any] = {
        "metodo": metodo,
        "tipo": tipo,
        "solucion": list(solucion),
        "iteraciones": iteraciones,
        "convergio": convergio,
        "iteraciones_totales": ultima["iteracion"] if ultima is not None else 0,
        "error_absoluto_final": ultima["error_absoluto"] if ultima is not None else 0.0,
        "error_relativo_final": ultima["error_relativo"] if ultima is not None else 0.0,
        "error_porcentual_final": ultima["error_porcentual"] if ultima is not None else 0.0,
        "residual_final": ultima["residual"] if ultima is not None else None,
        "mensaje": mensaje,
    }
    resultado.update(extras)
    return resultado


def _validar_parametros_iterativos(tolerancia: float, max_iteraciones: int) -> None:
    if tolerancia <= 0:
        raise ValueError("La tolerancia debe ser mayor que cero")
    if max_iteraciones < 1:
        raise ValueError("El número máximo de iteraciones debe ser positivo")


def _validar_diagonal(A: List[List[float]]) -> None:
    escala = max(1.0, max(abs(valor) for fila in A for valor in fila))
    for i, fila in enumerate(A):
        if abs(fila[i]) <= _TOLERANCIA * escala:
            raise ValueError(f"El elemento diagonal A[{i}][{i}] es cero o demasiado pequeño")


def _validar_spd(A: List[List[float]]) -> None:
    n = len(A)
    escala = max(1.0, max(abs(valor) for fila in A for valor in fila))
    umbral = _TOLERANCIA * escala

    for i in range(n):
        for j in range(i):
            if abs(A[i][j] - A[j][i]) > umbral:
                raise ValueError("La matriz A no es simétrica")

    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            suma = A[i][j] - math.fsum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                if suma <= umbral:
                    raise ValueError("La matriz A no es definida positiva")
                L[i][j] = math.sqrt(suma)
            else:
                L[i][j] = suma / L[j][j]


def _sustitucion_adelante(
    L: List[List[float]], b: Sequence[float]
) -> List[float]:
    n = len(L)
    y = [0.0] * n
    for i in range(n):
        y[i] = (
            b[i] - math.fsum(L[i][j] * y[j] for j in range(i))
        ) / L[i][i]
    return y


def _sustitucion_atras(
    U: List[List[float]], y: Sequence[float]
) -> List[float]:
    n = len(U)
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (
            y[i] - math.fsum(U[i][j] * x[j] for j in range(i + 1, n))
        ) / U[i][i]
    return x


def solucion_exacta(
    A: Optional[Sequence[Sequence[float]]] = None,
    b: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Resuelve el sistema mediante eliminación gaussiana con pivoteo parcial."""
    matriz, vector = _preparar_sistema(A, b)
    n = len(matriz)
    aumentada = [matriz[i][:] + [vector[i]] for i in range(n)]
    escala = max(1.0, max(abs(valor) for fila in matriz for valor in fila))

    for columna in range(n):
        pivote = max(
            range(columna, n),
            key=lambda fila: abs(aumentada[fila][columna]),
        )
        if abs(aumentada[pivote][columna]) <= _TOLERANCIA * escala:
            raise ValueError("El sistema es singular o no tiene solución única")

        if pivote != columna:
            aumentada[columna], aumentada[pivote] = (
                aumentada[pivote],
                aumentada[columna],
            )

        for fila in range(columna + 1, n):
            factor = aumentada[fila][columna] / aumentada[columna][columna]
            aumentada[fila][columna] = 0.0
            for j in range(columna + 1, n + 1):
                aumentada[fila][j] -= factor * aumentada[columna][j]

    solucion = [0.0] * n
    for i in range(n - 1, -1, -1):
        solucion[i] = (
            aumentada[i][n]
            - math.fsum(aumentada[i][j] * solucion[j] for j in range(i + 1, n))
        ) / aumentada[i][i]

    paso = _entrada_iteracion(1, solucion, None, matriz, vector)
    return _construir_resultado(
        metodo="Solución exacta (eliminación gaussiana)",
        tipo="directo",
        solucion=solucion,
        iteraciones=[paso],
        convergio=True,
        mensaje="Solución obtenida directamente mediante eliminación gaussiana.",
        matriz_aumentada_final=aumentada,
    )


def factorizacion_lu(
    A: Optional[Sequence[Sequence[float]]] = None,
    b: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Resuelve A*x=b mediante factorización LU con pivoteo parcial."""
    matriz, vector = _preparar_sistema(A, b)
    n = len(matriz)
    LU = [fila[:] for fila in matriz]
    permutacion = list(range(n))
    escala = max(1.0, max(abs(valor) for fila in matriz for valor in fila))

    for columna in range(n):
        pivote = max(
            range(columna, n),
            key=lambda fila: abs(LU[fila][columna]),
        )
        if abs(LU[pivote][columna]) <= _TOLERANCIA * escala:
            raise ValueError("La matriz es singular y no admite factorización LU")

        if pivote != columna:
            LU[columna], LU[pivote] = LU[pivote], LU[columna]
            permutacion[columna], permutacion[pivote] = (
                permutacion[pivote],
                permutacion[columna],
            )
            for j in range(columna):
                LU[columna][j], LU[pivote][j] = LU[pivote][j], LU[columna][j]

        for fila in range(columna + 1, n):
            factor = LU[fila][columna] / LU[columna][columna]
            LU[fila][columna] = factor
            for j in range(columna + 1, n):
                LU[fila][j] -= factor * LU[columna][j]

    L = [[0.0] * n for _ in range(n)]
    U = [[0.0] * n for _ in range(n)]
    for i in range(n):
        L[i][i] = 1.0
        for j in range(i):
            L[i][j] = LU[i][j]
        for j in range(i, n):
            U[i][j] = LU[i][j]

    P = [[0.0] * n for _ in range(n)]
    for i, columna in enumerate(permutacion):
        P[i][columna] = 1.0

    b_permutado = [vector[i] for i in permutacion]
    y = _sustitucion_adelante(L, b_permutado)
    solucion = _sustitucion_atras(U, y)

    paso = _entrada_iteracion(1, solucion, None, matriz, vector)
    return _construir_resultado(
        metodo="Factorización LU",
        tipo="directo",
        solucion=solucion,
        iteraciones=[paso],
        convergio=True,
        mensaje="Solución obtenida mediante factorización LU con pivoteo parcial.",
        L=L,
        U=U,
        P=P,
        permutacion=permutacion,
        y=y,
    )


def jacobi(
    A: Optional[Sequence[Sequence[float]]] = None,
    b: Optional[Sequence[float]] = None,
    x0: Optional[Sequence[float]] = None,
    tolerancia: float = 1e-10,
    max_iteraciones: int = 1000,
) -> Dict[str, Any]:
    """Resuelve A*x=b mediante el método iterativo de Jacobi."""
    matriz, vector = _preparar_sistema(A, b)
    _validar_parametros_iterativos(tolerancia, max_iteraciones)
    _validar_diagonal(matriz)

    n = len(matriz)
    if x0 is None:
        x = [0.0] * n
    else:
        x = _vector_a_floats(x0)
        if len(x) != n:
            raise ValueError("La longitud de x0 debe coincidir con el tamaño de A")

    iteraciones: List[Dict[str, Any]] = []
    convergio = False

    for k in range(1, max_iteraciones + 1):
        x_nuevo = [0.0] * n
        for i in range(n):
            suma = math.fsum(
                matriz[i][j] * x[j] for j in range(n) if j != i
            )
            x_nuevo[i] = (vector[i] - suma) / matriz[i][i]

        paso = _entrada_iteracion(k, x_nuevo, x, matriz, vector)
        iteraciones.append(paso)

        if paso["error_relativo"] <= tolerancia or paso["error_absoluto"] <= tolerancia:
            convergio = True
            x = x_nuevo
            break

        x = x_nuevo

    mensaje = (
        "El método convergió dentro de la tolerancia solicitada."
        if convergio
        else "Se alcanzó el número máximo de iteraciones sin converger."
    )
    return _construir_resultado(
        metodo="Jacobi",
        tipo="iterativo",
        solucion=x,
        iteraciones=iteraciones,
        convergio=convergio,
        mensaje=mensaje,
        tolerancia=tolerancia,
        max_iteraciones=max_iteraciones,
        x_inicial=[0.0] * n if x0 is None else list(x0),
    )


def gauss_seidel(
    A: Optional[Sequence[Sequence[float]]] = None,
    b: Optional[Sequence[float]] = None,
    x0: Optional[Sequence[float]] = None,
    tolerancia: float = 1e-10,
    max_iteraciones: int = 1000,
) -> Dict[str, Any]:
    """Resuelve A*x=b mediante el método iterativo de Gauss-Seidel."""
    matriz, vector = _preparar_sistema(A, b)
    _validar_parametros_iterativos(tolerancia, max_iteraciones)
    _validar_diagonal(matriz)

    n = len(matriz)
    if x0 is None:
        x = [0.0] * n
    else:
        x = _vector_a_floats(x0)
        if len(x) != n:
            raise ValueError("La longitud de x0 debe coincidir con el tamaño de A")

    iteraciones: List[Dict[str, Any]] = []
    convergio = False

    for k in range(1, max_iteraciones + 1):
        x_anterior = x[:]
        for i in range(n):
            suma = math.fsum(
                matriz[i][j] * x[j] for j in range(n) if j != i
            )
            x[i] = (vector[i] - suma) / matriz[i][i]

        paso = _entrada_iteracion(k, x, x_anterior, matriz, vector)
        iteraciones.append(paso)

        if paso["error_relativo"] <= tolerancia or paso["error_absoluto"] <= tolerancia:
            convergio = True
            break

    mensaje = (
        "El método convergió dentro de la tolerancia solicitada."
        if convergio
        else "Se alcanzó el número máximo de iteraciones sin converger."
    )
    return _construir_resultado(
        metodo="Gauss-Seidel",
        tipo="iterativo",
        solucion=x,
        iteraciones=iteraciones,
        convergio=convergio,
        mensaje=mensaje,
        tolerancia=tolerancia,
        max_iteraciones=max_iteraciones,
        x_inicial=[0.0] * n if x0 is None else list(x0),
    )


def gradiente_conjugado(
    A: Optional[Sequence[Sequence[float]]] = None,
    b: Optional[Sequence[float]] = None,
    x0: Optional[Sequence[float]] = None,
    tolerancia: float = 1e-10,
    max_iteraciones: int = 1000,
) -> Dict[str, Any]:
    """Resuelve A*x=b mediante gradiente conjugado para matrices SPD."""
    matriz, vector = _preparar_sistema(A, b)
    _validar_parametros_iterativos(tolerancia, max_iteraciones)
    _validar_spd(matriz)

    n = len(matriz)
    if x0 is None:
        x = [0.0] * n
    else:
        x = _vector_a_floats(x0)
        if len(x) != n:
            raise ValueError("La longitud de x0 debe coincidir con el tamaño de A")

    Ax = _producto_matriz_vector(matriz, x)
    r = [vector[i] - Ax[i] for i in range(n)]
    p = r[:]
    rs_actual = _producto_punto(r, r)
    norma_b = _norma_dos(vector)
    umbral_residual = tolerancia * max(1.0, norma_b)

    iteraciones: List[Dict[str, Any]] = []
    convergio = False

    if math.sqrt(rs_actual) <= umbral_residual:
        paso = _entrada_iteracion(0, x, None, matriz, vector)
        iteraciones.append(paso)
        convergio = True
    else:
        for k in range(1, max_iteraciones + 1):
            Ap = _producto_matriz_vector(matriz, p)
            denominador = _producto_punto(p, Ap)
            if denominador <= 0.0:
                raise ValueError("La matriz A no es definida positiva o el método no es aplicable")

            alpha = rs_actual / denominador
            x_nuevo = [x[i] + alpha * p[i] for i in range(n)]
            r_nuevo = [r[i] - alpha * Ap[i] for i in range(n)]
            rs_nuevo = _producto_punto(r_nuevo, r_nuevo)

            paso = _entrada_iteracion(k, x_nuevo, x, matriz, vector)
            iteraciones.append(paso)

            if (
                paso["error_relativo"] <= tolerancia
                or paso["error_absoluto"] <= tolerancia
                or math.sqrt(rs_nuevo) <= umbral_residual
            ):
                convergio = True
                x = x_nuevo
                break

            beta = rs_nuevo / rs_actual
            p = [r_nuevo[i] + beta * p[i] for i in range(n)]
            x = x_nuevo
            r = r_nuevo
            rs_actual = rs_nuevo

    mensaje = (
        "El método convergió dentro de la tolerancia solicitada."
        if convergio
        else "Se alcanzó el número máximo de iteraciones sin converger."
    )
    return _construir_resultado(
        metodo="Gradiente conjugado",
        tipo="iterativo",
        solucion=x,
        iteraciones=iteraciones,
        convergio=convergio,
        mensaje=mensaje,
        tolerancia=tolerancia,
        max_iteraciones=max_iteraciones,
        x_inicial=[0.0] * n if x0 is None else list(x0),
    )


eliminacion_gaussiana = solucion_exacta
cg = gradiente_conjugado


if __name__ == "__main__":
    metodos = (
        solucion_exacta,
        factorizacion_lu,
        jacobi,
        gauss_seidel,
        gradiente_conjugado,
    )
    for metodo in metodos:
        resultado = metodo()
        solucion = ", ".join(f"{valor:.10f}" for valor in resultado["solucion"])
        print(f"{resultado['metodo']}: x = [{solucion}]")
        print(
            f"  iteraciones={resultado['iteraciones_totales']} "
            f"residual={resultado['residual_final']:.3e} "
            f"convergio={resultado['convergio']}"
        )
