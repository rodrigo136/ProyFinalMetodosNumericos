"""Parámetros didácticos y reproducibles de los cuatro módulos SIMTELE-RISK."""

from __future__ import annotations

import math
from copy import deepcopy
from datetime import date
from typing import Any, Callable, Dict, List

try:
    from . import edo, integracion, interpolacion, raices
    from .errores import numero_condicion
    from .sistemas_lineales import (
        A_REFERENCIA,
        B_REFERENCIA,
        factorizacion_lu,
        gauss_seidel,
        gradiente_conjugado,
        jacobi,
    )
except ImportError:
    import edo
    import integracion
    import interpolacion
    import raices
    from errores import numero_condicion
    from sistemas_lineales import (
        A_REFERENCIA,
        B_REFERENCIA,
        factorizacion_lu,
        gauss_seidel,
        gradiente_conjugado,
        jacobi,
    )

ESCENARIOS_MODULO: Dict[int, Dict[str, Any]] = {
    1: {
        "codigo": "CE-001",
        "nombre": "Detención de emergencia de cabinas",
        "metodos": ["rk2", "rk4", "trapecio", "simpson", "romberg", "biseccion", "newton", "secante"],
        "escenarios": {
            "NORMAL": {"descripcion": "Referencia académica de frenado con desaceleración constante v0=6 m/s y a=1.5 m/s².", "parametros": {"velocidad_inicial": 6.0, "desaceleracion": 1.5, "amplitud_desaceleracion": 0.0, "distancia_disponible": 15.0, "tiempo_reaccion": 0.8, "pasos": 80}},
            "ESTRES": {"descripcion": "Exigencia física sintética con desaceleración variable en el tiempo; no implica por sí sola inestabilidad numérica.", "parametros": {"velocidad_inicial": 8.0, "desaceleracion": 2.0, "amplitud_desaceleracion": 0.15, "distancia_disponible": 20.0, "tiempo_reaccion": 1.2, "pasos": 120}},
            "MAL_CONDICIONADO": {"descripcion": "Sensibilidad del tiempo de parada ante una desaceleración pequeña; condición matemática y estabilidad se informan por separado.", "parametros": {"velocidad_inicial": 9.0, "desaceleracion": 0.75, "amplitud_desaceleracion": 0.02, "distancia_disponible": 35.0, "tiempo_reaccion": 1.0, "pasos": 160}},
        },
    },
    2: {
        "codigo": "CE-002",
        "nombre": "Deterioro mecánico y mantenimiento",
        "metodos": ["biseccion", "newton", "secante", "jacobi", "gauss_seidel", "lu", "gradiente_conjugado"],
        "escenarios": {
            "NORMAL": {"descripcion": "Proyección sintética gradual para planificar mantenimiento de una línea hipotética.", "parametros": {"deterioro_inicial": 0.1, "tasa": 0.03, "curvatura": 0.002, "umbral": 1.0, "horizonte": 24.0, "linea": "Línea Roja (ejemplo académico)", "mantenimiento_inicio": 10.0, "mantenimiento_fin": 11.0, "fecha_inicio": "2026-01-01"}},
            "ESTRES": {"descripcion": "Desgaste sintético acelerado y mantenimiento programado que puede coincidir con el cruce del umbral.", "parametros": {"deterioro_inicial": 0.1, "tasa": 0.07, "curvatura": 0.006, "umbral": 1.0, "horizonte": 16.0, "linea": "Línea Amarilla (ejemplo académico)", "mantenimiento_inicio": 5.0, "mantenimiento_fin": 7.0, "fecha_inicio": "2026-01-01"}},
            "MAL_CONDICIONADO": {"descripcion": "Sensibilidad matemática: umbral próximo al estado inicial y tasa pequeña; no presupone fallo de convergencia.", "parametros": {"deterioro_inicial": 0.1, "tasa": 0.00001, "curvatura": 0.0, "umbral": 0.1001, "horizonte": 20.0, "linea": "Línea Morada (ejemplo académico)", "mantenimiento_inicio": 2.0, "mantenimiento_fin": 3.0, "fecha_inicio": "2026-01-01"}},
        },
    },
    3: {
        "codigo": "CE-003",
        "nombre": "Oscilaciones por viento",
        "metodos": ["rk2", "rk4", "trapecio", "simpson", "romberg"],
        "escenarios": {
            "NORMAL": {"descripcion": "Sistema masa-resorte-amortiguador de referencia (m=500 kg, k=1200 N/m, c=40 Ns/m) ante ráfaga sintética.", "parametros": {"masa": 500.0, "amortiguamiento": 40.0, "rigidez": 1200.0, "fuerza": 1200.0, "frecuencia": 1.0, "tiempo_final": 12.0, "pasos": 240, "umbral_balanceo": 0.35}},
            "ESTRES": {"descripcion": "Ráfaga sintética cercana a resonancia con parámetros físicos de referencia; la amplitud se compara con un umbral didáctico.", "parametros": {"masa": 500.0, "amortiguamiento": 40.0, "rigidez": 1200.0, "fuerza": 4500.0, "frecuencia": 1.52, "tiempo_final": 12.0, "pasos": 360, "umbral_balanceo": 0.35}},
            "MAL_CONDICIONADO": {"descripcion": "Rigidez elevada y paso deliberadamente crítico; condicionamiento del problema y estabilidad de RK se reportan por separado.", "parametros": {"masa": 500.0, "amortiguamiento": 40.0, "rigidez": 120000.0, "fuerza": 1200.0, "frecuencia": 1.0, "tiempo_final": 12.0, "pasos": 40, "umbral_balanceo": 0.35}},
        },
    },
    4: {
        "codigo": "CE-004",
        "nombre": "Reconstrucción de señales de sensores",
        "metodos": ["lagrange", "newton_interpolacion", "spline"],
        "escenarios": {
            "NORMAL": {"descripcion": "Telemetría sintética y(t)=sin(t), con pérdida de paquetes que se reconstruyen en nodos ocultos.", "parametros": {"senal": "sin", "cantidad_nodos": 9, "cantidad_ocultos": 3, "inicio": 0.0, "fin": 3.141592653589793, "ruido": 0.0}},
            "ESTRES": {"descripcion": "Telemetría sintética exp(-t) con nodos perdidos y ruido electromagnético hipotético.", "parametros": {"senal": "exp", "cantidad_nodos": 11, "cantidad_ocultos": 5, "inicio": 0.0, "fin": 4.0, "ruido": 0.01}},
            "MAL_CONDICIONADO": {"descripcion": "Nodos uniformes y señal de Runge para ilustrar sensibilidad polinómica/Vandermonde, no un fallo de convergencia.", "parametros": {"senal": "runge", "cantidad_nodos": 15, "cantidad_ocultos": 5, "inicio": 0.0, "fin": 1.0, "ruido": 0.0}},
        },
    },
}


def obtener_escenarios_modulo() -> Dict[str, Any]:
    """Devuelve una copia serializable para evitar mutaciones del catálogo."""
    return {"modulos": {str(numero): deepcopy(datos) for numero, datos in ESCENARIOS_MODULO.items()}}


def _raiz_analitica_modulo_1(v0: float, aceleracion: float) -> float:
    return v0 / aceleracion


def _validar_parametros(
    modulo: int,
    parametros: Dict[str, Any],
    predeterminados: Dict[str, Any],
) -> Dict[str, Any]:
    permitidos = set(ESCENARIOS_MODULO[modulo]["escenarios"]["NORMAL"]["parametros"])
    desconocidos = set(parametros) - permitidos
    if desconocidos:
        raise ValueError(f"Parámetros no reconocidos: {', '.join(sorted(desconocidos))}")
    base = deepcopy(predeterminados)
    base.update(parametros)
    for clave, valor in base.items():
        if isinstance(valor, bool):
            raise ValueError(f"El parámetro {clave} no puede ser booleano")
        if isinstance(valor, (int, float)) and not math.isfinite(float(valor)):
            raise ValueError(f"El parámetro {clave} debe ser finito")
    if modulo == 1 and (
        base["velocidad_inicial"] <= 0
        or base["desaceleracion"] <= 0
        or base["amplitud_desaceleracion"] < 0
        or base["amplitud_desaceleracion"] >= 1
        or base["distancia_disponible"] <= 0
        or base["tiempo_reaccion"] < 0
        or not isinstance(base["pasos"], int)
        or base["pasos"] < 1
        or base["pasos"] > 10000
    ):
        raise ValueError("Velocidad y desaceleración deben ser positivas; la amplitud variable debe estar entre 0 y 1")
    if modulo == 2 and (
        base["horizonte"] <= 0
        or base["tasa"] < 0
        or base["curvatura"] < 0
        or (base["tasa"] == 0 and base["curvatura"] == 0)
        or base["umbral"] <= base["deterioro_inicial"]
        or base["mantenimiento_inicio"] < 0
        or base["mantenimiento_fin"] < base["mantenimiento_inicio"]
        or not isinstance(base["fecha_inicio"], str)
        or not isinstance(base["linea"], str)
        or not base["linea"].strip()
    ):
        raise ValueError("El horizonte debe ser positivo y el umbral superar el deterioro inicial")
    if modulo == 2:
        try:
            date.fromisoformat(base["fecha_inicio"])
        except ValueError as exc:
            raise ValueError("La fecha de inicio debe tener formato AAAA-MM-DD") from exc
    if modulo == 3 and (
        base["masa"] <= 0
        or base["rigidez"] <= 0
        or base["amortiguamiento"] < 0
        or base["fuerza"] < 0
        or base["frecuencia"] < 0
        or base["tiempo_final"] <= 0
        or base["umbral_balanceo"] < 0
        or not isinstance(base["pasos"], int)
        or base["pasos"] < 1
        or base["pasos"] > 10000
    ):
        raise ValueError("Masa, rigidez y tiempo deben ser positivos; amortiguamiento no negativo")
    if modulo == 4 and (
        not isinstance(base["cantidad_nodos"], int)
        or not isinstance(base["cantidad_ocultos"], int)
        or base["cantidad_nodos"] < 3
        or base["cantidad_nodos"] > 30
        or base["cantidad_ocultos"] < 1
        or base["cantidad_ocultos"] >= base["cantidad_nodos"] - 1
        or base["fin"] <= base["inicio"]
        or base["ruido"] < 0
        or base["ruido"] > 0.25
        or base["senal"] not in {"sin", "exp", "runge"}
    ):
        raise ValueError("Parámetros inválidos para reconstruir la señal")
    return base


def ejecutar_metodo_modulo(
    modulo: int,
    escenario: str,
    metodo: str,
    parametros: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Ejecuta un método de un módulo usando exclusivamente parámetros publicados."""
    if modulo not in ESCENARIOS_MODULO:
        raise ValueError("El módulo debe estar entre 1 y 4")
    clave = str(escenario).upper().replace(" ", "_")
    datos = ESCENARIOS_MODULO[modulo]["escenarios"].get(clave)
    if datos is None:
        raise ValueError("Escenario inválido; use NORMAL, ESTRES o MAL_CONDICIONADO")
    metodos_lineales = {"jacobi", "gauss_seidel", "lu", "gradiente_conjugado"}
    if metodo not in ESCENARIOS_MODULO[modulo]["metodos"] and not (modulo == 2 and metodo in metodos_lineales):
        raise ValueError("El método seleccionado no aplica a este módulo")

    p = _validar_parametros(modulo, {**(parametros or {})}, datos["parametros"])
    resultado: Dict[str, Any]
    if modulo == 1:
        v0, desaceleracion = p["velocidad_inicial"], p["desaceleracion"]
        amplitud = p["amplitud_desaceleracion"]
        omega = 0.7
        aceleracion = lambda t: desaceleracion * (1.0 + amplitud * math.sin(omega * t))
        funcion_v = lambda t: v0 - desaceleracion * t - desaceleracion * amplitud * (1.0 - math.cos(omega * t)) / omega
        integral_v = lambda t: v0 * t - 0.5 * desaceleracion * t * t - desaceleracion * amplitud * (t / omega - math.sin(omega * t) / omega ** 2)
        if amplitud == 0:
            tiempo_parada = _raiz_analitica_modulo_1(v0, desaceleracion)
        else:
            intervalo = (0.0, v0 / (desaceleracion * (1.0 - amplitud)))
            tiempo_parada = raices.biseccion(funcion_v, *intervalo)["raiz_aproximada"]
        referencia_distancia = integral_v(tiempo_parada)
        if metodo in {"rk2", "rk4"}:
            funcion = lambda t, estado: [estado[1], -aceleracion(t)]
            referencia = lambda t: [integral_v(t), funcion_v(t)]
            resultado = edo.resolver_edo(funcion, (0.0, tiempo_parada), [0.0, v0], p["pasos"], metodo=metodo, referencia=referencia)
            resultado["cantidad"] = "trayectoria y velocidad"
        elif metodo in {"trapecio", "simpson", "romberg"}:
            n = p["pasos"] if metodo != "romberg" else None
            n_efectivos = n
            if metodo == "trapecio":
                resultado = integracion.trapecio_compuesto(funcion_v, 0.0, tiempo_parada, n, referencia=referencia_distancia)
            elif metodo == "simpson":
                n_efectivos = n if n % 2 == 0 else n + 1
                resultado = integracion.simpson_13_compuesto(funcion_v, 0.0, tiempo_parada, n_efectivos, referencia=referencia_distancia)
            else:
                resultado = integracion.romberg(funcion_v, 0.0, tiempo_parada, niveles=6, referencia=referencia_distancia)
            if n_efectivos is not None:
                resultado["tabla_refinamiento"][-1]["subintervalos"] = n_efectivos
            resultado["cantidad"] = "Distancia de frenado (integral de v(t))"
            resultado["curva"] = [
                {"x": tiempo_parada * i / 80, "y": funcion_v(tiempo_parada * i / 80)}
                for i in range(81)
            ]
        else:
            funcion_root = funcion_v
            derivada = lambda t: -aceleracion(t)
            if metodo == "biseccion":
                resultado = raices.biseccion(funcion_root, 0.0, tiempo_parada * 1.5, referencia=tiempo_parada)
            elif metodo == "newton":
                resultado = raices.newton_raphson(funcion_root, derivada, tiempo_parada * 0.8, referencia=tiempo_parada)
            else:
                resultado = raices.secante(funcion_root, 0.0, tiempo_parada * 1.5, referencia=tiempo_parada)
            resultado["valor_referencia_analitica"] = tiempo_parada
            resultado["cantidad"] = "Tiempo de detención (raíz de v(t))"
            resultado["curva"] = [
                {"x": tiempo_parada * i / 80, "y": funcion_root(tiempo_parada * i / 80)}
                for i in range(81)
            ]
        resultado["tipo"] = (
            "edo" if metodo in {"rk2", "rk4"}
            else "integracion" if metodo in {"trapecio", "simpson", "romberg"}
            else "raices"
        )
        resultado["referencia_analitica"] = {"tiempo_parada": tiempo_parada, "distancia_frenado": referencia_distancia}
        resultado["tiempo_reaccion"] = p["tiempo_reaccion"]
        resultado["distancia_reaccion"] = v0 * p["tiempo_reaccion"]
        resultado["distancia_total"] = referencia_distancia + resultado["distancia_reaccion"]
        resultado["distancia_disponible"] = p["distancia_disponible"]
        resultado["supera_distancia_segura"] = resultado["distancia_total"] > p["distancia_disponible"]
    elif modulo == 2:
        d0, tasa, curva, umbral, horizonte = (p[k] for k in ("deterioro_inicial", "tasa", "curvatura", "umbral", "horizonte"))
        funcion = lambda t: d0 + tasa * t + curva * t * t - umbral
        derivada = lambda t: tasa + 2.0 * curva * t
        raiz_analitica = (-tasa + math.sqrt(tasa * tasa + 4.0 * curva * (umbral - d0))) / (2.0 * curva) if curva else (umbral - d0) / tasa
        if metodo in metodos_lineales:
            if clave == "MAL_CONDICIONADO":
                matriz = [[1.0, 0.99, 0.0, 0.0], [0.99, 1.0, 0.0, 0.0], [0.0, 0.0, 2.0, 0.5], [0.0, 0.0, 0.5, 2.0]]
                vector = [1.99, 1.99, 2.5, 2.5]
            elif clave == "ESTRES":
                matriz = [[20.0, 4.0, 2.0, 0.0], [4.0, 20.0, 2.0, 2.0], [2.0, 2.0, 16.0, 4.0], [0.0, 2.0, 4.0, 18.0]]
                vector = [26.0, 48.0, 62.0, 56.0]
            else:
                matriz, vector = A_REFERENCIA, B_REFERENCIA
            funcion_metodo = {"jacobi": jacobi, "gauss_seidel": gauss_seidel, "lu": factorizacion_lu, "gradiente_conjugado": gradiente_conjugado}[metodo]
            if metodo in {"jacobi", "gauss_seidel", "gradiente_conjugado"}:
                resultado = funcion_metodo(
                    A=matriz, b=vector, tolerancia=1e-8, max_iteraciones=10000
                )
            else:
                resultado = funcion_metodo(A=matriz, b=vector)
            resultado["numero_condicion_kappa_2"] = numero_condicion(matriz)
            resultado["matriz"] = matriz
            resultado["vector"] = vector
            resultado["tipo_escenario"] = "mal_condicionamiento matemático" if clave == "MAL_CONDICIONADO" else ("estrés operativo sintético" if clave == "ESTRES" else "referencia normal")
            resultado["cantidad"] = "Solución del sistema SPD 4×4"
        else:
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
            resultado["cantidad"] = "Tiempo hasta cruce de D_umbral"
            resultado["tipo"] = "raices"
        resultado["linea"] = p["linea"]
        resultado["tiempo_mantenimiento"] = [p["mantenimiento_inicio"], p["mantenimiento_fin"]]
        resultado["fecha_inicio_modelo"] = p["fecha_inicio"]
        resultado["umbral"] = umbral
        resultado["curva_deterioro"] = [
            {
                "x": horizonte * i / 100,
                "y": d0 + tasa * horizonte * i / 100 + curva * (horizonte * i / 100) ** 2,
            }
            for i in range(101)
        ]
        resultado["referencia_analitica_deterioro"] = {"tiempo_umbral": raiz_analitica}
    elif modulo == 3:
        masa, amortiguamiento, rigidez, fuerza, frecuencia = (p[k] for k in ("masa", "amortiguamiento", "rigidez", "fuerza", "frecuencia"))
        def rhs(t: float, estado: List[float]) -> List[float]:
            x, v = estado
            return [v, (fuerza * math.sin(frecuencia * t) - amortiguamiento * v - rigidez * x) / masa]

        x0, v0 = 0.1, 0.0
        amortiguamiento_relativo = amortiguamiento / (2.0 * masa)
        frecuencia_amortiguada = math.sqrt(max(0.0, rigidez / masa - amortiguamiento_relativo ** 2))
        def referencia_libre(t: float) -> List[float]:
            if frecuencia_amortiguada == 0:
                return [0.0, 0.0]
            c, s = math.cos(frecuencia_amortiguada * t), math.sin(frecuencia_amortiguada * t)
            factor = math.exp(-amortiguamiento_relativo * t)
            coeficiente = (v0 + amortiguamiento_relativo * x0) / frecuencia_amortiguada
            x = factor * (x0 * c + coeficiente * s)
            v = factor * ((-amortiguamiento_relativo * x0 + coeficiente * frecuencia_amortiguada) * c + (-amortiguamiento_relativo * coeficiente - x0 * frecuencia_amortiguada) * s)
            return [x, v]

        pasos_ref = min(10000, max(int(p["pasos"]) * 10, 4000))
        solucion_ref = edo.resolver_edo(rhs, (0.0, p["tiempo_final"]), [x0, v0], pasos_ref, metodo="rk4")
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
                [x0, v0],
                p["pasos"],
                metodo=metodo,
                referencia=referencia_rk4,
            )
            resultado["magnitud"] = "desplazamiento x(t) y velocidad v(t)"
            resultado["cantidad"] = "Trayectoria x(t) y velocidad v(t)"
            resultado["tipo_referencia"] = f"RK4 de alta precisión ({pasos_ref} pasos)"
            resultado["maximo_balanceo"] = max(abs(fila["aproximacion"][0]) for fila in resultado["tabla_temporal"])
            resultado["umbral_balanceo"] = p["umbral_balanceo"]
            resultado["supera_umbral_balanceo"] = resultado["maximo_balanceo"] > p["umbral_balanceo"]
            resultado["tipo"] = "edo"
        else:
            solucion = edo.resolver_edo(rhs, (0.0, p["tiempo_final"]), [x0, v0], p["pasos"], metodo="rk4")
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
            solucion_ref_int = edo.resolver_edo(rhs, (0.0, p["tiempo_final"]), [x0, v0], pasos_ref_int, metodo="rk4")
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
            resultado["maximo_balanceo"] = max(abs(valor) for valor in desplazamientos)
            resultado["umbral_balanceo"] = p["umbral_balanceo"]
            resultado["supera_umbral_balanceo"] = resultado["maximo_balanceo"] > p["umbral_balanceo"]
            resultado["cantidad"] = "Integral de x(t)^2; indicador energético didáctico"
            resultado["tipo"] = "integracion"
        indices_referencia = range(0, len(tiempos_ref), max(1, len(tiempos_ref) // 80))
        resultado["curva_referencia_libre"] = [
            {"x": tiempos_ref[indice], "y": referencia_libre(tiempos_ref[indice])[0]}
            for indice in indices_referencia
        ]
        resultado["referencia_analitica_subamortiguada"] = [
            referencia_libre(tiempos_ref[indice]) for indice in indices_referencia
        ]
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
        ruido = p["ruido"]
        nodos_y = [funcion_senal(x) + ruido * math.sin(31.0 * i + 0.3) for i, x in enumerate(nodos_x)]
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
        resultado["tipo"] = "interpolacion"
        resultado["curva"] = [
            {"x": punto["x"], "y": punto["y"], "referencia": referencia_densa[i]}
            for i, punto in enumerate(curva["curva"])
        ]
        resultado["nodos_ocultos"] = [{"x": x, "y": y} for x, y in zip(test_x, test_y)]

    resultado["modulo"] = modulo
    resultado["escenario"] = clave
    resultado["parametros"] = deepcopy(p)
    if modulo == 1:
        resultado["conclusion_numerica"] = f"El método {resultado.get('metodo', metodo)} aproxima una detención en {tiempo_parada:.6g} s; el error se mide frente al modelo analítico (constante) o a su expresión variable."
        resultado["conclusion_problema"] = f"En este caso didáctico, la distancia de frenado más reacción es {resultado.get('distancia_total', referencia_distancia):.6g} m frente a {p['distancia_disponible']:.6g} m disponibles. No representa límites ni datos operativos reales."
    elif modulo == 2 and metodo in metodos_lineales:
        resultado["conclusion_numerica"] = f"κ₂(A)={resultado['numero_condicion_kappa_2']:.6g}; la condición cuantifica sensibilidad, mientras convergencia y residual describen el desempeño del método."
        resultado["conclusion_problema"] = "El sistema SPD de 4×4 es un modelo de relaciones mecánicas sintéticas; no permite inferir el estado de una línea real."
    elif modulo == 2:
        resultado["conclusion_numerica"] = f"El cruce D(t)=D_umbral se estima en {raiz_analitica:.6g} unidades de tiempo por la referencia analítica."
        resultado["conclusion_problema"] = f"La línea hipotética {p['linea']} estaría indisponible durante el mantenimiento configurado; el cruce del umbral orienta el ejemplo de calendario, no un plan real."
    elif modulo == 3:
        resultado["conclusion_numerica"] = f"RK calcula la respuesta forzada y reporta estabilidad separada del condicionamiento; amplitud máxima {resultado.get('maximo_balanceo', 0):.6g} m."
        resultado["conclusion_problema"] = "La amplitud y la integral de x(t)² describen solo esta masa-resorte-amortiguador sintético; no establecen gálibos ni umbrales de seguridad oficiales."
    else:
        resultado["cantidad"] = "Señal reconstruida y error en nodos ocultos"
        resultado["conclusion_numerica"] = f"El error en nodos ocultos para {resultado.get('metodo', metodo)} es {resultado.get('error_absoluto_final')} (norma de error absoluto)."
        resultado["conclusion_problema"] = "La reconstrucción recupera lecturas sintéticas bajo pérdida y ruido controlados; no es telemetría ni diagnóstico de sensores reales."
    return resultado
