"""Parámetros didácticos y reproducibles de los cuatro módulos SIMTELE-RISK."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Callable, Dict, List

try:
    from . import edo, integracion, interpolacion, raices
except ImportError:
    import edo
    import integracion
    import interpolacion
    import raices

ESCENARIOS_MODULO: Dict[int, Dict[str, Any]] = {
    1: {
        "codigo": "CE-001",
        "nombre": "Detención de emergencia de cabinas",
        "metodos": ["rk2", "rk4", "trapecio", "simpson", "romberg", "biseccion", "newton", "secante"],
        "escenarios": {
            "NORMAL": {"descripcion": "Frenado nominal, desaceleración uniforme y parada dentro del intervalo.", "parametros": {"velocidad_inicial": 20.0, "desaceleracion": 2.5, "pasos": 40}},
            "ESTRES": {"descripcion": "Exigencia física: velocidad inicial y desaceleración elevada; no implica inestabilidad numérica.", "parametros": {"velocidad_inicial": 30.0, "desaceleracion": 5.0, "pasos": 60}},
            "MAL_CONDICIONADO": {"descripcion": "Sensibilidad matemática: velocidad alta y desaceleración pequeña hacen sensible el tiempo de parada a perturbaciones.", "parametros": {"velocidad_inicial": 30.0, "desaceleracion": 0.75, "pasos": 80}},
        },
    },
    2: {
        "codigo": "CE-002",
        "nombre": "Deterioro mecánico y mantenimiento",
        "metodos": ["biseccion", "newton", "secante"],
        "escenarios": {
            "NORMAL": {"descripcion": "Deterioro gradual con umbral de mantenimiento dentro del horizonte.", "parametros": {"deterioro_inicial": 0.1, "tasa": 0.03, "curvatura": 0.002, "umbral": 1.0, "horizonte": 24.0}},
            "ESTRES": {"descripcion": "Exigencia operativa: desgaste acelerado y umbral alcanzado antes.", "parametros": {"deterioro_inicial": 0.1, "tasa": 0.07, "curvatura": 0.006, "umbral": 1.0, "horizonte": 16.0}},
            "MAL_CONDICIONADO": {"descripcion": "Sensibilidad matemática: umbral muy próximo al estado inicial y tasa pequeña.", "parametros": {"deterioro_inicial": 0.1, "tasa": 0.00001, "curvatura": 0.0, "umbral": 0.1001, "horizonte": 20.0}},
        },
    },
    3: {
        "codigo": "CE-003",
        "nombre": "Oscilaciones por viento",
        "metodos": ["rk2", "rk4", "trapecio", "simpson", "romberg"],
        "escenarios": {
            "NORMAL": {"descripcion": "Respuesta amortiguada nominal ante una carga sinusoidal.", "parametros": {"masa": 1200.0, "amortiguamiento": 180.0, "rigidez": 900.0, "fuerza": 1200.0, "frecuencia": 0.7, "tiempo_final": 12.0, "pasos": 240}},
            "ESTRES": {"descripcion": "Exigencia física: fuerza de viento mayor y amortiguamiento menor.", "parametros": {"masa": 1200.0, "amortiguamiento": 55.0, "rigidez": 900.0, "fuerza": 4500.0, "frecuencia": 0.7, "tiempo_final": 12.0, "pasos": 240}},
            "MAL_CONDICIONADO": {"descripcion": "Sensibilidad matemática: excitación próxima a la frecuencia natural y amortiguamiento bajo.", "parametros": {"masa": 1200.0, "amortiguamiento": 2.0, "rigidez": 900.0, "fuerza": 1200.0, "frecuencia": 0.8660, "tiempo_final": 12.0, "pasos": 480}},
        },
    },
    4: {
        "codigo": "CE-004",
        "nombre": "Reconstrucción de señales de sensores",
        "metodos": ["lagrange", "newton_interpolacion", "spline"],
        "escenarios": {
            "NORMAL": {"descripcion": "Lecturas regulares de una señal suave con muestras ocultas.", "parametros": {"senal": "sin", "cantidad_nodos": 9, "cantidad_ocultos": 3, "inicio": 0.0, "fin": 3.141592653589793}},
            "ESTRES": {"descripcion": "Exigencia de instrumentación: mayor proporción de lecturas ausentes.", "parametros": {"senal": "exp", "cantidad_nodos": 11, "cantidad_ocultos": 5, "inicio": 0.0, "fin": 4.0}},
            "MAL_CONDICIONADO": {"descripcion": "Mal condicionamiento matemático del polinomio: señal de Runge y nodos uniformes.", "parametros": {"senal": "runge", "cantidad_nodos": 15, "cantidad_ocultos": 5, "inicio": 0.0, "fin": 1.0}},
        },
    },
}


def obtener_escenarios_modulo() -> Dict[str, Any]:
    """Devuelve una copia serializable para evitar mutaciones del catálogo."""
    return {"modulos": {str(numero): deepcopy(datos) for numero, datos in ESCENARIOS_MODULO.items()}}


def _raiz_analitica_modulo_1(v0: float, aceleracion: float) -> float:
    return v0 / aceleracion


def ejecutar_metodo_modulo(modulo: int, escenario: str, metodo: str) -> Dict[str, Any]:
    """Ejecuta un método de un módulo usando exclusivamente parámetros publicados."""
    if modulo not in ESCENARIOS_MODULO:
        raise ValueError("El módulo debe estar entre 1 y 4")
    clave = str(escenario).upper().replace(" ", "_")
    datos = ESCENARIOS_MODULO[modulo]["escenarios"].get(clave)
    if datos is None:
        raise ValueError("Escenario inválido; use NORMAL, ESTRES o MAL_CONDICIONADO")
    if metodo not in ESCENARIOS_MODULO[modulo]["metodos"]:
        raise ValueError("El método seleccionado no aplica a este módulo")

    p = datos["parametros"]
    resultado: Dict[str, Any]
    if modulo == 1:
        v0, desaceleracion = p["velocidad_inicial"], p["desaceleracion"]
        tiempo_parada = _raiz_analitica_modulo_1(v0, desaceleracion)
        referencia_distancia = v0 * tiempo_parada - 0.5 * desaceleracion * tiempo_parada ** 2
        if metodo in {"rk2", "rk4"}:
            funcion = lambda _, estado: [estado[1], -desaceleracion]
            referencia = lambda t: [v0 * t - 0.5 * desaceleracion * t * t, v0 - desaceleracion * t]
            resultado = edo.resolver_edo(funcion, (0.0, tiempo_parada), [0.0, v0], p["pasos"], metodo=metodo, referencia=referencia)
            resultado["cantidad"] = "trayectoria y velocidad"
        elif metodo in {"trapecio", "simpson", "romberg"}:
            funcion_v = lambda t: v0 - desaceleracion * t
            n = p["pasos"] if metodo != "romberg" else None
            if metodo == "trapecio":
                resultado = integracion.trapecio_compuesto(funcion_v, 0.0, tiempo_parada, n, referencia=referencia_distancia)
            elif metodo == "simpson":
                resultado = integracion.simpson_13_compuesto(funcion_v, 0.0, tiempo_parada, n if n % 2 == 0 else n + 1, referencia=referencia_distancia)
            else:
                resultado = integracion.romberg(funcion_v, 0.0, tiempo_parada, niveles=6, referencia=referencia_distancia)
            resultado["tabla_refinamiento"][-1]["subintervalos"] = n or resultado["tabla_refinamiento"][-1]["subintervalos"]
            resultado["curva"] = [
                {"x": tiempo_parada * i / 80, "y": funcion_v(tiempo_parada * i / 80)}
                for i in range(81)
            ]
        else:
            funcion_root = lambda t: v0 - desaceleracion * t
            derivada = lambda _: -desaceleracion
            if metodo == "biseccion":
                resultado = raices.biseccion(funcion_root, 0.0, tiempo_parada * 1.5, referencia=tiempo_parada)
            elif metodo == "newton":
                resultado = raices.newton_raphson(funcion_root, derivada, tiempo_parada * 0.8, referencia=tiempo_parada)
            else:
                resultado = raices.secante(funcion_root, 0.0, tiempo_parada * 1.5, referencia=tiempo_parada)
            resultado["valor_referencia_analitica"] = tiempo_parada
            resultado["curva"] = [
                {"x": tiempo_parada * i / 80, "y": funcion_root(tiempo_parada * i / 80)}
                for i in range(81)
            ]
        resultado["referencia_analitica"] = {"tiempo_parada": tiempo_parada, "distancia_frenado": referencia_distancia}
    elif modulo == 2:
        d0, tasa, curva, umbral, horizonte = (p[k] for k in ("deterioro_inicial", "tasa", "curvatura", "umbral", "horizonte"))
        funcion = lambda t: d0 + tasa * t + curva * t * t - umbral
        derivada = lambda t: tasa + 2.0 * curva * t
        raiz_analitica = (-tasa + math.sqrt(tasa * tasa + 4.0 * curva * (umbral - d0))) / (2.0 * curva) if curva else (umbral - d0) / tasa
        if metodo == "biseccion":
            resultado = raices.biseccion(funcion, 0.0, horizonte, referencia=raiz_analitica)
        elif metodo == "newton":
            resultado = raices.newton_raphson(funcion, derivada, max(0.0, raiz_analitica * 0.8), referencia=raiz_analitica)
        else:
            resultado = raices.secante(funcion, 0.0, horizonte * 0.4, referencia=raiz_analitica)
        resultado["referencia_analitica"] = {"tiempo_umbral": raiz_analitica}
        resultado["curva"] = [
            {
                "x": horizonte * i / 100,
                "y": d0 + tasa * horizonte * i / 100 + curva * (horizonte * i / 100) ** 2,
                "referencia": umbral,
            }
            for i in range(101)
        ]
        resultado["umbral"] = umbral
    elif modulo == 3:
        masa, amortiguamiento, rigidez, fuerza, frecuencia = (p[k] for k in ("masa", "amortiguamiento", "rigidez", "fuerza", "frecuencia"))
        def rhs(t: float, estado: List[float]) -> List[float]:
            x, v = estado
            return [v, (fuerza * math.sin(frecuencia * t) - amortiguamiento * v - rigidez * x) / masa]

        pasos_ref = min(10000, max(int(p["pasos"]) * 10, 4000))
        solucion_ref = edo.resolver_edo(rhs, (0.0, p["tiempo_final"]), [0.0, 0.0], pasos_ref, metodo="rk4")
        filas_ref = solucion_ref["tabla_temporal"]
        tiempos_ref = [float(fila["t"]) for fila in filas_ref]
        estados_ref = [list(fila["aproximacion"]) for fila in filas_ref]

        def referencia_rk4(t: float) -> List[float]:
            if t <= tiempos_ref[0]:
                return estados_ref[0][:]
            if t >= tiempos_ref[-1]:
                return estados_ref[-1][:]
            paso_idx = min(
                len(tiempos_ref) - 2,
                max(0, int((t - tiempos_ref[0]) / (tiempos_ref[-1] - tiempos_ref[0]) * (len(tiempos_ref) - 1))),
            )
            while paso_idx < len(tiempos_ref) - 2 and tiempos_ref[paso_idx + 1] < t:
                paso_idx += 1
            while paso_idx > 0 and tiempos_ref[paso_idx] > t:
                paso_idx -= 1
            t0_ref, t1_ref = tiempos_ref[paso_idx], tiempos_ref[paso_idx + 1]
            alpha = 0.0 if t1_ref == t0_ref else (t - t0_ref) / (t1_ref - t0_ref)
            e0, e1 = estados_ref[paso_idx], estados_ref[paso_idx + 1]
            return [e0[j] + alpha * (e1[j] - e0[j]) for j in range(len(e0))]

        if metodo in {"rk2", "rk4"}:
            resultado = edo.resolver_edo(
                rhs,
                (0.0, p["tiempo_final"]),
                [0.0, 0.0],
                p["pasos"],
                metodo=metodo,
                referencia=referencia_rk4,
            )
            resultado["magnitud"] = "desplazamiento x(t) y velocidad v(t)"
            resultado["tipo_referencia"] = f"RK4 de alta precisión ({pasos_ref} pasos)"
        else:
            solucion = edo.resolver_edo(rhs, (0.0, p["tiempo_final"]), [0.0, 0.0], p["pasos"], metodo="rk4")
            filas = solucion["tabla_temporal"]
            tiempos = [fila["t"] for fila in filas]
            desplazamientos = [fila["aproximacion"][0] for fila in filas]

            def posicion(t: float) -> float:
                indice = min(len(tiempos) - 2, max(0, int(t / p["tiempo_final"] * (len(tiempos) - 1))))
                fraccion = (t - tiempos[indice]) / (tiempos[indice + 1] - tiempos[indice])
                return desplazamientos[indice] + fraccion * (desplazamientos[indice + 1] - desplazamientos[indice])

            integral = lambda t: posicion(t) ** 2

            # Referencia numérica de alta precisión sobre la trayectoria fina RK4
            pasos_ref_int = min(10000, max(int(p["pasos"]) * 10, 4000))
            solucion_ref_int = edo.resolver_edo(rhs, (0.0, p["tiempo_final"]), [0.0, 0.0], pasos_ref_int, metodo="rk4")
            filas_ref_int = solucion_ref_int["tabla_temporal"]
            tiempos_ref_int = [float(fila["t"]) for fila in filas_ref_int]
            desplazamientos_ref_int = [float(fila["aproximacion"][0]) for fila in filas_ref_int]

            def posicion_ref(t: float) -> float:
                if t <= tiempos_ref_int[0]:
                    return desplazamientos_ref_int[0]
                if t >= tiempos_ref_int[-1]:
                    return desplazamientos_ref_int[-1]
                idx = min(
                    len(tiempos_ref_int) - 2,
                    max(0, int((t - tiempos_ref_int[0]) / (tiempos_ref_int[-1] - tiempos_ref_int[0]) * (len(tiempos_ref_int) - 1))),
                )
                while idx < len(tiempos_ref_int) - 2 and tiempos_ref_int[idx + 1] < t:
                    idx += 1
                while idx > 0 and tiempos_ref_int[idx] > t:
                    idx -= 1
                t0_r, t1_r = tiempos_ref_int[idx], tiempos_ref_int[idx + 1]
                frac = 0.0 if t1_r == t0_r else (t - t0_r) / (t1_r - t0_r)
                return desplazamientos_ref_int[idx] + frac * (desplazamientos_ref_int[idx + 1] - desplazamientos_ref_int[idx])

            integral_ref = lambda t: posicion_ref(t) ** 2
            ref_romberg = integracion.romberg(integral_ref, 0.0, p["tiempo_final"], niveles=7)
            referencia_integral = float(ref_romberg["integral_aproximada"])

            if metodo == "trapecio":
                resultado = integracion.trapecio_compuesto(integral, 0.0, p["tiempo_final"], p["pasos"], referencia=referencia_integral)
            elif metodo == "simpson":
                resultado = integracion.simpson_13_compuesto(
                    integral,
                    0.0,
                    p["tiempo_final"],
                    p["pasos"] if p["pasos"] % 2 == 0 else p["pasos"] + 1,
                    referencia=referencia_integral,
                )
            else:
                resultado = integracion.romberg(integral, 0.0, p["tiempo_final"], niveles=7, referencia=referencia_integral)

            resultado["curva"] = [{"x": t, "y": posicion(t)} for t in tiempos]
            resultado["trayectoria_referencia"] = "RK4 con la misma malla (referencia numérica)"
            resultado["referencia_numerica_integral"] = referencia_integral
            resultado["tipo_referencia"] = f"Romberg (nivel 7) sobre RK4 de {pasos_ref_int} pasos"
    else:
        n = p["cantidad_nodos"]
        inicio, fin = p["inicio"], p["fin"]
        todos_x = [inicio + (fin - inicio) * i / (n - 1) for i in range(n)]
        funcion_senal: Callable[[float], float]
        if p["senal"] == "sin":
            funcion_senal = math.sin
        elif p["senal"] == "exp":
            funcion_senal = lambda t: math.exp(-t)
        else:
            funcion_senal = lambda t: 1.0 / (1.0 + 25.0 * (t - 0.5) ** 2)
        ocultos = sorted({round((i + 1) * (n - 1) / (p["cantidad_ocultos"] + 1)) for i in range(p["cantidad_ocultos"])})
        test_x = [todos_x[i] for i in ocultos]
        test_y = [funcion_senal(t) for t in test_x]
        nodos_x = [x for i, x in enumerate(todos_x) if i not in ocultos]
        nodos_y = [funcion_senal(x) for x in nodos_x]
        densos = [inicio + (fin - inicio) * i / 120 for i in range(121)]
        referencia_densa = [funcion_senal(t) for t in densos]
        if metodo == "lagrange":
            resultado = interpolacion.lagrange(nodos_x, nodos_y, test_x, referencia=test_y)
            curva = interpolacion.lagrange(nodos_x, nodos_y, densos)
        elif metodo == "newton_interpolacion":
            resultado = interpolacion.newton_diferencias_divididas(nodos_x, nodos_y, test_x, referencia=test_y)
            curva = interpolacion.newton_diferencias_divididas(nodos_x, nodos_y, densos)
        else:
            resultado = interpolacion.splines_cubicos_naturales(nodos_x, nodos_y, test_x, referencia=test_y)
            curva = interpolacion.splines_cubicos_naturales(nodos_x, nodos_y, densos)
        resultado["curva"] = [
            {"x": punto["x"], "y": punto["y"], "referencia": referencia_densa[i]}
            for i, punto in enumerate(curva["curva"])
        ]
        resultado["nodos_ocultos"] = [{"x": x, "y": y} for x, y in zip(test_x, test_y)]

    resultado["modulo"] = modulo
    resultado["escenario"] = clave
    resultado["parametros"] = deepcopy(p)
    return resultado
