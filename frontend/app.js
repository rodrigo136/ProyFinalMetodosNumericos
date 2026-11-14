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
    if (window.location.port === "5000") {
        return "";
    }
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    const host = window.location.hostname || "127.0.0.1";
    return `${protocol}//${host}:5000`;
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

const state = {
    casos: [],
    escenarios: [],
    simulaciones: [],
    referencia: { A: REFERENCIA_DEFAULT.A, b: REFERENCIA_DEFAULT.b },
    metodoId: "exacta",
    escenarioSeleccionado: null,
    casoFiltro: null,
    moduloSeleccionado: null,
    ultimoResultado: null,
    ultimoMetodo: null,
    ultimoEscenario: null,
    ultimaEjecucion: null,
    datosCargados: false,
    ejecutando: false,
    guardando: false
};

let toastTimer = null;

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

    $("empty-result").hidden = false;
    $("result-content").hidden = true;
    $("result-subtitle").textContent = "Aún no hay una ejecución";
    $("result-status").textContent = "Sin ejecutar";
    $("result-status").className = "result-badge result-badge-idle";
    $("iteration-count").textContent = "0 iteraciones";
    $("lu-factors").hidden = true;
    $("lu-grid").replaceChildren();

    actualizarAcciones();
}

function actualizarAcciones() {
    const sinEscenario = !state.escenarioSeleccionado;
    const botonEjecutar = $("run-method");
    const botonGuardar = $("save-simulation");

    botonEjecutar.disabled = sinEscenario || state.ejecutando;
    botonGuardar.disabled = sinEscenario || !state.ultimoResultado || state.guardando;

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
    const escenario = obtenerEscenarioSeleccionado();

    if (!resultado || !metodo || !escenario) {
        mostrarToast("Ejecuta un método antes de guardar la simulación.", "error");
        return;
    }

    state.guardando = true;
    alternarCarga($("save-simulation"), true, "Guardando");
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
        descripcion: `Ejecución de ${metodo.nombre} sobre el sistema de referencia (${escenario.caso_codigo || "caso"}).`,
        metodo: metodo.nombre,
        version_modelo: "lineal-v1",
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
            sistema: state.referencia,
            tolerancia,
            max_iteraciones: maxIteraciones,
            solucion: resultado.solucion,
            iteraciones_totales: resultado.iteraciones_totales,
            residual_final: resultado.residual_final,
            error_relativo_final: resultado.error_relativo_final,
            convergio: resultado.convergio
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
    } catch (error) {
        mostrarToast(error.message, "error");
    } finally {
        state.guardando = false;
        alternarCarga($("save-simulation"), false);
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

    if (!state.simulaciones.length) {
        empty.hidden = false;
        if (tableScroll) {
            tableScroll.hidden = true;
        }
        return;
    }

    empty.hidden = true;
    if (tableScroll) {
        tableScroll.hidden = false;
    }

    for (const simulacion of state.simulaciones) {
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
        boton.className = "link-btn";
        boton.dataset.simId = String(simulacion.id);
        boton.textContent = "Ver";
        celdaAccion.appendChild(boton);
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

    body.replaceChildren(grid, eyebrow, pre);
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
        const [salud, casos, escenarios, simulaciones] = await Promise.all([
            apiRequest("/api/salud"),
            apiRequest("/api/casos-estudio"),
            apiRequest("/api/escenarios"),
            apiRequest("/api/simulaciones")
        ]);

        if (sistemaValido(salud && salud.sistema_referencia)) {
            state.referencia = clonar(salud.sistema_referencia);
        }

        state.casos = Array.isArray(casos) ? casos : [];
        state.escenarios = Array.isArray(escenarios) ? escenarios : [];
        state.simulaciones = Array.isArray(simulaciones) ? simulaciones : [];
        state.datosCargados = true;

        actualizarEstadoApi("online");
        renderizarEstadisticas();
        renderizarEscenarios();
        renderizarMatrizReferencia();
        renderizarSimulaciones();
        actualizarAcciones();

        if (!silencioso) {
            mostrarToast("Datos actualizados correctamente.", "success");
        }
    } catch (error) {
        state.datosCargados = false;
        actualizarEstadoApi("offline");
        renderizarEstadisticas();
        renderizarEscenarios();
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

    document.querySelectorAll(".nav-sublink").forEach((enlace) => {
        const activo = Boolean(modulo) && Number(enlace.dataset.module) === Number(numero);
        enlace.classList.toggle("nav-sublink-active", activo);
        if (activo) {
            enlace.setAttribute("aria-current", "page");
        } else {
            enlace.removeAttribute("aria-current");
        }
    });

    const toggle = $("modules-toggle");
    if (toggle) {
        toggle.classList.toggle("nav-link-active", Boolean(modulo));
    }
}

function seleccionarModulo(numero, opciones = {}) {
    const { caso = null, desplazar = false, enfocar = false } = opciones;
    const modulo = MODULOS[Number(numero)];
    if (!modulo) {
        return;
    }

    state.moduloSeleccionado = Number(numero);
    actualizarInterfazModulo(numero);
    actualizarNavegacionActiva("#modulo-2");

    const codigoCaso = caso || modulo.caso;
    if (codigoCaso && codigoCaso !== state.casoFiltro) {
        state.casoFiltro = codigoCaso;
        if (state.ultimoResultado) {
            limpiarResultado();
        }
        renderizarEscenarios();
    }

    if (desplazar) {
        const seccion = $("modulo-2");
        if (seccion) {
            seccion.scrollIntoView({ behavior: "smooth", block: "start" });
        }
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

function actualizarNavegacionActiva(hash = window.location.hash) {
    const enlaces = Array.from(document.querySelectorAll(".nav-link"));
    const subenlaces = Array.from(document.querySelectorAll(".nav-sublink"));
    if (!enlaces.length) {
        return;
    }

    const destino = hash && hash.startsWith("#") ? hash : "#dashboard";
    let activo = null;

    if (state.moduloSeleccionado && (destino === "#modulo-2" || destino === "#modulos")) {
        activo = subenlaces.find(
            (enlace) => Number(enlace.dataset.module) === Number(state.moduloSeleccionado)
        ) || null;
    }

    const esSubenlace = Boolean(activo);
    if (!activo) {
        activo = enlaces.find((enlace) => enlace.getAttribute("href") === destino)
            || enlaces.find((enlace) => enlace.getAttribute("href") === "#dashboard")
            || enlaces[0];
    }

    enlaces.forEach((enlace) => {
        const esActivo = enlace === activo || (esSubenlace && enlace.id === "modules-toggle");
        enlace.classList.toggle("nav-link-active", esActivo);
        if (esActivo) {
            enlace.setAttribute("aria-current", "page");
        } else {
            enlace.removeAttribute("aria-current");
        }
    });

    subenlaces.forEach((enlace) => {
        const esActivo = enlace === activo;
        enlace.classList.toggle("nav-sublink-active", esActivo);
        if (esActivo) {
            enlace.setAttribute("aria-current", "page");
        } else {
            enlace.removeAttribute("aria-current");
        }
    });
}

function enlazarEventos() {
    document.querySelectorAll(".method-option").forEach((boton) => {
        boton.addEventListener("click", () => {
            seleccionarMetodo(boton.dataset.method);
        });
    });

    document.querySelectorAll(".nav-link[href]").forEach((enlace) => {
        enlace.addEventListener("click", () => {
            if (enlace.getAttribute("href") !== "#modulo-2") {
                state.moduloSeleccionado = null;
                actualizarInterfazModulo(null);
            }
            actualizarNavegacionActiva(enlace.getAttribute("href"));
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

    $("scenario-select").addEventListener("change", (evento) => {
        state.escenarioSeleccionado = Number(evento.target.value) || null;
        actualizarDetalleEscenario();
        actualizarAcciones();
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
    $("refresh-all").addEventListener("click", () => cargarTodo());
    $("refresh-simulations").addEventListener("click", recargarSimulaciones);

    $("simulations-body").addEventListener("click", (evento) => {
        const boton = evento.target.closest("button[data-sim-id]");
        if (boton) {
            verSimulacion(Number(boton.dataset.simId));
        }
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
    state.referencia = clonar(REFERENCIA_DEFAULT);
    enlazarEventos();
    actualizarNavegacionActiva();
    seleccionarMetodo("exacta", { limpiar: false });
    renderizarMatrizReferencia();
    renderizarEstadisticas();
    renderizarSimulaciones();
    actualizarEstadoApi("waiting");
    actualizarAcciones();
    cargarTodo({ silencioso: true });
}

document.addEventListener("DOMContentLoaded", iniciar);
