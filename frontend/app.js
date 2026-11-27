"use strict";

const REFERENCIA_DEFAULT = {
    A: [
        [10, 2, 1, 0],
        [2, 10, 1, 1],
        [1, 1, 8, 2],
        [0, 1, 2, 9]
    ],
    b: [13, 24, 31, 28]
};

const API_BASE = (() => {
    const override = new URLSearchParams(window.location.search).get("api");
    if (override) {
        return override.replace(/\/+$/, "");
    }
    // Si estamos en producción (Render u otro servidor), usamos rutas relativas
    if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
        return "";
    }
    return "http://127.0.0.1:5000";
})();

const METODOS = {
    exacta: {
        id: "exacta",
        nombre: "Solución exacta",
        endpoint: "exacta",
        iterativo: false,
        detalle: "Eliminación gaussiana con pivoteo parcial."
    },
    lu: {
        id: "lu",
        nombre: "Factorización LU",
        endpoint: "lu",
        iterativo: false,
        detalle: "Factorización con pivoteo parcial y sustitución."
    },
    jacobi: {
        id: "jacobi",
        nombre: "Jacobi",
        endpoint: "jacobi",
        iterativo: true,
        detalle: "Método iterativo por diagonal dominante."
    },
    "gauss-seidel": {
        id: "gauss-seidel",
        nombre: "Gauss-Seidel",
        endpoint: "gauss-seidel",
        iterativo: true,
        detalle: "Actualización sucesiva de componentes."
    },
    "gradiente-conjugado": {
        id: "gradiente-conjugado",
        nombre: "Gradiente conjugado",
        endpoint: "gradiente-conjugado",
        iterativo: true,
        detalle: "Método iterativo para matrices SPD."
    }
};

const ESTADOS = {
    completada: "Completada",
    fallida: "Fallida",
    pendiente: "Pendiente",
    en_ejecucion: "En ejecución",
    cancelada: "Cancelada"
};

const MODULOS = {
    1: { nombre: "Detención de emergencia", caso: "CE-001" },
    2: { nombre: "Deterioro mecánico", caso: "CE-002" },
    3: { nombre: "Oscilaciones por viento", caso: "CE-003" },
    4: { nombre: "Reconstrucción de sensores", caso: "CE-004" }
};

const METODOS_NUMERICOS = {
    rk2: { nombre: "Runge-Kutta 2 (Heun)", categoria: "edo" },
    rk4: { nombre: "Runge-Kutta 4 clásico", categoria: "edo" },
    trapecio: { nombre: "Trapecio compuesto", categoria: "integracion" },
    simpson: { nombre: "Simpson 1/3 compuesto", categoria: "integracion" },
    romberg: { nombre: "Romberg", categoria: "integracion" },
    biseccion: { nombre: "Bisección", categoria: "raices" },
    newton: { nombre: "Newton-Raphson", categoria: "raices" },
    secante: { nombre: "Secante", categoria: "raices" },
    lagrange: { nombre: "Lagrange", categoria: "interpolacion" },
    newton_interpolacion: { nombre: "Newton por diferencias divididas", categoria: "interpolacion" },
    spline: { nombre: "Spline cúbico natural", categoria: "interpolacion" },
    jacobi: { nombre: "Jacobi", categoria: "lineal" },
    gauss_seidel: { nombre: "Gauss-Seidel", categoria: "lineal" },
    lu: { nombre: "Factorización LU", categoria: "lineal" },
    gradiente_conjugado: { nombre: "Gradiente conjugado", categoria: "lineal" }
};

const ETIQUETAS_PARAMETROS = {
    velocidad_inicial: "Velocidad inicial (m/s)",
    desaceleracion: "Desaceleración (m/s²)",
    amplitud_desaceleracion: "Variación temporal de desaceleración",
    distancia_disponible: "Distancia segura disponible (m)",
    tiempo_reaccion: "Tiempo de reacción (s)",
    deterioro_inicial: "Deterioro inicial D₀",
    tasa: "Tasa α",
    curvatura: "Curvatura β",
    umbral: "Umbral D",
    horizonte: "Horizonte temporal",
    linea: "Línea hipotética",
    mantenimiento_inicio: "Inicio de mantenimiento (unidades de tiempo)",
    mantenimiento_fin: "Fin de mantenimiento (unidades de tiempo)",
    fecha_inicio: "Fecha sintética de inicio",
    masa: "Masa (kg)",
    amortiguamiento: "Amortiguamiento (Ns/m)",
    rigidez: "Rigidez (N/m)",
    fuerza: "Amplitud de ráfaga (N)",
    frecuencia: "Frecuencia de ráfaga (rad/s)",
    tiempo_final: "Tiempo final (s)",
    pasos: "Pasos de integración",
    umbral_balanceo: "Umbral didáctico de balanceo (m)",
    senal: "Señal sintética",
    cantidad_nodos: "Nodos totales",
    cantidad_ocultos: "Nodos ocultos",
    inicio: "Inicio del dominio",
    fin: "Fin del dominio",
    ruido: "Ruido sintético (amplitud)"
};

const state = {
    casos: [],
    escenarios: [],
    simulaciones: [],
    escenariosModulo: null,
    referencia: { A: REFERENCIA_DEFAULT.A, b: REFERENCIA_DEFAULT.b },
    metodoId: "exacta",
    escenarioSeleccionado: null,
    casoFiltro: null,
    moduloSeleccionado: null,
    ultimoResultado: null,
    ultimoMetodo: null,
    ultimoEscenario: null,
    ultimaEjecucion: null,
    ultimaConfiguracion: null,
    comparaciones: [],
    animationFrame: null,
    animationStart: null,
    animationProgress: 0,
    animationPlaying: false,
    datosCargados: false,
    ejecutando: false,
    guardando: false
};

let toastTimer = null;
let welcomeInterval = null;
let welcomeTimeout = null;
let navScrollFrame = null;
let navScrollTarget = null;
let navScrollTimer = null;

function $(id) {
    return document.getElementById(id);
}

function clonar(valor) {
    return JSON.parse(JSON.stringify(valor));
}

async function apiRequest(ruta, opciones = {}) {
    const config = {
        ...opciones,
        headers: { ...(opciones.headers || {}) }
    };

    if (config.body !== undefined && typeof config.body !== "string") {
        config.body = JSON.stringify(config.body);
        config.headers["Content-Type"] = "application/json";
    }

    let respuesta;
    try {
        respuesta = await fetch(`${API_BASE}${ruta}`, config);
    } catch (error) {
        throw new Error(`No se pudo conectar con la API en ${API_BASE}`);
    }

    const texto = await respuesta.text();
    let datos = null;
    if (texto) {
        try {
            datos = JSON.parse(texto);
        } catch (error) {
            datos = texto;
        }
    }

    if (!respuesta.ok) {
        const mensaje = datos && typeof datos === "object" && datos.error
            ? datos.error
            : `Error HTTP ${respuesta.status}`;
        throw new Error(mensaje);
    }

    return datos;
}

function formatearDecimal(valor, decimales = 8) {
    const numero = Number(valor);
    if (!Number.isFinite(numero)) {
        return "—";
    }
    if (numero === 0) {
        return "0";
    }
    const absoluto = Math.abs(numero);
    if (absoluto >= 1e6 || absoluto < 1e-4) {
        return numero.toExponential(4);
    }
    return numero.toFixed(decimales).replace(/\.?0+$/, "");
}

function formatearError(valor) {
    const numero = Number(valor);
    if (valor === null || valor === undefined || Number.isNaN(numero)) {
        return "—";
    }
    if (!Number.isFinite(numero)) {
        return "∞";
    }
    if (numero === 0) {
        return "0.000e+0";
    }
    return numero.toExponential(3);
}

function formatearPorcentaje(valor) {
    return `${formatearError(valor)} %`;
}

function formatearFecha(valor) {
    if (!valor) {
        return "—";
    }

    let texto = String(valor);
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(texto)) {
        texto = `${texto.replace(" ", "T")}Z`;
    }

    const fecha = new Date(texto);
    if (Number.isNaN(fecha.getTime())) {
        return String(valor);
    }

    return new Intl.DateTimeFormat("es", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    }).format(fecha);
}

function capitalizar(texto) {
    if (!texto) {
        return "—";
    }
    const limpio = String(texto).replace(/_/g, " ");
    return limpio.charAt(0).toUpperCase() + limpio.slice(1);
}

function mostrarToast(mensaje, tipo = "info") {
    const toast = $("toast");
    toast.textContent = mensaje;
    toast.className = `toast toast-${tipo}`;
    toast.hidden = false;

    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
        toast.hidden = true;
    }, 4500);
}

function actualizarEstadoApi(estado) {
    const textos = {
        waiting: "Comprobando API",
        online: "API conectada",
        offline: "API sin conexión"
    };
    const textosSidebar = {
        waiting: "Conectando",
        online: "Base conectada",
        offline: "Sin conexión"
    };

    const pill = $("api-status");
    pill.classList.remove(
        "status-pill-online",
        "status-pill-offline",
        "status-pill-waiting"
    );
    pill.classList.add(`status-pill-${estado}`);
    $("api-status-text").textContent = textos[estado];

    $("sidebar-status-dot").className = `status-dot status-dot-${estado}`;
    $("sidebar-status-text").textContent = textosSidebar[estado];
}

function renderizarEstadisticas() {
    const valor = (coleccion) => state.datosCargados ? coleccion.length : "—";

    $("stat-casos").textContent = valor(state.casos);
    $("stat-escenarios").textContent = valor(state.escenarios);
    $("stat-simulaciones").textContent = valor(state.simulaciones);
}

function obtenerEscenarioSeleccionado() {
    return state.escenarios.find(
        (escenario) => Number(escenario.id) === Number(state.escenarioSeleccionado)
    ) || null;
}

function escenariosFiltrados() {
    if (!state.casoFiltro) {
        return state.escenarios;
    }
    return state.escenarios.filter(
        (escenario) => escenario.caso_codigo === state.casoFiltro
    );
}

function renderizarEscenarios() {
    const select = $("scenario-select");
    const seleccionAnterior = state.escenarioSeleccionado;
    const escenarios = escenariosFiltrados();

    select.replaceChildren();

    if (!escenarios.length) {
        const opcion = document.createElement("option");
        opcion.value = "";
        opcion.textContent = "Sin escenarios disponibles";
        select.appendChild(opcion);
        select.disabled = true;
        state.escenarioSeleccionado = null;
        $("scenario-detail").hidden = true;
        actualizarAcciones();
        return;
    }

    select.disabled = false;

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = state.casoFiltro
        ? "Selecciona un escenario del módulo"
        : "Selecciona un escenario";
    select.appendChild(placeholder);

    const grupos = new Map();
    for (const escenario of escenarios) {
        const clave = escenario.caso_estudio_id;
        if (!grupos.has(clave)) {
            grupos.set(clave, {
                codigo: escenario.caso_codigo || "Caso",
                nombre: escenario.caso_nombre || "",
                escenarios: []
            });
        }
        grupos.get(clave).escenarios.push(escenario);
    }

    for (const grupo of grupos.values()) {
        const optgroup = document.createElement("optgroup");
        optgroup.label = `${grupo.codigo} · ${grupo.nombre}`;

        for (const escenario of grupo.escenarios) {
            const opcion = document.createElement("option");
            opcion.value = String(escenario.id);
            opcion.textContent = `${escenario.nombre} (${capitalizar(escenario.tipo)})`;
            optgroup.appendChild(opcion);
        }

        select.appendChild(optgroup);
    }

    const sigueDisponible = escenarios.some(
        (escenario) => Number(escenario.id) === Number(seleccionAnterior)
    );
    state.escenarioSeleccionado = sigueDisponible
        ? Number(seleccionAnterior)
        : Number(escenarios[0].id);

    select.value = String(state.escenarioSeleccionado);
    actualizarDetalleEscenario();
    actualizarAcciones();
}

function seleccionarEscenarioPersistente(codigo) {
    const escenario = escenariosFiltrados().find((item) => item.codigo === codigo);
    if (!escenario) {
        return;
    }
    state.escenarioSeleccionado = Number(escenario.id);
    $("scenario-select").value = String(escenario.id);
    actualizarDetalleEscenario();
    actualizarAcciones();
}

function actualizarDetalleEscenario() {
    const detalle = $("scenario-detail");
    const escenario = obtenerEscenarioSeleccionado();

    if (!escenario) {
        detalle.hidden = true;
        return;
    }

    detalle.hidden = false;
    $("scenario-case").textContent = `${escenario.caso_codigo || "—"} · ${escenario.caso_nombre || ""}`.trim();
    $("scenario-type").textContent = capitalizar(escenario.tipo);
    $("scenario-probability").textContent = escenario.probabilidad === null || escenario.probabilidad === undefined
        ? "—"
        : `${(Number(escenario.probabilidad) * 100).toFixed(1)} %`;
    $("scenario-severity").textContent = capitalizar(escenario.severidad);
}

function renderizarMatrizReferencia() {
    const contenedor = $("matrix-view");
    const { A, b } = state.referencia;

    if (!Array.isArray(A) || !A.length || !Array.isArray(b) || b.length !== A.length) {
        contenedor.textContent = "Sistema de referencia no disponible.";
        return;
    }

    const n = A.length;
    $("system-shape").textContent = `${n} × ${n}`;

    const grid = document.createElement("div");
    grid.className = "matrix-grid";
    grid.style.gridTemplateColumns = `repeat(${n}, minmax(38px, 1fr)) 1px minmax(38px, 1fr)`;

    for (let i = 0; i < n; i += 1) {
        for (let j = 0; j < n; j += 1) {
            const celda = document.createElement("span");
            celda.className = "matrix-cell";
            celda.textContent = formatearDecimal(A[i][j], 4);
            grid.appendChild(celda);
        }

        const separador = document.createElement("span");
        separador.className = "matrix-separator";
        grid.appendChild(separador);

        const celdaB = document.createElement("span");
        celdaB.className = "matrix-cell matrix-cell-vector";
        celdaB.textContent = formatearDecimal(b[i], 4);
        grid.appendChild(celdaB);
    }

    const shell = document.createElement("div");
    shell.className = "matrix-shell";
    shell.appendChild(grid);
    contenedor.replaceChildren(shell);
}

function actualizarPresetNumerico() {
    const selectorMetodo = $("numerical-method");
    const modulo = Number($("numerical-module").value);
    const codigoEscenario = $("numerical-scenario").value;
    const moduloDatos = state.escenariosModulo && state.escenariosModulo.modulos
        ? state.escenariosModulo.modulos[String(modulo)]
        : null;
    const escenario = moduloDatos && moduloDatos.escenarios
        ? moduloDatos.escenarios[codigoEscenario]
        : null;

    selectorMetodo.replaceChildren();
    if (!moduloDatos || !escenario) {
        $("preset-description").textContent = "No se pudieron cargar los parámetros preconfigurados.";
        $("parameter-fields").textContent = "Verifica la conexión con la API.";
        $("run-numerical").disabled = true;
        $("compare-numerical").disabled = true;
        return;
    }

    for (const id of moduloDatos.metodos) {
        const opcion = document.createElement("option");
        opcion.value = id;
        opcion.textContent = METODOS_NUMERICOS[id].nombre;
        selectorMetodo.appendChild(opcion);
    }
    selectorMetodo.value = moduloDatos.metodos[0];
    $("preset-description").textContent = escenario.descripcion;
    renderizarCamposParametros(escenario.parametros);
    $("run-numerical").disabled = false;
    $("compare-numerical").disabled = false;
}

function renderizarCamposParametros(parametros) {
    const contenedor = $("parameter-fields");
    contenedor.replaceChildren();
    Object.entries(parametros).forEach(([clave, valor]) => {
        const campo = document.createElement("div");
        campo.className = "field parameter-field";
        const etiqueta = document.createElement("label");
        const id = `parameter-${clave}`;
        etiqueta.htmlFor = id;
        etiqueta.textContent = ETIQUETAS_PARAMETROS[clave] || clave;
        let control;
        if (clave === "senal") {
            control = document.createElement("select");
            [["sin", "sin(t)"], ["exp", "exp(-t)"], ["runge", "Runge"]].forEach(([valorOpcion, texto]) => {
                const opcion = document.createElement("option");
                opcion.value = valorOpcion;
                opcion.textContent = texto;
                control.appendChild(opcion);
            });
        } else {
            control = document.createElement("input");
            control.type = typeof valor === "number" ? "number" : "text";
            if (typeof valor === "number") control.step = "any";
            if (clave === "fecha_inicio") control.type = "date";
        }
        control.id = id;
        control.dataset.parameter = clave;
        control.value = String(valor);
        control.addEventListener("change", () => {
            if (state.ultimoResultado) {
                limpiarResultado();
                $("numerical-hint").textContent = "Parámetros modificados; vuelve a ejecutar el método.";
            }
        });
        campo.append(etiqueta, control);
        contenedor.appendChild(campo);
    });
}

function leerParametrosNumericos() {
    const parametros = {};
    for (const control of $("parameter-fields").querySelectorAll("[data-parameter]")) {
        const valor = control.type === "number" ? Number(control.value) : control.value;
        if (control.type === "number" && (!control.value.trim() || !Number.isFinite(valor))) {
            control.reportValidity();
            throw new Error(`El parámetro ${ETIQUETAS_PARAMETROS[control.dataset.parameter]} debe ser finito.`);
        }
        parametros[control.dataset.parameter] = valor;
    }
    return parametros;
}

function listaMetodosModulo(modulo) {
    const datos = state.escenariosModulo.modulos[String(modulo)];
    return datos.metodos.map((id) => ({
        id,
        nombre: METODOS_NUMERICOS[id] ? METODOS_NUMERICOS[id].nombre : id,
        categoria: METODOS_NUMERICOS[id] ? METODOS_NUMERICOS[id].categoria : ""
    }));
}

function formatearValorTabla(valor) {
    if (valor === null || valor === undefined) {
        return "—";
    }
    if (Array.isArray(valor)) {
        return `[${valor.map((item) => formatearDecimal(item, 5)).join(", ")}]`;
    }
    if (typeof valor === "object") {
        return JSON.stringify(valor);
    }
    return typeof valor === "number" ? formatearDecimal(valor, 7) : String(valor);
}

function dibujarGrafico(canvasId, series) {
    const canvas = $(canvasId);
    const contexto = canvas.getContext("2d");
    const estilos = window.getComputedStyle(document.documentElement);
    const colorCss = (nombre, respaldo) => estilos.getPropertyValue(nombre).trim() || respaldo;
    const colores = [
        colorCss("--palette-blue", "#355C7D"),
        colorCss("--palette-coral-ink", "#A53F4C"),
        colorCss("--palette-mauve", "#6C5B7B"),
        colorCss("--palette-rose-ink", "#8D455D")
    ];
    const ancho = Math.max(280, canvas.clientWidth);
    const alto = Math.max(180, canvas.clientHeight);
    const escala = window.devicePixelRatio || 1;
    canvas.width = Math.round(ancho * escala);
    canvas.height = Math.round(alto * escala);
    contexto.setTransform(escala, 0, 0, escala, 0, 0);
    contexto.clearRect(0, 0, ancho, alto);

    const validas = series.map((serie) => ({
        ...serie,
        puntos: (serie.puntos || []).filter((punto) =>
            punto.x !== null && punto.x !== undefined
            && punto.y !== null && punto.y !== undefined
            && Number.isFinite(Number(punto.x)) && Number.isFinite(Number(punto.y))
        )
    })).filter((serie) => serie.puntos.length > 0);
    if (!validas.length) {
        contexto.fillStyle = colorCss("--muted", "#58677a");
        contexto.font = "12px sans-serif";
        contexto.fillText("No hay datos suficientes para graficar.", 12, 24);
        return;
    }

    const todos = validas.flatMap((serie) => serie.puntos);
    let minX = Math.min(...todos.map((punto) => Number(punto.x)));
    let maxX = Math.max(...todos.map((punto) => Number(punto.x)));
    let minY = Math.min(...todos.map((punto) => Number(punto.y)));
    let maxY = Math.max(...todos.map((punto) => Number(punto.y)));
    if (minX === maxX) { minX -= 1; maxX += 1; }
    if (minY === maxY) { minY -= 1; maxY += 1; }
    const margen = { left: 42, right: 12, top: 24, bottom: 28 };
    const plotW = ancho - margen.left - margen.right;
    const plotH = alto - margen.top - margen.bottom;
    const px = (x) => margen.left + (Number(x) - minX) / (maxX - minX) * plotW;
    const py = (y) => margen.top + (maxY - Number(y)) / (maxY - minY) * plotH;

    contexto.strokeStyle = colorCss("--line", "#e6d9dc");
    contexto.lineWidth = 1;
    for (let i = 0; i <= 4; i += 1) {
        const y = margen.top + plotH * i / 4;
        contexto.beginPath();
        contexto.moveTo(margen.left, y);
        contexto.lineTo(ancho - margen.right, y);
        contexto.stroke();
    }
    contexto.strokeStyle = colorCss("--muted", "#58677a");
    contexto.beginPath();
    contexto.moveTo(margen.left, margen.top);
    contexto.lineTo(margen.left, alto - margen.bottom);
    contexto.lineTo(ancho - margen.right, alto - margen.bottom);
    contexto.stroke();

    validas.forEach((serie, indice) => {
        contexto.strokeStyle = colores[indice % colores.length];
        contexto.lineWidth = 2;
        contexto.beginPath();
        serie.puntos.forEach((punto, puntoIndice) => {
            const x = px(punto.x);
            const y = py(punto.y);
            if (puntoIndice === 0) contexto.moveTo(x, y);
            else contexto.lineTo(x, y);
        });
        contexto.stroke();
        if (serie.puntos.length <= 20) {
            contexto.fillStyle = colores[indice % colores.length];
            serie.puntos.forEach((punto) => {
                contexto.beginPath();
                contexto.arc(px(punto.x), py(punto.y), 2.5, 0, Math.PI * 2);
                contexto.fill();
            });
        }
    });

    contexto.font = "10px sans-serif";
    contexto.textBaseline = "top";
    let leyendaX = margen.left;
    validas.forEach((serie, indice) => {
        contexto.fillStyle = colores[indice % colores.length];
        contexto.fillRect(leyendaX, 7, 9, 9);
        contexto.fillStyle = colorCss("--muted-strong", "#3f4e62");
        const texto = serie.nombre || `Serie ${indice + 1}`;
        contexto.fillText(texto, leyendaX + 13, 6);
        leyendaX += contexto.measureText(texto).width + 28;
    });
}

function construirSeriesGrafico(resultado) {
    let solucion = [];
    if (Array.isArray(resultado.curva)) {
        solucion.push({
            nombre: "Aproximación",
            puntos: resultado.curva.map((punto) => ({ x: punto.x, y: punto.y }))
        });
        if (resultado.curva.some((punto) => punto.referencia !== undefined)) {
            solucion.push({
                nombre: "Referencia",
                puntos: resultado.curva.map((punto) => ({ x: punto.x, y: punto.referencia }))
            });
        }
    } else if (Array.isArray(resultado.tabla_temporal)) {
        solucion = [{
            nombre: "Estado",
            puntos: resultado.tabla_temporal.map((fila) => ({
                x: fila.t,
                y: Array.isArray(fila.aproximacion) ? fila.aproximacion[0] : fila.aproximacion
            }))
        }];
        if (resultado.tabla_temporal.some((fila) => Array.isArray(fila.aproximacion) && fila.aproximacion.length > 1)) {
            solucion.push({
                nombre: "Velocidad",
                puntos: resultado.tabla_temporal.map((fila) => ({ x: fila.t, y: fila.aproximacion[1] }))
            });
        }
        if (resultado.tabla_temporal.some((fila) => Array.isArray(fila.referencia) && fila.referencia.length)) {
            solucion.push({
                nombre: "Referencia",
                puntos: resultado.tabla_temporal.map((fila) => ({
                    x: fila.t,
                    y: Array.isArray(fila.referencia) ? fila.referencia[0] : fila.referencia
                }))
            });
        }
    } else if (Array.isArray(resultado.solucion)) {
        solucion = [{
            nombre: "Componentes de la solución",
            puntos: resultado.solucion.map((valor, indice) => ({ x: indice + 1, y: valor }))
        }];
    }
    if (Array.isArray(resultado.solucion) && !Array.isArray(resultado.tabla_temporal)) {
        solucion.push({
            nombre: "Solución del sistema",
            puntos: resultado.solucion.map((valor, indice) => ({ x: indice + 1, y: valor }))
        });
    }
    if (Array.isArray(resultado.nodos)) {
        solucion.push({ nombre: "Nodos medidos", puntos: resultado.nodos });
    }
    if (Array.isArray(resultado.nodos_ocultos)) {
        solucion.push({ nombre: "Nodos ocultos (validación)", puntos: resultado.nodos_ocultos });
    }
    if (Array.isArray(resultado.curva) && resultado.curva.some((punto) => punto.referencia !== undefined)) {
        solucion.push({
            nombre: "Umbral",
            puntos: resultado.curva.map((punto) => ({ x: punto.x, y: punto.referencia }))
        });
    }
    if (Array.isArray(resultado.curva_referencia_libre)) {
        solucion.push({ nombre: "Referencia analítica sin fuerza", puntos: resultado.curva_referencia_libre });
    }
    const filasError = resultado.iteraciones
        || resultado.tabla_refinamiento
        || resultado.tabla_temporal
        || resultado.evaluaciones
        || [];
    const puntosError = filasError.map((fila, indice) => ({
        x: fila.iteracion ?? fila.subintervalos ?? fila.t ?? fila.x ?? indice + 1,
        y: fila.error_absoluto ?? fila.residual ?? null
    }));
    const diferencias = [];
    for (let i = 1; i < filasError.length; i += 1) {
        const anterior = filasError[i - 1].aproximacion;
        const actual = filasError[i].aproximacion;
        if (typeof anterior === "number" && typeof actual === "number") {
            diferencias.push({
                x: filasError[i].subintervalos ?? filasError[i].t ?? i + 1,
                y: Math.abs(actual - anterior)
            });
        } else if (Array.isArray(anterior) && Array.isArray(actual) && anterior.length === actual.length) {
            diferencias.push({
                x: filasError[i].t ?? i + 1,
                y: Math.sqrt(actual.reduce((suma, valor, indice) => suma + (valor - anterior[indice]) ** 2, 0))
            });
        }
    }
    const errores = [{ nombre: "Error / residual", puntos: puntosError }];
    if (diferencias.length) errores.push({ nombre: "Cambio entre pasos", puntos: diferencias });
    return { solucion, errores };
}

function datosTablaNumerica(resultado) {
    if (Array.isArray(resultado.iteraciones)) {
        if (resultado.iteraciones.length && Array.isArray(resultado.iteraciones[0].x)) {
            return {
                titulo: "Iteraciones del sistema lineal",
                filas: resultado.iteraciones,
                columnas: [
                    ["iteracion", "Iteración"], ["x", "Vector x"],
                    ["error_absoluto", "Error abs."], ["error_relativo", "Error rel."],
                    ["error_porcentual", "Error %"], ["residual", "Residual"]
                ]
            };
        }
        return {
            titulo: "Iteraciones de la raíz",
            filas: resultado.iteraciones,
            columnas: [
                ["iteracion", "Iteración"], ["aproximacion", "Aproximación"],
                ["error_absoluto", "Error abs."], ["error_relativo", "Error rel."],
                ["error_porcentual", "Error %"], ["residual", "Residual"]
            ]
        };
    }
    if (Array.isArray(resultado.tabla_refinamiento)) {
        return {
            titulo: "Tabla de refinamiento",
            filas: resultado.tabla_refinamiento,
            columnas: [
                ["subintervalos", "Subintervalos"], ["paso", "Paso"], ["nivel", "Nivel"],
                ["aproximacion", "Aproximación"], ["error_absoluto", "Error abs."],
                ["error_relativo", "Error rel."], ["error_porcentual", "Error %"]
            ]
        };
    }
    if (Array.isArray(resultado.tabla_temporal)) {
        return {
            titulo: "Tabla temporal",
            filas: resultado.tabla_temporal,
            columnas: [
                ["t", "t"], ["aproximacion", "Aproximación"], ["referencia", "Referencia"],
                ["error_absoluto", "Error abs."], ["error_relativo", "Error rel."],
                ["error_porcentual", "Error %"]
            ]
        };
    }
    return {
        titulo: "Evaluaciones de la señal",
        filas: resultado.evaluaciones || [],
        columnas: [
            ["x", "Punto"], ["aproximacion", "Aproximación"], ["referencia", "Referencia"],
            ["error_absoluto", "Error abs."], ["error_relativo", "Error rel."],
            ["error_porcentual", "Error %"]
        ]
    };
}

function renderizarResultadoNumerico(resultado, metodo) {
    const resumen = $("numerical-summary");
    const valorPrincipal = resultado.raiz_aproximada
        ?? resultado.integral_aproximada
        ?? resultado.valor_final;
    const referencia = resultado.valor_referencia_analitica
        ?? resultado.referencia_analitica
        ?? resultado.valor_referencia;
    const elementos = [
        ["Método", metodo.nombre],
        ["Magnitud calculada", resultado.cantidad || resultado.magnitud || "—"],
        ["Valor final", formatearValorTabla(valorPrincipal)],
        ["Referencia", formatearValorTabla(referencia)],
        ["Error absoluto", formatearError(resultado.error_absoluto_final)],
        ["Error relativo", formatearError(resultado.error_relativo_final)],
        ["Error %", formatearPorcentaje(resultado.error_porcentual_final)],
        ["Residual", formatearError(resultado.residual_final)],
        ["Estado numérico", resultado.tipo === "edo"
            ? "Integración paso a paso"
            : (resultado.tipo === "directo"
                ? "Solución directa"
                : (resultado.tipo === "interpolacion"
                    ? "Reconstrucción evaluada"
                    : (resultado.tipo === "integracion"
                        ? "Cuadratura completada"
                        : (resultado.convergio === undefined ? "No aplica" : (resultado.convergio ? "Convergió" : "No convergió")))))],
        ["Estabilidad numérica", resultado.estable === undefined ? "No evaluada" : (resultado.estable ? "Estable" : "Inestable")],
        ["Condicionamiento κ₂(A)", resultado.numero_condicion_kappa_2 === undefined ? "No aplica" : formatearDecimal(resultado.numero_condicion_kappa_2, 5)]
    ];
    resumen.replaceChildren();
    for (const [etiqueta, valor] of elementos) {
        if (valor === "—" && etiqueta !== "Valor final" && etiqueta !== "Referencia") continue;
        const chip = document.createElement("div");
        chip.className = "meta-chip";
        const nombre = document.createElement("span");
        nombre.textContent = etiqueta;
        const contenido = document.createElement("strong");
        contenido.textContent = valor;
        chip.append(nombre, contenido);
        resumen.appendChild(chip);
    }
    $("numerical-results").hidden = false;
    $("numerical-conclusion").textContent = resultado.conclusion_numerica || "El resultado depende del método, la discretización y los parámetros sintéticos indicados; revise el error y el estado de estabilidad por separado.";
    $("problem-conclusion").textContent = resultado.conclusion_problema || "Interpretación académica de un caso hipotético: no permite diagnosticar fallas reales ni inferir condiciones oficiales de Mi Teleférico.";
    const tabla = datosTablaNumerica(resultado);
    $("numerical-table-title").textContent = tabla.titulo;
    $("numerical-table-caption").textContent = resultado.mensaje || "Aproximaciones y métricas de error.";
    $("numerical-row-count").textContent = `${tabla.filas.length} filas`;
    const encabezado = document.createElement("tr");
    tabla.columnas.forEach(([, titulo]) => {
        const th = document.createElement("th");
        th.textContent = titulo;
        encabezado.appendChild(th);
    });
    $("numerical-table-head").replaceChildren(encabezado);
    const cuerpo = document.createDocumentFragment();
    for (const fila of tabla.filas) {
        const tr = document.createElement("tr");
        tabla.columnas.forEach(([clave]) => {
            const td = document.createElement("td");
            td.className = clave.includes("error") || clave === "aproximacion" || clave === "residual" ? "numeric" : "";
            const valor = fila[clave];
            td.textContent = clave === "error_porcentual" && valor !== null && valor !== undefined
                ? formatearPorcentaje(valor)
                : (clave === "error_absoluto" || clave === "error_relativo" || clave === "residual"
                    ? formatearError(valor)
                    : formatearValorTabla(valor));
            tr.appendChild(td);
        });
        cuerpo.appendChild(tr);
    }
    $("numerical-table-body").replaceChildren(cuerpo);
    const series = construirSeriesGrafico(resultado);
    dibujarGrafico("solution-chart", series.solucion);
    dibujarGrafico("error-chart", series.errores);
    actualizarAnimacion(resultado);
}

function dibujarCabinaTeleferico(contexto, opciones) {
    const {
        x,
        ancho,
        escala = 0.82,
        angulo = 0,
        desplazamientoX = 0,
        colorBase = "#bd7654"
    } = opciones;
    const inicioCable = { x: 18, y: 58 };
    const finCable = { x: ancho - 18, y: 28 };
    const fraccionCable = (x - inicioCable.x) / (finCable.x - inicioCable.x);
    const yCable = inicioCable.y + (finCable.y - inicioCable.y) * fraccionCable;
    const rectanguloRedondeado = (x, y, anchoRect, altoRect, radio) => {
        const r = Math.min(radio, anchoRect / 2, altoRect / 2);
        contexto.beginPath();
        contexto.moveTo(x + r, y);
        contexto.lineTo(x + anchoRect - r, y);
        contexto.quadraticCurveTo(x + anchoRect, y, x + anchoRect, y + r);
        contexto.lineTo(x + anchoRect, y + altoRect - r);
        contexto.quadraticCurveTo(x + anchoRect, y + altoRect, x + anchoRect - r, y + altoRect);
        contexto.lineTo(x + r, y + altoRect);
        contexto.quadraticCurveTo(x, y + altoRect, x, y + altoRect - r);
        contexto.lineTo(x, y + r);
        contexto.quadraticCurveTo(x, y, x + r, y);
        contexto.closePath();
    };

    contexto.save();
    contexto.lineCap = "round";
    contexto.strokeStyle = "#55534e";
    contexto.lineWidth = 5;
    contexto.beginPath();
    contexto.moveTo(inicioCable.x, inicioCable.y);
    contexto.lineTo(finCable.x, finCable.y);
    contexto.stroke();
    contexto.strokeStyle = "#b7b2a7";
    contexto.lineWidth = 1.5;
    contexto.beginPath();
    contexto.moveTo(inicioCable.x, inicioCable.y + 3);
    contexto.lineTo(finCable.x, finCable.y + 3);
    contexto.stroke();

    contexto.translate(x, yCable);
    contexto.fillStyle = "#d9d5ca";
    contexto.strokeStyle = "#494842";
    contexto.lineWidth = 2;
    [-12, 0, 12].forEach((rodilloX) => {
        contexto.beginPath();
        contexto.arc(rodilloX, 0, 7, 0, Math.PI * 2);
        contexto.fill();
        contexto.stroke();
        contexto.fillStyle = "#79766e";
        contexto.beginPath();
        contexto.arc(rodilloX, 0, 2.5, 0, Math.PI * 2);
        contexto.fill();
        contexto.fillStyle = "#d9d5ca";
    });

    contexto.fillStyle = "#6b6860";
    rectanguloRedondeado(-20, 7, 40, 6, 3);
    contexto.fill();
    contexto.strokeStyle = "#494842";
    contexto.lineWidth = 2.5;
    contexto.beginPath();
    contexto.moveTo(-8, 11);
    contexto.bezierCurveTo(-15, 23, -10, 31, -3, 37);
    contexto.bezierCurveTo(2, 41, desplazamientoX - 6, 39, desplazamientoX, 38);
    contexto.stroke();
    contexto.strokeStyle = "#b8b3a8";
    contexto.lineWidth = 1.4;
    contexto.beginPath();
    contexto.moveTo(-5, 13);
    contexto.bezierCurveTo(-11, 24, -6, 31, 1, 37);
    contexto.stroke();

    contexto.save();
    contexto.translate(desplazamientoX, 37);
    contexto.rotate(angulo);
    contexto.scale(escala, escala);

    const silueta = () => {
        contexto.beginPath();
        contexto.moveTo(-39, 5);
        contexto.quadraticCurveTo(-35, 0, -27, 0);
        contexto.lineTo(27, 0);
        contexto.quadraticCurveTo(35, 0, 39, 8);
        contexto.quadraticCurveTo(48, 25, 48, 56);
        contexto.quadraticCurveTo(48, 79, 35, 91);
        contexto.quadraticCurveTo(0, 99, -35, 91);
        contexto.quadraticCurveTo(-48, 79, -48, 56);
        contexto.quadraticCurveTo(-48, 25, -39, 5);
        contexto.closePath();
    };

    contexto.fillStyle = "#f4f2eb";
    contexto.strokeStyle = "#45443f";
    contexto.lineWidth = 3;
    silueta();
    contexto.fill();
    contexto.stroke();

    contexto.save();
    silueta();
    contexto.clip();
    contexto.fillStyle = colorBase;
    contexto.beginPath();
    contexto.moveTo(-48, 51);
    contexto.quadraticCurveTo(0, 55, 48, 51);
    contexto.lineTo(48, 82);
    contexto.quadraticCurveTo(39, 96, 0, 96);
    contexto.quadraticCurveTo(-39, 96, -48, 82);
    contexto.closePath();
    contexto.fill();
    contexto.fillStyle = "rgba(255,255,255,0.2)";
    contexto.fillRect(-39, 57, 78, 3);

    const gradienteVidrio = contexto.createLinearGradient(-34, 15, 34, 45);
    gradienteVidrio.addColorStop(0, "#75c9d0");
    gradienteVidrio.addColorStop(0.55, "#38a9bb");
    gradienteVidrio.addColorStop(1, "#147e91");
    [-33, 12].forEach((ventanaX) => {
        contexto.fillStyle = "#d8d6cf";
        rectanguloRedondeado(ventanaX - 2, 12, 29, 34, 4);
        contexto.fill();
        contexto.fillStyle = gradienteVidrio;
        rectanguloRedondeado(ventanaX, 14, 25, 30, 3);
        contexto.fill();
        contexto.fillStyle = "rgba(255,255,255,0.55)";
        contexto.beginPath();
        contexto.moveTo(ventanaX + 4, 40);
        contexto.lineTo(ventanaX + 20, 16);
        contexto.lineTo(ventanaX + 25, 16);
        contexto.lineTo(ventanaX + 9, 40);
        contexto.closePath();
        contexto.fill();
    });

    contexto.fillStyle = "#d8d6cf";
    contexto.beginPath();
    contexto.roundRect(-10, 12, 20, 34, 4);
    contexto.fill();
    contexto.fillStyle = gradienteVidrio;
    contexto.beginPath();
    contexto.roundRect(-8, 14, 16, 30, 3);
    contexto.fill();
    contexto.strokeStyle = "#5b5148";
    contexto.lineWidth = 1.5;
    contexto.beginPath();
    contexto.moveTo(-10, 49);
    contexto.lineTo(-10, 82);
    contexto.quadraticCurveTo(0, 86, 10, 82);
    contexto.lineTo(10, 49);
    contexto.stroke();

    contexto.fillStyle = "rgba(45,42,38,0.18)";
    contexto.fillRect(-37, 89, 74, 4);
    contexto.restore();

    contexto.fillStyle = "#e5e0d4";
    contexto.beginPath();
    contexto.moveTo(-37, 6);
    contexto.quadraticCurveTo(0, 1, 37, 6);
    contexto.lineTo(40, 11);
    contexto.quadraticCurveTo(0, 7, -40, 11);
    contexto.closePath();
    contexto.fill();
    contexto.strokeStyle = "#45443f";
    contexto.lineWidth = 2;
    contexto.beginPath();
    contexto.moveTo(-40, 10);
    contexto.quadraticCurveTo(0, 5, 40, 10);
    contexto.stroke();
    contexto.restore();
    contexto.restore();
}

function colorCabinaEscenario(escenario, inestable = false) {
    if (inestable) return "#c94d48";
    return {
        NORMAL: "#bd7654",
        ESTRES: "#d28b32",
        MAL_CONDICIONADO: "#8065a5"
    }[escenario] || "#bd7654";
}

function dibujarAnimacion(resultado, progreso) {
    const canvas = $("module-animation");
    const contexto = canvas.getContext("2d");
    const ancho = Math.max(300, canvas.clientWidth);
    const alto = Math.max(180, canvas.clientHeight);
    const escala = window.devicePixelRatio || 1;
    canvas.width = Math.round(ancho * escala);
    canvas.height = Math.round(alto * escala);
    contexto.setTransform(escala, 0, 0, escala, 0, 0);
    contexto.clearRect(0, 0, ancho, alto);
    contexto.fillStyle = "#f8fafc";
    contexto.fillRect(0, 0, ancho, alto);
    contexto.font = "12px sans-serif";
    contexto.fillStyle = "#475569";

    const modulo = Number(resultado.modulo);
    if (modulo === 1) {
        const distancia = Number(resultado.distancia_total || resultado.referencia_analitica?.distancia_frenado || 1);
        const parametros = resultado.parametros || {};
        const velocidadInicial = Number(parametros.velocidad_inicial || 0);
        const desaceleracion = Number(parametros.desaceleracion || 0);
        const amplitud = Number(parametros.amplitud_desaceleracion || 0);
        const reaccion = Number(parametros.tiempo_reaccion || 0);
        const tiempoFrenado = Number(resultado.referencia_analitica?.tiempo_parada || 0);
        const tiempoAnimado = progreso * (reaccion + tiempoFrenado);
        const tFrenadoAnimado = Math.max(0, tiempoAnimado - reaccion);
        const distanciaRecorrida = tiempoAnimado <= reaccion
            ? velocidadInicial * tiempoAnimado
            : velocidadInicial * reaccion
                + velocidadInicial * tFrenadoAnimado
                - 0.5 * desaceleracion * tFrenadoAnimado ** 2
                - desaceleracion * amplitud * (tFrenadoAnimado / 0.7 - Math.sin(0.7 * tFrenadoAnimado) / (0.7 ** 2));
        const recorrido = Math.max(0, Math.min(1, distanciaRecorrida / distancia));
        const puntoX = 58 + recorrido * (ancho - 116);
        const seguridad = Number(resultado.distancia_disponible || distancia);
        const yCableMarca = 58 - 30 * (puntoX - 18) / (ancho - 36);
        contexto.strokeStyle = "#dc2626";
        contexto.setLineDash([5, 5]);
        contexto.beginPath();
        contexto.moveTo(puntoX, yCableMarca);
        contexto.lineTo(puntoX, alto - 12);
        contexto.stroke();
        contexto.setLineDash([]);
        dibujarCabinaTeleferico(contexto, {
            x: puntoX,
            ancho,
            escala: 0.8,
            colorBase: colorCabinaEscenario(resultado.escenario, resultado.supera_distancia_segura)
        });
        contexto.fillStyle = "#334155";
        contexto.fillText(`${resultado.escenario} · cabina avanzando ${formatearDecimal(distanciaRecorrida, 2)} / ${formatearDecimal(distancia, 2)} m`, 24, 20);
        contexto.fillText(`Distancia segura: ${formatearDecimal(seguridad, 2)} m`, 24, 38);
        contexto.strokeStyle = "#dc2626";
        contexto.setLineDash([3, 4]);
        const marca = 58 + Math.min(1, seguridad / Math.max(seguridad, distancia)) * (ancho - 116);
        contexto.beginPath();
        contexto.moveTo(marca, 47);
        contexto.lineTo(marca, alto - 10);
        contexto.stroke();
        contexto.setLineDash([]);
        $("animation-status").textContent = resultado.supera_distancia_segura
            ? `Alerta ${resultado.escenario}: la distancia sintética supera la disponibilidad configurada.`
            : `${resultado.escenario}: la cabina frena dentro de la distancia hipotética disponible.`;
    } else if (modulo === 2) {
        const umbral = Number(resultado.umbral || 1);
        const curvaDeterioro = resultado.curva_deterioro || resultado.curva || [];
        const punto = curvaDeterioro[Math.min(curvaDeterioro.length - 1, Math.floor(progreso * (curvaDeterioro.length || 1)))];
        const deterioration = punto ? Number(punto.y) : 0;
        const fraccion = Math.max(0, Math.min(1, deterioration / umbral));
        contexto.fillStyle = "#e2e8f0";
        contexto.fillRect(34, 76, ancho - 68, 34);
        contexto.fillStyle = fraccion >= 1 ? "#dc2626" : "#0f766e";
        contexto.fillRect(34, 76, (ancho - 68) * fraccion, 34);
        contexto.fillStyle = "#334155";
        contexto.fillText(`${resultado.linea || "Línea hipotética"} · deterioro ${formatearDecimal(deterioration, 3)} / umbral ${formatearDecimal(umbral, 3)}`, 34, 36);
        const ventana = resultado.tiempo_mantenimiento || [0, 0];
        const tiempoUmbral = resultado.referencia_analitica?.tiempo_umbral
            ?? resultado.referencia_analitica_deterioro?.tiempo_umbral
            ?? 0;
        const x = (t) => 34 + Math.max(0, Math.min(1, t / (resultado.parametros?.horizonte || 1))) * (ancho - 68);
        contexto.fillStyle = "#f59e0b";
        contexto.fillRect(x(ventana[0]), 142, Math.max(3, x(ventana[1]) - x(ventana[0])), 18);
        contexto.fillStyle = "#dc2626";
        contexto.fillRect(x(tiempoUmbral) - 2, 132, 4, 38);
        contexto.fillStyle = "#334155";
        contexto.fillText("Ventana de mantenimiento (naranja) · cruce de umbral (rojo)", 34, 178);
        const fechaInicio = resultado.fecha_inicio_modelo;
        const fechaMes = (meses) => {
            if (!fechaInicio) return "fecha no definida";
            const fecha = new Date(`${fechaInicio}T00:00:00Z`);
            fecha.setUTCMonth(fecha.getUTCMonth() + Math.round(meses));
            return fecha.toISOString().slice(0, 10);
        };
        $("animation-status").textContent = `Fechas hipotéticas: mantenimiento ${fechaMes(ventana[0])}–${fechaMes(ventana[1])}; umbral estimado ${fechaMes(tiempoUmbral)}.`;
    } else if (modulo === 3) {
        const filas = resultado.tabla_temporal || resultado.curva || [];
        const fila = filas[Math.min(filas.length - 1, Math.floor(progreso * Math.max(0, filas.length - 1)))];
        const estado = fila?.aproximacion;
        const desplazamiento = Array.isArray(estado) ? Number(estado[0]) : Number(fila?.y || 0);
        const desplazamientoPx = Math.max(-62, Math.min(62, desplazamiento * 85));
        const angulo = Math.max(-0.55, Math.min(0.55, Math.atan2(desplazamiento, 1.4)));
        dibujarCabinaTeleferico(contexto, {
            x: ancho / 2,
            ancho,
            escala: 0.82,
            angulo,
            desplazamientoX: desplazamientoPx,
            colorBase: colorCabinaEscenario(resultado.escenario, resultado.estable === false)
        });
        contexto.fillStyle = "#334155";
        contexto.fillText(`${resultado.escenario} · balanceo x(t): ${formatearDecimal(desplazamiento, 4)} m · θ=${formatearDecimal(angulo * 180 / Math.PI, 1)}°`, 24, 20);
        contexto.fillText(`Amplitud máxima: ${formatearDecimal(resultado.maximo_balanceo, 4)} m · c=${resultado.parametros?.amortiguamiento} Ns/m`, 24, 38);
        $("animation-status").textContent = resultado.estable === false
            ? `MAL CONDICIONADO: inestabilidad numérica detectada; θ y posición proceden de la trayectoria calculada.`
            : (resultado.supera_umbral_balanceo ? `${resultado.escenario}: se supera el umbral únicamente didáctico configurado.` : `${resultado.escenario}: balanceo calculado; umbral comparativo sintético, no oficial.`);
    } else {
        const curva = resultado.curva || [];
        const padding = 28;
        const xValues = curva.map((punto) => Number(punto.x));
        const yValues = curva.map((punto) => Number(punto.y));
        const minX = Math.min(...xValues);
        const maxX = Math.max(...xValues);
        const minY = Math.min(...yValues);
        const maxY = Math.max(...yValues);
        const px = (valor) => padding + (Number(valor) - minX) / (maxX - minX || 1) * (ancho - 2 * padding);
        const py = (valor) => alto - padding - (Number(valor) - minY) / (maxY - minY || 1) * (alto - 2 * padding);
        contexto.strokeStyle = "#2563eb";
        contexto.lineWidth = 2;
        contexto.beginPath();
        curva.forEach((punto, indice) => {
            const x = px(punto.x);
            const y = py(punto.y);
            if (!indice) contexto.moveTo(x, y);
            else contexto.lineTo(x, y);
        });
        contexto.stroke();
        const barrido = padding + progreso * (ancho - 2 * padding);
        (resultado.nodos || []).forEach((punto) => {
            contexto.fillStyle = "#0f766e";
            contexto.beginPath();
            contexto.arc(px(punto.x), py(punto.y), 4, 0, Math.PI * 2);
            contexto.fill();
        });
        (resultado.nodos_ocultos || []).forEach((punto) => {
            contexto.strokeStyle = "#d97706";
            contexto.lineWidth = 2;
            contexto.beginPath();
            contexto.arc(px(punto.x), py(punto.y), 5, 0, Math.PI * 2);
            contexto.stroke();
        });
        contexto.strokeStyle = "#dc2626";
        contexto.setLineDash([5, 4]);
        contexto.beginPath();
        contexto.moveTo(barrido, 18);
        contexto.lineTo(barrido, alto - 18);
        contexto.stroke();
        contexto.setLineDash([]);
        contexto.fillStyle = "#334155";
        contexto.fillText(`Telemetría sintética · ${resultado.nodos?.length || 0} nodos medidos · ${resultado.nodos_ocultos?.length || 0} ocultos`, 24, 24);
        $("animation-status").textContent = "El trazo reconstruido avanza sobre el dominio; los nodos ocultos son puntos de validación sintéticos.";
    }
}

function actualizarAnimacion(resultado) {
    if (state.animationFrame !== null) cancelAnimationFrame(state.animationFrame);
    state.animationFrame = null;
    state.animationPlaying = false;
    state.animationProgress = 0;
    dibujarAnimacion(resultado, 0);
}

function avanzarAnimacion(timestamp) {
    if (!state.animationPlaying || !state.ultimoResultado) return;
    if (state.animationStart === null) state.animationStart = timestamp;
    const delta = timestamp - (state.animationLastTimestamp || timestamp);
    state.animationLastTimestamp = timestamp;
    state.animationProgress = Math.min(1, state.animationProgress + delta / 5000 * Number($("animation-speed").value));
    dibujarAnimacion(state.ultimoResultado, state.animationProgress);
    if (state.animationProgress >= 1) {
        state.animationPlaying = false;
        state.animationFrame = null;
        $("animation-status").textContent += " Animación finalizada.";
        return;
    }
    state.animationFrame = requestAnimationFrame(avanzarAnimacion);
}

function iniciarAnimacion() {
    if (!state.ultimoResultado || state.animationPlaying) return;
    if (state.animationProgress >= 1) state.animationProgress = 0;
    state.animationPlaying = true;
    state.animationStart = null;
    state.animationLastTimestamp = null;
    state.animationFrame = requestAnimationFrame(avanzarAnimacion);
}

async function compararMetodosNumericos() {
    const modulo = Number($("numerical-module").value);
    const escenario = $("numerical-scenario").value;
    seleccionarEscenarioPersistente(escenario);
    const parametros = leerParametrosNumericos();
    const boton = $("compare-numerical");
    boton.disabled = true;
    $("numerical-hint").textContent = "Ejecutando comparación reproducible de métodos…";
    try {
        const resultados = [];
        for (const metodo of listaMetodosModulo(modulo)) {
            const resultado = await apiRequest(`/api/modulos/${modulo}/ejecutar`, {
                method: "POST",
                body: { escenario, metodo: metodo.id, parametros }
            });
            resultados.push({ metodo, resultado });
        }
        state.comparaciones = resultados;
        const seleccionado = resultados.find((item) => item.metodo.id === $("numerical-method").value) || resultados[0];
        state.ultimoResultado = seleccionado.resultado;
        state.ultimoMetodo = { id: seleccionado.metodo.id, nombre: seleccionado.metodo.nombre, tipo: "numerico" };
        state.ultimoEscenario = obtenerEscenarioSeleccionado();
        state.ultimaConfiguracion = parametros;
        state.ultimaEjecucion = new Date().toISOString();
        renderizarResultadoNumerico(seleccionado.resultado, seleccionado.metodo);
        renderizarTablaComparacion(resultados);
        actualizarAcciones();
        $("numerical-hint").textContent = `Comparación completada: ${resultados.length} métodos para ${escenario}.`;
    } catch (error) {
        mostrarToast(error.message, "error");
        $("numerical-hint").textContent = "La comparación no pudo completarse.";
    } finally {
        boton.disabled = false;
    }
}

function renderizarTablaComparacion(resultados) {
    const columnas = ["Método", "Valor/solución", "Error absoluto", "Residual", "Convergencia", "Estabilidad", "κ₂(A)"];
    const head = document.createElement("tr");
    columnas.forEach((titulo) => {
        const th = document.createElement("th");
        th.textContent = titulo;
        head.appendChild(th);
    });
    $("comparison-head").replaceChildren(head);
    const cuerpo = document.createDocumentFragment();
    resultados.forEach(({ metodo, resultado }) => {
        const principal = resultado.raiz_aproximada ?? resultado.integral_aproximada ?? resultado.valor_final ?? resultado.solucion;
        const fila = document.createElement("tr");
        [
            metodo.nombre,
            formatearValorTabla(principal),
            formatearError(resultado.error_absoluto_final),
            formatearError(resultado.residual_final),
            resultado.tipo === "edo"
                ? "Integración paso a paso"
                : (resultado.tipo === "directo"
                    ? "Solución directa"
                    : (resultado.tipo === "interpolacion"
                        ? "Reconstrucción evaluada"
                        : (resultado.tipo === "integracion"
                            ? "Cuadratura completada"
                            : (resultado.convergio === undefined ? "No aplica" : (resultado.convergio ? "Convergió" : "No convergió"))))),
            resultado.estable === undefined ? "No evaluada" : (resultado.estable ? "Estable" : "Inestable"),
            resultado.numero_condicion_kappa_2 === undefined ? "—" : formatearDecimal(resultado.numero_condicion_kappa_2, 5)
        ].forEach((valor) => fila.appendChild(crearCelda(String(valor))));
        cuerpo.appendChild(fila);
    });
    $("comparison-body").replaceChildren(cuerpo);
    $("comparison-count").textContent = `${resultados.length} métodos`;
    $("comparison-results").hidden = false;
    if (Number($("numerical-module").value) === 4) {
        const primera = resultados[0]?.resultado;
        const curvas = resultados.map(({ metodo, resultado }) => ({
            nombre: metodo.nombre,
            puntos: (resultado.curva || []).map((punto) => ({ x: punto.x, y: punto.y }))
        }));
        if (primera?.curva?.some((punto) => punto.referencia !== undefined)) {
            curvas.push({
                nombre: "Señal sintética de referencia",
                puntos: primera.curva.map((punto) => ({ x: punto.x, y: punto.referencia }))
            });
        }
        if (primera?.nodos) curvas.push({ nombre: "Nodos medidos", puntos: primera.nodos });
        if (primera?.nodos_ocultos) {
            curvas.push({ nombre: "Nodos ocultos de validación", puntos: primera.nodos_ocultos });
        }
        dibujarGrafico("solution-chart", curvas);
        const errores = resultados.map(({ metodo, resultado }) => ({
            nombre: metodo.nombre,
            puntos: (resultado.evaluaciones || []).map((fila) => ({
                x: fila.x,
                y: fila.error_absoluto
            }))
        }));
        dibujarGrafico("error-chart", errores);
    }
}

async function ejecutarMetodoNumerico() {
    const modulo = Number($("numerical-module").value);
    const escenario = $("numerical-scenario").value;
    seleccionarEscenarioPersistente(escenario);
    const idMetodo = $("numerical-method").value;
    const metodo = METODOS_NUMERICOS[idMetodo];
    if (!metodo) {
        mostrarToast("Selecciona un método numérico válido.", "error");
        return;
    }

    const boton = $("run-numerical");
    boton.disabled = true;
    $("numerical-hint").textContent = `Ejecutando ${metodo.nombre}…`;
    try {
        const parametros = leerParametrosNumericos();
        const resultado = await apiRequest(`/api/modulos/${modulo}/ejecutar`, {
            method: "POST",
            body: { escenario, metodo: idMetodo, parametros }
        });
        state.ultimoResultado = resultado;
        state.ultimoMetodo = { id: idMetodo, nombre: metodo.nombre, iterativo: false, tipo: "numerico" };
        state.ultimoEscenario = obtenerEscenarioSeleccionado();
        state.ultimaConfiguracion = parametros;
        state.ultimaEjecucion = new Date().toISOString();
        renderizarResultadoNumerico(resultado, metodo);
        actualizarAcciones();
        $("numerical-hint").textContent = `Análisis ${metodo.nombre} completado para ${escenario}.`;
        mostrarToast(`${metodo.nombre} ejecutado correctamente.`, "success");
    } catch (error) {
        $("numerical-results").hidden = true;
        state.ultimoResultado = null;
        state.ultimoMetodo = null;
        actualizarAcciones();
        $("numerical-hint").textContent = "No se pudo completar el análisis.";
        mostrarToast(error.message, "error");
    } finally {
        boton.disabled = false;
    }
}

function seleccionarMetodo(id, opciones = {}) {
    const { limpiar = true } = opciones;
    const metodo = METODOS[id];
    if (!metodo) {
        return;
    }

    const cambio = state.metodoId !== id;
    state.metodoId = id;

    document.querySelectorAll(".method-option").forEach((boton) => {
        const activo = boton.dataset.method === id;
        boton.classList.toggle("method-option-active", activo);
        boton.setAttribute("aria-pressed", String(activo));
    });

    $("iterative-controls").hidden = !metodo.iterativo;

    if (cambio && limpiar) {
        limpiarResultado();
    }
}

function limpiarResultado() {
    state.ultimoResultado = null;
    state.ultimoMetodo = null;
    state.ultimoEscenario = null;
    state.ultimaEjecucion = null;
    state.ultimaConfiguracion = null;
    state.comparaciones = [];
    state.animationPlaying = false;
    if (state.animationFrame !== null) cancelAnimationFrame(state.animationFrame);
    state.animationFrame = null;

    $("empty-result").hidden = false;
    $("result-content").hidden = true;
    $("result-subtitle").textContent = "Aún no hay una ejecución";
    $("result-status").textContent = "Sin ejecutar";
    $("result-status").className = "result-badge result-badge-idle";
    $("iteration-count").textContent = "0 iteraciones";
    $("lu-factors").hidden = true;
    $("lu-grid").replaceChildren();
    $("numerical-results").hidden = true;
    $("comparison-results").hidden = true;

    actualizarAcciones();
}

function actualizarAcciones() {
    const sinEscenario = !state.escenarioSeleccionado;
    const botonEjecutar = $("run-method");
    const botonGuardar = $("save-simulation");
    const botonGuardarNumerico = $("save-numerical-simulation");

    botonEjecutar.disabled = sinEscenario || state.ejecutando;
    botonGuardar.disabled = sinEscenario || !state.ultimoResultado || state.guardando;

    if (botonGuardarNumerico) {
        const hayResultadoNumerico = Boolean(
            state.ultimoResultado
            && state.ultimoMetodo
            && state.ultimoMetodo.tipo === "numerico"
        );
        botonGuardarNumerico.disabled = !hayResultadoNumerico || state.guardando;
    }

    if (!state.ejecutando && !state.ultimoResultado) {
        $("run-hint").textContent = sinEscenario
            ? "No hay escenarios disponibles. Verifica la conexión con la API."
            : "Ejecuta un método para habilitar el guardado.";
    }
}

function alternarCarga(boton, cargando, textoCarga) {
    const span = boton.querySelector("span");
    if (!span) {
        return;
    }

    if (cargando) {
        boton.dataset.textoOriginal = span.textContent;
        span.textContent = textoCarga;
        boton.classList.add("is-loading");
        boton.disabled = true;
    } else {
        if (boton.dataset.textoOriginal) {
            span.textContent = boton.dataset.textoOriginal;
        }
        boton.classList.remove("is-loading");
        boton.disabled = false;
    }
}

async function ejecutarMetodo() {
    const metodo = METODOS[state.metodoId];
    const escenario = obtenerEscenarioSeleccionado();

    if (!escenario) {
        mostrarToast("Selecciona un escenario antes de ejecutar.", "error");
        $("scenario-select").focus();
        return;
    }

    const payload = {
        A: state.referencia.A,
        b: state.referencia.b
    };

    if (metodo.iterativo) {
        const tolerancia = Number($("tolerance").value);
        const maxIteraciones = Number($("max-iterations").value);

        if (!Number.isFinite(tolerancia) || tolerancia <= 0) {
            mostrarToast("La tolerancia debe ser un número mayor que cero.", "error");
            $("tolerance").focus();
            return;
        }

        if (!Number.isInteger(maxIteraciones) || maxIteraciones < 1) {
            mostrarToast("El máximo de iteraciones debe ser un entero positivo.", "error");
            $("max-iterations").focus();
            return;
        }

        payload.tolerancia = tolerancia;
        payload.max_iteraciones = maxIteraciones;
    }

    state.ejecutando = true;
    alternarCarga($("run-method"), true, "Ejecutando");
    $("run-hint").textContent = `Ejecutando ${metodo.nombre}…`;
    actualizarAcciones();

    try {
        const resultado = await apiRequest(`/api/metodos/${metodo.endpoint}`, {
            method: "POST",
            body: payload
        });

        state.ultimoResultado = resultado;
        state.ultimoMetodo = metodo;
        state.ultimoEscenario = escenario;
        state.ultimaEjecucion = new Date().toISOString();

        $("numerical-results").hidden = true;
        renderizarResultado(resultado, metodo);
        mostrarToast(
            `${metodo.nombre}: ${resultado.convergio ? "convergió" : "no convergió"} en ${resultado.iteraciones_totales} iteraciones.`,
            resultado.convergio ? "success" : "info"
        );
        $("run-hint").textContent = `${metodo.nombre} ejecutado sobre ${escenario.nombre}. Listo para guardar.`;
    } catch (error) {
        limpiarResultado();
        mostrarToast(error.message, "error");
        $("run-hint").textContent = "No se pudo completar la ejecución.";
    } finally {
        state.ejecutando = false;
        alternarCarga($("run-method"), false);
        actualizarAcciones();
    }
}

function htmlMatriz(titulo, matriz) {
    if (!Array.isArray(matriz) || !matriz.length) {
        return "";
    }

    const n = matriz.length;
    const celdas = matriz.flatMap((fila) => {
        return fila.map((valor) => {
            return `<span class="mini-cell">${formatearDecimal(valor)}</span>`;
        });
    }).join("");

    return `
        <div class="lu-matrix">
            <h5>${titulo}</h5>
            <div class="mini-matrix" style="grid-template-columns: repeat(${n}, minmax(44px, auto));">
                ${celdas}
            </div>
        </div>
    `;
}

function renderizarResultado(resultado, metodo) {
    $("empty-result").hidden = true;
    $("result-content").hidden = false;

    const estado = $("result-status");
    const convergio = Boolean(resultado.convergio);
    estado.textContent = metodo.iterativo
        ? (convergio ? "Convergido" : "No convergido")
        : "Completado";
    estado.className = `result-badge result-badge-${convergio ? "success" : "warning"}`;

    const escenario = state.ultimoEscenario;
    $("result-subtitle").textContent = `${metodo.nombre} · ${resultado.iteraciones_totales} iteraciones${escenario ? ` · ${escenario.nombre}` : ""}`;

    const solucion = Array.isArray(resultado.solucion) ? resultado.solucion : [];
    $("solution-grid").innerHTML = solucion.map((valor, indice) => {
        return `
            <article class="solution-card">
                <span>x<sub>${indice + 1}</sub></span>
                <strong title="${formatearDecimal(valor)}">${formatearDecimal(valor)}</strong>
            </article>
        `;
    }).join("");

    const chips = [
        ["Método", metodo.nombre],
        ["Iteraciones", String(resultado.iteraciones_totales)],
        ["Residual final", formatearError(resultado.residual_final)],
        ["Error relativo final", formatearError(resultado.error_relativo_final)],
        ["Convergencia", convergio ? "Sí" : "No"]
    ];

    $("result-meta").innerHTML = chips.map(([etiqueta, valor]) => {
        return `<div class="meta-chip"><span>${etiqueta}</span><strong>${valor}</strong></div>`;
    }).join("");

    renderizarTablaIteraciones(resultado);
    renderizarFactoresLu(resultado);
    actualizarAcciones();
}

function renderizarTablaIteraciones(resultado) {
    const iteraciones = Array.isArray(resultado.iteraciones) ? resultado.iteraciones : [];
    const dimension = iteraciones[0] && Array.isArray(iteraciones[0].x)
        ? iteraciones[0].x.length
        : (Array.isArray(resultado.solucion) ? resultado.solucion.length : 0);

    const encabezadosX = Array.from({ length: dimension }, (_, indice) => {
        return `<th>x<sub>${indice + 1}</sub></th>`;
    }).join("");

    $("iterations-head").innerHTML = `
        <tr>
            <th>Iter.</th>
            ${encabezadosX}
            <th>Error abs.</th>
            <th>Error rel.</th>
            <th>Error %</th>
            <th>Residual</th>
        </tr>
    `;

    if (!iteraciones.length) {
        $("iterations-body").innerHTML = `
            <tr>
                <td colspan="${dimension + 5}">No hay iteraciones para mostrar.</td>
            </tr>
        `;
    } else {
        $("iterations-body").innerHTML = iteraciones.map((iteracion) => {
            const x = Array.isArray(iteracion.x) ? iteracion.x : [];
            const celdasX = Array.from({ length: dimension }, (_, indice) => {
                return `<td class="numeric">${formatearDecimal(x[indice] ?? 0)}</td>`;
            }).join("");

            return `
                <tr>
                    <td class="mono">${iteracion.iteracion ?? "—"}</td>
                    ${celdasX}
                    <td class="numeric">${formatearError(iteracion.error_absoluto)}</td>
                    <td class="numeric">${formatearError(iteracion.error_relativo)}</td>
                    <td class="numeric">${formatearPorcentaje(iteracion.error_porcentual)}</td>
                    <td class="numeric">${formatearError(iteracion.residual)}</td>
                </tr>
            `;
        }).join("");
    }

    $("iteration-count").textContent = `${iteraciones.length} ${iteraciones.length === 1 ? "paso" : "pasos"}`;
}

function renderizarFactoresLu(resultado) {
    const bloque = $("lu-factors");
    const grid = $("lu-grid");

    if (!resultado.L && !resultado.U && !resultado.P) {
        bloque.hidden = true;
        grid.replaceChildren();
        return;
    }

    bloque.hidden = false;
    grid.innerHTML = [
        htmlMatriz("L", resultado.L),
        htmlMatriz("U", resultado.U),
        htmlMatriz("P", resultado.P)
    ].join("");
}

async function guardarSimulacion() {
    const resultado = state.ultimoResultado;
    const metodo = state.ultimoMetodo;
    const escenario = state.ultimoEscenario || obtenerEscenarioSeleccionado();

    if (!resultado || !metodo || !escenario) {
        mostrarToast("Ejecuta un método antes de guardar la simulación.", "error");
        return;
    }

    const esNumerico = metodo.tipo === "numerico";
    const botonGuardarActivo = esNumerico && $("save-numerical-simulation")
        ? $("save-numerical-simulation")
        : $("save-simulation");

    state.guardando = true;
    alternarCarga(botonGuardarActivo, true, "Guardando");
    actualizarAcciones();

    const ahora = new Date().toISOString();
    const sufijo = Date.now().toString(36).toUpperCase();
    const codigo = `SIM-${metodo.id.replace(/-/g, "").toUpperCase()}-${sufijo}`;
    const tolerancia = metodo.iterativo ? Number($("tolerance").value) : null;
    const maxIteraciones = metodo.iterativo ? Number($("max-iterations").value) : null;

    const payload = {
        escenario_id: escenario.id,
        codigo,
        nombre: `${metodo.nombre} · ${escenario.nombre}`,
        descripcion: esNumerico
            ? `Ejecución de ${metodo.nombre} para ${escenario.caso_nombre || "módulo"} (${escenario.codigo}).`
            : `Ejecución de ${metodo.nombre} sobre el sistema de referencia (${escenario.caso_codigo || "caso"}).`,
        metodo: metodo.nombre,
        version_modelo: esNumerico ? "metodos-semana-2" : "lineal-v1",
        numero_iteraciones: Math.max(1, Number(resultado.iteraciones_totales) || 1),
        nivel_confianza: 0.95,
        parametros: {
            metodo: metodo.id,
            metodo_nombre: metodo.nombre,
            escenario: {
                id: escenario.id,
                codigo: escenario.codigo,
                nombre: escenario.nombre,
                caso_codigo: escenario.caso_codigo,
                caso_nombre: escenario.caso_nombre
            },
            sistema: esNumerico ? null : state.referencia,
            tolerancia,
            max_iteraciones: maxIteraciones,
            solucion: resultado.solucion,
            iteraciones_totales: resultado.iteraciones_totales,
            residual_final: resultado.residual_final,
            error_relativo_final: resultado.error_relativo_final,
            convergio: resultado.convergio,
            modulo: esNumerico ? Number($("numerical-module").value) : null,
            escenario_numerico: esNumerico ? $("numerical-scenario").value : null,
            parametros_modelo: esNumerico ? (state.ultimaConfiguracion || leerParametrosNumericos()) : null,
            resultado_numerico: esNumerico ? resultado : null
        },
        estado: resultado.convergio ? "completada" : "fallida",
        fecha_inicio: state.ultimaEjecucion || ahora,
        fecha_fin: ahora
    };

    try {
        const guardada = await apiRequest("/api/simulaciones", {
            method: "POST",
            body: payload
        });

        state.simulaciones.unshift(guardada);
        renderizarSimulaciones();
        renderizarEstadisticas();
        mostrarToast(`Simulación ${guardada.codigo} guardada correctamente.`, "success");
        $("run-hint").textContent = `Simulación ${guardada.codigo} persistida en SQLite.`;
        $("numerical-hint").textContent = `Simulación ${guardada.codigo} persistida en SQLite.`;
    } catch (error) {
        mostrarToast(error.message, "error");
    } finally {
        state.guardando = false;
        alternarCarga(botonGuardarActivo, false);
        actualizarAcciones();
    }
}

function crearCelda(texto, clase = "") {
    const celda = document.createElement("td");
    if (clase) {
        celda.className = clase;
    }
    celda.textContent = texto;
    return celda;
}

function renderizarSimulaciones() {
    const tbody = $("simulations-body");
    const empty = $("simulations-empty");
    const tableScroll = document.querySelector(".saved-panel .table-scroll");

    tbody.replaceChildren();

    const textoBusqueda = ($("history-search")?.value || "").trim().toLocaleLowerCase();
    const filtroModulo = $("history-module")?.value || "";
    const filtroEscenario = $("history-scenario")?.value || "";
    const simulacionesFiltradas = state.simulaciones.filter((simulacion) => {
        const parametros = simulacion.parametros || {};
        const modulo = parametros.modulo == null ? "" : String(parametros.modulo);
        const escenario = parametros.escenario_numerico || simulacion.escenario?.codigo || "";
        const busqueda = [
            simulacion.codigo, simulacion.nombre, simulacion.metodo,
            simulacion.caso_estudio?.nombre, simulacion.caso_estudio?.codigo,
            simulacion.escenario?.nombre, escenario, modulo
        ].join(" ").toLocaleLowerCase();
        return (!filtroModulo || modulo === filtroModulo)
            && (!filtroEscenario || escenario === filtroEscenario)
            && (!textoBusqueda || busqueda.includes(textoBusqueda));
    });

    if (!simulacionesFiltradas.length) {
        empty.hidden = false;
        empty.querySelector("h4").textContent = state.simulaciones.length ? "Sin coincidencias" : "Sin simulaciones";
        empty.querySelector("p").textContent = state.simulaciones.length
            ? "Ajusta los filtros de búsqueda."
            : "Las ejecuciones sintéticas que guardes aparecerán aquí.";
        if (tableScroll) {
            tableScroll.hidden = true;
        }
        return;
    }

    empty.hidden = true;
    if (tableScroll) {
        tableScroll.hidden = false;
    }

    for (const simulacion of simulacionesFiltradas) {
        const fila = document.createElement("tr");

        fila.appendChild(crearCelda(`#${simulacion.id}`, "mono"));
        fila.appendChild(crearCelda(simulacion.codigo || "—", "mono"));

        const escenario = simulacion.escenario || {};
        const caso = simulacion.caso_estudio || {};
        const nombreEscenario = escenario.nombre || "—";
        const referenciaCaso = caso.codigo ? ` · ${caso.codigo}` : "";
        fila.appendChild(crearCelda(`${nombreEscenario}${referenciaCaso}`));

        fila.appendChild(crearCelda(simulacion.metodo || "—"));

        const celdaEstado = document.createElement("td");
        const badge = document.createElement("span");
        const estado = String(simulacion.estado || "pendiente");
        badge.className = `state-badge state-${estado}`;
        badge.textContent = ESTADOS[estado] || capitalizar(estado);
        celdaEstado.appendChild(badge);
        fila.appendChild(celdaEstado);

        fila.appendChild(crearCelda(String(simulacion.numero_iteraciones ?? "—"), "numeric"));
        fila.appendChild(crearCelda(formatearFecha(simulacion.created_at)));

        const celdaAccion = document.createElement("td");
        const boton = document.createElement("button");
        boton.type = "button";
        const ver = document.createElement("button");
        ver.type = "button";
        ver.className = "link-btn";
        ver.dataset.simId = String(simulacion.id);
        ver.dataset.action = "view";
        ver.textContent = "Ver";
        const relanzar = document.createElement("button");
        relanzar.type = "button";
        relanzar.className = "link-btn";
        relanzar.dataset.simId = String(simulacion.id);
        relanzar.dataset.action = "relaunch";
        relanzar.textContent = "Relanzar";
        relanzar.disabled = !simulacion.parametros?.resultado_numerico;
        celdaAccion.append(ver, relanzar);
        fila.appendChild(celdaAccion);

        tbody.appendChild(fila);
    }
}

async function recargarSimulaciones() {
    try {
        state.simulaciones = await apiRequest("/api/simulaciones");
        renderizarSimulaciones();
        renderizarEstadisticas();
        mostrarToast("Simulaciones actualizadas.", "success");
    } catch (error) {
        mostrarToast(error.message, "error");
    }
}

function abrirModal() {
    $("modal").hidden = false;
    document.body.style.overflow = "hidden";
}

function cerrarModal() {
    $("modal").hidden = true;
    document.body.style.overflow = "";
}

function crearItemDetalle(etiqueta, valor) {
    const item = document.createElement("div");
    item.className = "detail-item";

    const label = document.createElement("span");
    label.textContent = etiqueta;

    const contenido = document.createElement("strong");
    contenido.textContent = valor || "—";

    item.appendChild(label);
    item.appendChild(contenido);
    return item;
}

function renderizarDetalleSimulacion(simulacion) {
    const body = $("modal-body");
    const grid = document.createElement("div");
    grid.className = "detail-grid";

    const escenario = simulacion.escenario || {};
    const caso = simulacion.caso_estudio || {};

    const items = [
        ["Código", simulacion.codigo],
        ["Nombre", simulacion.nombre],
        ["Método", simulacion.metodo],
        ["Estado", ESTADOS[simulacion.estado] || capitalizar(simulacion.estado)],
        ["Escenario", escenario.nombre],
        ["Caso", [caso.codigo, caso.nombre].filter(Boolean).join(" · ")],
        ["Iteraciones", String(simulacion.numero_iteraciones ?? "—")],
        ["Creada", formatearFecha(simulacion.created_at)]
    ];

    for (const [etiqueta, valor] of items) {
        grid.appendChild(crearItemDetalle(etiqueta, valor));
    }

    const eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = "Parámetros de ejecución";

    const pre = document.createElement("pre");
    pre.className = "detail-json";
    pre.textContent = JSON.stringify(simulacion.parametros || {}, null, 2);

    const acciones = document.createElement("div");
    acciones.className = "detail-actions";
    const relanzar = document.createElement("button");
    relanzar.type = "button";
    relanzar.className = "btn btn-primary";
    relanzar.dataset.relaunchId = String(simulacion.id);
    relanzar.textContent = "Relanzar y verificar coincidencia";
    relanzar.disabled = !simulacion.parametros?.resultado_numerico;
    acciones.appendChild(relanzar);
    body.replaceChildren(grid, eyebrow, pre, acciones);
}

async function relanzarSimulacion(id) {
    $("numerical-hint").textContent = `Relanzando la simulación #${id} desde la configuración guardada…`;
    try {
        const replay = await apiRequest(`/api/simulaciones/${id}/relanzar`, {
            method: "POST",
            body: { tolerancia: 1e-10 }
        });
        const simulacion = state.simulaciones.find((item) => item.id === id);
        const guardados = simulacion?.parametros || {};
        const modulo = Number(guardados.modulo);
        const metodo = METODOS_NUMERICOS[guardados.metodo] || { nombre: guardados.metodo };
        $("numerical-module").value = String(modulo);
        $("numerical-scenario").value = guardados.escenario_numerico;
        actualizarPresetNumerico();
        if (guardados.parametros_modelo) {
            renderizarCamposParametros(guardados.parametros_modelo);
        }
        $("numerical-method").value = guardados.metodo;
        state.moduloSeleccionado = modulo;
        state.ultimoResultado = replay.resultado_recalculado;
        state.ultimoMetodo = { id: guardados.metodo, nombre: metodo.nombre, tipo: "numerico" };
        state.ultimoEscenario = state.escenarios.find((item) =>
            item.codigo === guardados.escenario_numerico
            && item.caso_codigo === MODULOS[modulo]?.caso
        ) || null;
        state.escenarioSeleccionado = state.ultimoEscenario;
        if (state.ultimoEscenario) $("scenario-select").value = String(state.ultimoEscenario.id);
        state.ultimaConfiguracion = guardados.parametros_modelo;
        state.ultimaEjecucion = new Date().toISOString();
        renderizarResultadoNumerico(replay.resultado_recalculado, metodo);
        actualizarInterfazModulo(modulo);
        actualizarAcciones();
        $("numerical-hint").textContent = replay.coincide
            ? `Relanzamiento verificado: diferencia máxima ${formatearError(replay.diferencia_maxima)} ≤ tolerancia ${formatearError(replay.tolerancia)}.`
            : `El relanzamiento difiere del resultado persistido (error máximo ${formatearError(replay.diferencia_maxima)}).`;
        mostrarToast(
            replay.coincide ? "El resultado relanzado coincide dentro de la tolerancia." : "El resultado relanzado no coincide dentro de la tolerancia.",
            replay.coincide ? "success" : "error"
        );
        cerrarModal();
        desplazarseASeccion("numerical-workspace");
    } catch (error) {
        mostrarToast(error.message, "error");
    }
}

async function verSimulacion(id) {
    abrirModal();
    $("modal-title").textContent = `Simulación #${id}`;
    $("modal-body").textContent = "Cargando detalle…";

    try {
        const simulacion = await apiRequest(`/api/simulaciones/${id}`);
        $("modal-title").textContent = `Simulación ${simulacion.codigo || `#${id}`}`;
        renderizarDetalleSimulacion(simulacion);
    } catch (error) {
        $("modal-body").textContent = error.message;
    }
}

function sistemaValido(sistema) {
    return Boolean(
        sistema
        && Array.isArray(sistema.A)
        && sistema.A.length
        && sistema.A.every((fila) => Array.isArray(fila))
        && Array.isArray(sistema.b)
        && sistema.b.length === sistema.A.length
    );
}

async function cargarTodo(opciones = {}) {
    const { silencioso = false } = opciones;
    actualizarEstadoApi("waiting");

    try {
        const [salud, casos, escenarios, simulaciones, escenariosModulo] = await Promise.all([
            apiRequest("/api/salud"),
            apiRequest("/api/casos-estudio"),
            apiRequest("/api/escenarios"),
            apiRequest("/api/simulaciones"),
            apiRequest("/api/escenarios-modulo")
        ]);

        if (sistemaValido(salud && salud.sistema_referencia)) {
            state.referencia = clonar(salud.sistema_referencia);
        }

        state.casos = Array.isArray(casos) ? casos : [];
        state.escenarios = Array.isArray(escenarios) ? escenarios : [];
        state.simulaciones = Array.isArray(simulaciones) ? simulaciones : [];
        state.escenariosModulo = escenariosModulo;
        state.datosCargados = true;

        actualizarEstadoApi("online");
        renderizarEstadisticas();
        renderizarEscenarios();
        actualizarPresetNumerico();
        renderizarMatrizReferencia();
        renderizarSimulaciones();
        actualizarAcciones();

        if (!silencioso) {
            mostrarToast("Datos actualizados correctamente.", "success");
        }
    } catch (error) {
        state.datosCargados = false;
        state.escenariosModulo = null;
        actualizarEstadoApi("offline");
        renderizarEstadisticas();
        renderizarEscenarios();
        actualizarPresetNumerico();
        renderizarMatrizReferencia();
        renderizarSimulaciones();
        actualizarAcciones();

        if (!silencioso) {
            mostrarToast(error.message, "error");
        }
    }
}

function actualizarInterfazModulo(numero) {
    const modulo = MODULOS[Number(numero)] || null;
    const titulo = $("page-title");
    const pageEyebrow = $("page-eyebrow");
    const eyebrow = $("modulo-eyebrow");
    const heading = $("modulo-title");

    if (titulo) {
        titulo.textContent = modulo ? modulo.nombre : "Riesgo y simulación";
    }
    if (pageEyebrow) {
        pageEyebrow.textContent = modulo ? `MÓDULO ${numero}` : "Panel de control";
    }
    if (eyebrow) {
        eyebrow.textContent = modulo ? `MÓDULO ${numero}` : "Módulos de estudio";
    }
    if (heading) {
        heading.textContent = modulo ? modulo.nombre : "Sistemas lineales";
    }

}

function seleccionarModulo(numero, opciones = {}) {
    const { caso = null, desplazar = false, enfocar = false } = opciones;
    const modulo = MODULOS[Number(numero)];
    if (!modulo) {
        return;
    }

    state.moduloSeleccionado = Number(numero);
    $("numerical-module").value = String(numero);
    actualizarPresetNumerico();
    actualizarInterfazModulo(numero);

    const codigoCaso = caso || modulo.caso;
    if (codigoCaso && codigoCaso !== state.casoFiltro) {
        state.casoFiltro = codigoCaso;
        if (state.ultimoResultado) {
            limpiarResultado();
        }
        renderizarEscenarios();
    }
    seleccionarEscenarioPersistente($("numerical-scenario").value);

    if (desplazar) {
        desplazarseASeccion("modulo-2");
    } else {
        actualizarNavegacionActiva();
    }

    if (enfocar) {
        const selector = $("scenario-select");
        if (selector && !selector.disabled) {
            selector.focus({ preventScroll: true });
        }
    }
}

function abrirSolucionadorSistemas(tarjeta) {
    if (!tarjeta) {
        return;
    }

    seleccionarModulo(tarjeta.dataset.module, {
        caso: tarjeta.dataset.caso,
        desplazar: true,
        enfocar: true
    });
}

function seccionActivaPorScroll() {
    const secciones = ["dashboard", "modulos", "modulo-2", "numerical-workspace", "simulaciones"];
    const lineaActiva = Math.min(180, Math.max(100, window.innerHeight * 0.22));
    let activa = "dashboard";

    for (const id of secciones) {
        const seccion = $(id);
        if (seccion && seccion.getBoundingClientRect().top <= lineaActiva) {
            activa = id;
        }
    }
    return activa;
}

function actualizarNavegacionActiva(seccionForzada = null) {
    const seccionActiva = seccionForzada || navScrollTarget || seccionActivaPorScroll();
    const enlaces = Array.from(document.querySelectorAll(".nav-link"));
    const subenlaces = Array.from(document.querySelectorAll(".nav-sublink"));
    const grupoActivo = seccionActiva === "modulos" || seccionActiva === "modulo-2";
    const subenlaceActivo = seccionActiva === "modulo-2" && state.moduloSeleccionado
        ? subenlaces.find(
            (enlace) => Number(enlace.dataset.module) === Number(state.moduloSeleccionado)
        ) || null
        : null;

    enlaces.forEach((enlace) => {
        const activa = enlace.id === "modules-toggle"
            ? grupoActivo
            : enlace.dataset.navSection === seccionActiva;
        enlace.classList.toggle("nav-link-active", activa);
        if (activa) {
            enlace.setAttribute("aria-current", "page");
        } else {
            enlace.removeAttribute("aria-current");
        }
    });

    subenlaces.forEach((enlace) => {
        const activa = enlace === subenlaceActivo;
        enlace.classList.toggle("nav-sublink-active", activa);
        if (activa) {
            enlace.setAttribute("aria-current", "page");
        } else {
            enlace.removeAttribute("aria-current");
        }
    });
}

function desplazarseASeccion(id) {
    const seccion = $(id);
    if (!seccion) {
        return;
    }
    navScrollTarget = id;
    actualizarNavegacionActiva(id);
    seccion.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start"
    });
    if (window.location.hash !== `#${id}`) {
        history.replaceState(null, "", `#${id}`);
    }
    window.clearTimeout(navScrollTimer);
    navScrollTimer = window.setTimeout(() => {
        navScrollTarget = null;
        actualizarNavegacionActiva();
    }, 1800);
}

function cancelarDesplazamientoProgramado() {
    if (!navScrollTarget) {
        return;
    }
    navScrollTarget = null;
    window.clearTimeout(navScrollTimer);
    actualizarNavegacionActiva();
}

function actualizarNavegacionAlDesplazarse() {
    if (navScrollFrame !== null) {
        return;
    }
    navScrollFrame = window.requestAnimationFrame(() => {
        navScrollFrame = null;
        actualizarNavegacionActiva();
    });
}

function enlazarEventos() {
    document.querySelectorAll(".method-option").forEach((boton) => {
        boton.addEventListener("click", () => {
            seleccionarMetodo(boton.dataset.method);
        });
    });

    document.querySelectorAll(".nav-link[data-nav-section]").forEach((enlace) => {
        enlace.addEventListener("click", (evento) => {
            evento.preventDefault();
            const destino = enlace.dataset.navSection;
            if (destino !== "numerical-workspace") {
                state.moduloSeleccionado = null;
                actualizarInterfazModulo(null);
            }
            desplazarseASeccion(destino);
        });
    });

    const modulesToggle = $("modules-toggle");
    const modulesSubnav = $("modules-subnav");
    if (modulesToggle && modulesSubnav) {
        modulesToggle.addEventListener("click", () => {
            const expandido = modulesToggle.getAttribute("aria-expanded") === "true";
            modulesToggle.setAttribute("aria-expanded", String(!expandido));
            modulesSubnav.hidden = expandido;
        });
    }

    document.querySelectorAll(".nav-sublink").forEach((enlace) => {
        enlace.addEventListener("click", (evento) => {
            evento.preventDefault();
            seleccionarModulo(enlace.dataset.module, {
                caso: enlace.dataset.caso,
                desplazar: true,
                enfocar: true
            });
            if (window.location.hash !== "#modulo-2") {
                history.replaceState(null, "", "#modulo-2");
            }
        });
    });

    window.addEventListener("hashchange", () => {
        actualizarNavegacionActiva();
    });
    window.addEventListener("scroll", actualizarNavegacionAlDesplazarse, { passive: true });
    window.addEventListener("resize", actualizarNavegacionAlDesplazarse);
    window.addEventListener("wheel", cancelarDesplazamientoProgramado, { passive: true });
    window.addEventListener("touchstart", cancelarDesplazamientoProgramado, { passive: true });
    window.addEventListener("pointerdown", cancelarDesplazamientoProgramado, { passive: true });
    window.addEventListener("scrollend", () => {
        if (navScrollTarget) {
            navScrollTarget = null;
            window.clearTimeout(navScrollTimer);
            actualizarNavegacionActiva();
        }
    });

    $("scenario-select").addEventListener("change", (evento) => {
        state.escenarioSeleccionado = Number(evento.target.value) || null;
        actualizarDetalleEscenario();
        actualizarAcciones();
    });

    $("numerical-module").addEventListener("change", (evento) => {
        seleccionarModulo(evento.target.value);
        limpiarResultado();
    });
    $("numerical-scenario").addEventListener("change", () => {
        seleccionarEscenarioPersistente($("numerical-scenario").value);
        actualizarPresetNumerico();
        limpiarResultado();
    });
    $("numerical-method").addEventListener("change", () => {
        limpiarResultado();
    });
    $("run-numerical").addEventListener("click", ejecutarMetodoNumerico);
    $("compare-numerical").addEventListener("click", compararMetodosNumericos);
    $("animation-play").addEventListener("click", iniciarAnimacion);
    $("animation-pause").addEventListener("click", () => {
        state.animationPlaying = false;
        if (state.animationFrame !== null) cancelAnimationFrame(state.animationFrame);
        state.animationFrame = null;
    });
    $("animation-restart").addEventListener("click", () => {
        state.animationProgress = 0;
        if (state.ultimoResultado) dibujarAnimacion(state.ultimoResultado, 0);
    });

    ["tolerance", "max-iterations"].forEach((id) => {
        $(id).addEventListener("change", () => {
            if (state.ultimoResultado) {
                limpiarResultado();
                mostrarToast("Configuración modificada. Vuelve a ejecutar el método.", "info");
            }
        });
    });

    $("run-method").addEventListener("click", ejecutarMetodo);
    $("save-simulation").addEventListener("click", guardarSimulacion);
    const botonGuardarNumerico = $("save-numerical-simulation");
    if (botonGuardarNumerico) {
        botonGuardarNumerico.addEventListener("click", guardarSimulacion);
    }
    $("refresh-all").addEventListener("click", () => cargarTodo());
    $("refresh-simulations").addEventListener("click", recargarSimulaciones);

    $("simulations-body").addEventListener("click", (evento) => {
        const boton = evento.target.closest("button[data-sim-id]");
        if (boton) {
            if (boton.dataset.action === "relaunch") {
                void relanzarSimulacion(Number(boton.dataset.simId));
            } else {
                verSimulacion(Number(boton.dataset.simId));
            }
        }
    });
    $("modal-body").addEventListener("click", (evento) => {
        const boton = evento.target.closest("button[data-relaunch-id]");
        if (boton) void relanzarSimulacion(Number(boton.dataset.relaunchId));
    });
    ["history-search", "history-module", "history-scenario"].forEach((id) => {
        $(id).addEventListener("input", renderizarSimulaciones);
        $(id).addEventListener("change", renderizarSimulaciones);
    });

    document.querySelectorAll(".module-card[data-module]").forEach((tarjeta) => {
        tarjeta.addEventListener("click", () => abrirSolucionadorSistemas(tarjeta));
        tarjeta.addEventListener("keydown", (evento) => {
            if (evento.key === "Enter" || evento.key === " ") {
                evento.preventDefault();
                abrirSolucionadorSistemas(tarjeta);
            }
        });
    });

    $("modal-close").addEventListener("click", cerrarModal);
    $("modal").addEventListener("click", (evento) => {
        if (evento.target === $("modal")) {
            cerrarModal();
        }
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && !$("modal").hidden) {
            cerrarModal();
        }
    });
}

function iniciar() {
    iniciarPantallaBienvenida();
    state.referencia = clonar(REFERENCIA_DEFAULT);
    enlazarEventos();
    actualizarNavegacionActiva();
    seleccionarMetodo("exacta", { limpiar: false });
    renderizarMatrizReferencia();
    renderizarEstadisticas();
    renderizarSimulaciones();
    actualizarEstadoApi("waiting");
    actualizarAcciones();
    void cargarTodo({ silencioso: true });
}

function cerrarPantallaBienvenida() {
    const pantalla = $("welcome-screen");
    if (!pantalla || pantalla.hidden || pantalla.classList.contains("is-closing")) {
        return;
    }

    window.clearInterval(welcomeInterval);
    window.clearTimeout(welcomeTimeout);
    pantalla.classList.add("is-closing");
    window.setTimeout(() => {
        pantalla.hidden = true;
        document.body.classList.remove("welcome-open");
        $("page-title").focus();
    }, 340);
}

function iniciarPantallaBienvenida() {
    const pantalla = $("welcome-screen");
    if (!pantalla) {
        return;
    }

    document.body.classList.add("welcome-open");
    const cuenta = $("welcome-countdown");
    const barra = $("welcome-progress");
    const barraContenedor = $("welcome-progress-track");
    let transcurridos = 0;

    const botonEntrada = $("welcome-enter");
    botonEntrada.addEventListener("click", cerrarPantallaBienvenida, { once: true });
    pantalla.addEventListener("keydown", (evento) => {
        if (evento.key === "Tab") {
            evento.preventDefault();
            botonEntrada.focus();
        }
    });
    botonEntrada.focus();
    welcomeInterval = window.setInterval(() => {
        transcurridos = Math.min(10, transcurridos + 1);
        cuenta.textContent = String(10 - transcurridos);
        barra.style.width = `${transcurridos * 10}%`;
        barraContenedor.setAttribute("aria-valuenow", String(transcurridos));
    }, 1000);
    welcomeTimeout = window.setTimeout(cerrarPantallaBienvenida, 10000);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar, { once: true });
} else {
    iniciar();
}
