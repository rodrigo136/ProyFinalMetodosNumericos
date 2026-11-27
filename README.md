# SIMTELE-RISK

**Sistema Integrado de Métodos Numéricos para Transporte por Cable**

Proyecto final de Métodos Numéricos con backend Flask, cálculo en Python/NumPy y persistencia SQLite. Estudia cuatro problemas matemáticos inspirados de forma didáctica en el transporte por cable de La Paz.

> **Naturaleza de los datos:** SIMTELE-RISK es un sistema académico y educativo. Todos los datos, señales, ráfagas, líneas, fallas, umbrales, calendarios y resultados son sintéticos o hipotéticos; no representan fallas reales, mediciones ni datos oficiales de Mi Teleférico. Los modelos no sustituyen análisis de ingeniería ni procedimientos operativos.

- Repositorio: [rodrigo136/ProyFinalMetodosNumericos](https://github.com/rodrigo136/ProyFinalMetodosNumericos)
- Aplicación desplegada: [proyfinalmetodosnumericos.onrender.com](https://proyfinalmetodosnumericos.onrender.com)
- Estado de la API: [`/api/salud`](https://proyfinalmetodosnumericos.onrender.com/api/salud)

## Descripción del proyecto

El proyecto utiliza como contexto hipotético la seguridad, el mantenimiento y la calidad de mediciones de una red de transporte por cable. Los escenarios no describen condiciones de operación de la red real.

El sistema incluye cuatro módulos obligatorios:

1. **Detención de emergencia:** estudio de escenarios de detención automática o manual de cabinas ante condiciones de emergencia.
2. **Deterioro mecánico:** análisis del desgaste y de las acciones de mantenimiento preventivo o correctivo.
3. **Oscilaciones por viento:** simulación del efecto del viento sobre cabinas y estructuras.
4. **Reconstrucción de sensores:** recuperación de señales a partir de lecturas incompletas o afectadas por ruido.

Cada módulo se registra como un caso de estudio y puede asociarse con escenarios operativos. La interfaz permite seleccionar el caso, ejecutar un método y consultar los resultados disponibles.

## Arquitectura tecnológica

| Capa | Tecnología | Responsabilidad |
|---|---|---|
| Backend | Python y Flask | API HTTP, validación de solicitudes, ejecución de métodos y coordinación de persistencia. |
| Persistencia | SQLite | Casos, escenarios, simulaciones, ejecuciones y resultados. |
| Frontend | HTML5, CSS3 y JavaScript nativo | Interfaz web sin framework de frontend; consume la API Flask. |
| Cálculo numérico | Python y NumPy | Métodos para EDO, integración, raíces, interpolación y sistemas lineales; análisis de error y condicionamiento. |

### Modelo de datos

El esquema definido en [`database/schema.sql`](database/schema.sql) contiene las seis tablas obligatorias:

| Tabla | Propósito |
|---|---|
| `caso_estudio` | Información de los cuatro módulos/casos de estudio. |
| `escenario` | Escenarios asociados a cada caso, con parámetros y atributos de riesgo. |
| `simulacion` | Datos y estado de cada simulación guardada. |
| `ejecucion_metodo` | Ejecuciones de métodos numéricos asociadas a una simulación. |
| `iteracion_resultado` | Valores y métricas producidos en cada iteración. |
| `resultado_resumen` | Resúmenes estadísticos de los resultados de una ejecución. |

Al iniciar la API, el backend crea el esquema si todavía no existe y carga los casos y escenarios iniciales. Las relaciones conectan casos con escenarios, escenarios con simulaciones y simulaciones con ejecuciones, iteraciones y resúmenes. Por defecto, la base activa está en `backend/simtele_risk.db`; se puede cambiar su ubicación mediante `SIMTELE_RISK_DB`.

La API guarda la configuración y los resultados de la simulación en formato JSON dentro de `simulacion.parametros`. El esquema define además las tablas normalizadas de ejecuciones, iteraciones y resúmenes; no se debe asumir que cada guardado inserta automáticamente registros en las seis tablas. El detalle se recupera mediante la API y el relanzamiento recalcula usando la configuración guardada.

## Cobertura matemática

### Análisis de errores

El proyecto incluye utilidades para calcular y analizar:

- **Error absoluto:** \(E_a = |x_{\text{real}} - x_{\text{aprox}}|\).
- **Error relativo:** \(E_r = E_a / |x_{\text{real}}|\), solo cuando el valor real no es cero; si es cero, se informa como no disponible, sin dividir por cero. El error porcentual es \(100 E_r\).
- **Error entre iteraciones:** diferencia absoluta y relativa entre aproximaciones consecutivas, usada para evaluar la convergencia.
- **Residual:** \(r = b - Ax\); se usa su norma para medir qué tan bien la aproximación satisface el sistema.
- **Número de condición:** \(\kappa(A) = \|A\|\,\|A^{-1}\|\), indicador de la sensibilidad del sistema ante perturbaciones. El módulo de errores admite normas seleccionables y devuelve infinito cuando detecta una matriz singular.

La implementación está en [`backend/errores.py`](backend/errores.py) y [`backend/sistemas_lineales.py`](backend/sistemas_lineales.py). Los resultados de los métodos incluyen errores de iteración y residual; el número de condición está disponible como utilidad matemática.

### Sistemas lineales

Los métodos se aplican al sistema \(Ax=b\). El sistema de referencia predeterminado es de orden \(4 \times 4\):

\[
A =
\begin{bmatrix}
10 & 2 & 1 & 0 \\
2 & 10 & 1 & 1 \\
1 & 1 & 8 & 2 \\
0 & 1 & 2 & 9
\end{bmatrix},
\qquad
b =
\begin{bmatrix}
13 \\ 24 \\ 31 \\ 28
\end{bmatrix}.
\]

Se implementan cinco métodos:

- **Solución exacta:** eliminación gaussiana con pivoteo parcial.
- **Factorización LU:** factorización con pivoteo parcial y sustitución.
- **Jacobi:** método iterativo con aproximación inicial, tolerancia y máximo de iteraciones.
- **Gauss-Seidel:** método iterativo sucesivo con los mismos controles.
- **Gradiente conjugado:** método iterativo para matrices simétricas definidas positivas.

Los métodos iterativos reportan convergencia, número de iteraciones, errores y residual. La convergencia depende de las propiedades del sistema y de los parámetros elegidos; no está garantizada para cualquier matriz.

### Métodos numéricos de las Semanas 2 y 3

Los módulos `backend/raices.py`, `backend/integracion.py`,
`backend/edo.py` y `backend/interpolacion.py` implementan los métodos. Estos reportan sus
iteraciones o tablas, errores disponibles, referencias analíticas cuando
corresponden y estados de convergencia, estabilidad y condicionamiento como
propiedades diferenciadas. Las referencias iguales a
cero dejan el error relativo como no disponible, y se rechazan entradas o
resultados no finitos.

Los cuatro módulos incluyen presets editables para `NORMAL`, `ESTRES` (presentado como ESTRÉS) y `MAL_CONDICIONADO`. El API acepta los códigos sin tilde. Los métodos y modelos son:

- **Módulo 1 — Detención de emergencia:** \(x'=v,\;v'=-a(t)\), con RK2/Heun,
  RK4, trapecio compuesto, Simpson 1/3 compuesto, Romberg y raíces por
  bisección, Newton-Raphson y secante para \(v(t)=0\). La referencia constante
  es \(v_0=6\ \mathrm{m/s}\), \(a=1.5\ \mathrm{m/s^2}\), con
  \(t_{\mathrm{paro}}=4\ \mathrm{s}\) y \(d_{\mathrm{frenado}}=12\ \mathrm{m}\).
  Para desaceleración variable se usa
  \(a(t)=a_0[1+\gamma\sin(0.7t)]\). La distancia total incluye la distancia
  recorrida durante el tiempo de reacción.
- **Módulo 2 — Deterioro mecánico y mantenimiento:** raíces de
  \(D(t)-D_{\mathrm{umbral}}\), con
  \(D(t)=D_0+\alpha t+\beta t^2\), más Jacobi, Gauss-Seidel, LU y gradiente
  conjugado sobre un sistema SPD de orden \(4\times4\), con \(\kappa_2(A)\).
  Un calendario ilustrativo contrasta mantenimiento hipotético, disponibilidad
  y cruce de umbral. La fecha inicial del preset es 2026-01-01; los intervalos
  de mantenimiento y tiempos de cruce se expresan en meses relativos a ella.
- **Módulo 3 — Oscilaciones por viento:** sistema masa-resorte-amortiguador
  forzado con
  \(m=500\ \mathrm{kg}\), \(k=1200\ \mathrm{N/m}\), \(c=40\ \mathrm{Ns/m}\)
  en los presets normal y estrés y fuerza \(F(t)=F_0\sin(\omega t)\); integra
  \(x(t)^2\) con trapecio, Simpson 1/3 y Romberg. Se incluye la referencia
  analítica subamortiguada para vibración libre (\(F(t)=0\)).
  \(\int x(t)^2\,dt\) es un indicador integral didáctico, no energía expresada
  en joules. Se incluye un caso con malla crítica.
- **Módulo 4 — Reconstrucción de señales:** interpolación de Lagrange, Newton
  por diferencias divididas y splines cúbicos naturales sobre
  \(y(t)=\sin(t)\), \(y(t)=e^{-t}\) y la función de Runge. Se ocultan nodos
  antes de interpolar para medir el error en datos no usados en el ajuste; el
  ruido es determinista. Runge y la sensibilidad asociada a la representación
  polinómica/Vandermonde son ejemplos matemáticos, no fallas de sensores reales.

### Matriz de validación reproducible 3×4

Las siguientes referencias se obtienen con los presets predeterminados de
`backend/escenarios_modulo.py`, sin enviar `parametros` adicionales a
`POST /api/modulos/<modulo>/ejecutar`. Se selecciona RK4 en los módulos 1 y 3,
bisección para la raíz del módulo 2 (y LU para \(\kappa_2\)), y Lagrange en el
módulo 4. Las cifras se redondean para presentación; el backend conserva más
precisión. Bisección usa tolerancia predeterminada \(10^{-10}\).

| Escenario | 1. Detención (RK4) | 2. Deterioro (bisección y LU) | 3. Oscilaciones (RK4/Romberg) | 4. Señales (Lagrange) |
|---|---|---|---|---|
| **NORMAL** | Entrada: \(v_0=6\), \(a_0=1.5\), \(\gamma=0\), reacción \(0.8\) s, distancia disponible \(15\) m, 80 pasos. Referencia: \(t=4.000\) s; frenado \(12.000\) m; total \(16.800\) m, supera el límite didáctico. | Entrada: \(D_0=0.1,\alpha=0.03,\beta=0.002,D_u=1\), horizonte 24 meses; línea Roja (hipotética), mantenimiento \([10,11]\) meses desde 2026-01-01. Referencia: cruce \(t=15.000\) meses; \(\kappa_2(A)=2.071124\). | Entrada: \(m=500,c=40,k=1200,F_0=1200,\omega=1,T=12\) s, 240 pasos, \(x_0=0.1,v_0=0\). Referencia: \(x_{\max}\approx2.542017\) m; \(\int x^2dt\approx21.84127\ \mathrm{m^2s}\); estable según el indicador implementado y supera el umbral didáctico de 0.35 m. | Entrada: \(\sin(t)\), 9 nodos totales, 3 ocultos, \([0,\pi]\), ruido 0. Referencia: \(E_2\) del error en nodos ocultos \(\approx0.00137475\). |
| **ESTRÉS** | Entrada: \(v_0=8,a_0=2,\gamma=0.15\), reacción \(1.2\) s, distancia disponible \(20\) m, 120 pasos. Referencia: \(t\approx3.610590\) s; frenado \(\approx14.65379\) m; total \(\approx24.25379\) m, supera el límite didáctico. | Entrada: \(D_0=0.1,\alpha=0.07,\beta=0.006,D_u=1\), horizonte 16 meses; línea Amarilla (hipotética), mantenimiento \([5,7]\) meses desde 2026-01-01. Referencia: cruce \(t\approx7.732350\) meses; \(\kappa_2(A)=2.071124\). | Entrada: \(m=500,c=40,k=1200,F_0=4500,\omega=1.52,T=12\) s, 360 pasos, \(x_0=0.1,v_0=0\). Referencia: \(x_{\max}\approx25.43309\) m; \(\int x^2dt\approx1634.84374\ \mathrm{m^2s}\); estable según el indicador implementado, aunque excede el umbral didáctico de 0.35 m. | Entrada: \(e^{-t}\), 11 nodos, 5 ocultos, \([0,4]\), ruido determinista de amplitud 0.01. Referencia: \(E_2\approx0.01682957\). |
| **MAL CONDICIONADO** | Entrada: \(v_0=9,a_0=0.75,\gamma=0.02\), reacción \(1\) s, distancia disponible \(35\) m, 160 pasos. Referencia: \(t\approx11.95733\) s; frenado \(\approx53.76971\) m; total \(\approx62.76971\) m. La sensibilidad del tiempo aumenta con la baja desaceleración. | Entrada: \(D_0=0.1,\alpha=0.00001,\beta=0,D_u=0.1001\), horizonte 20 meses; línea Morada (hipotética), mantenimiento \([2,3]\) meses desde 2026-01-01. Referencia: cruce \(t=10.000\) meses; \(\kappa_2(A)=250\) para la matriz SPD usada en el sistema lineal. | Entrada: \(m=500,c=40,k=120000,F_0=1200,\omega=1,T=12\) s, 40 pasos, \(x_0=0.1,v_0=0\). Referencia: RK4 completa los pasos (`convergio=true`) pero reporta `estable=false`; \(x_{\max}\approx2.16\times10^{46}\) m e integral \(\approx5.11\times10^{91}\ \mathrm{m^2s}\). Estos valores muestran crecimiento numérico y no son interpretables físicamente. | Entrada: función de Runge \(1/[1+25(t-0.5)^2]\), 15 nodos, 5 ocultos, \([0,1]\), ruido 0. Referencia: \(E_2\approx0.05283588\); el escenario ilustra sensibilidad del interpolante polinómico en nodos equiespaciados. |

En el módulo 2, el sistema lineal normal usa la matriz \(A\) y vector \(b\)
publicados en la sección anterior; ESTRÉS usa \(2A\) y \(2b\), por lo que su
número de condición no cambia. MAL CONDICIONADO usa la matriz SPD
\[
\begin{bmatrix}
1&0.99&0&0\\0.99&1&0&0\\0&0&2&0.5\\0&0&0.5&2
\end{bmatrix},
\]
cuyo \(\kappa_2\) es 250. En el módulo 4, \(\|e\|_2\) es la norma euclidiana
del error sobre los nodos ocultos, no el error máximo puntual.

El estado `estable` de la EDO es un control de acotamiento implementado
(finitud y escala máxima relativa al estado inicial); no es una demostración
formal de estabilidad del método. `convergio=true` en RK indica que se
completaron los pasos solicitados, no garantiza precisión ni estabilidad.
Condicionamiento, convergencia y estabilidad son propiedades distintas. El
umbral de balanceo de 0.35 m, las distancias disponibles y demás umbrales son
exclusivamente didácticos, no límites oficiales ni criterios operativos.

Los resultados de cada módulo presentan conclusiones numéricas y del problema
por separado. El historial SQLite ofrece búsqueda, filtros, detalle y
relanzamiento; el nuevo cálculo se compara con el guardado dentro de una
tolerancia explícita, incluso después de recargar la aplicación.

## Instalación y ejecución

### Requisitos

- Python 3.10 o posterior.
- `pip`.
- Un navegador web moderno.

Las dependencias Python están listadas en [`requirements.txt`](requirements.txt); incluyen Flask, NumPy y el servidor WSGI utilizado en Render.

### 1. Clonar el repositorio

```bash
git clone https://github.com/rodrigo136/ProyFinalMetodosNumericos.git SIMTELE-RISK
cd SIMTELE-RISK
```

### 2. Crear un entorno e instalar dependencias

```bash
python -m venv .venv
```

Activación en Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activación en macOS o Linux:

```bash
source .venv/bin/activate
```

Instala los paquetes requeridos:

```bash
python -m pip install -r requirements.txt
```

### 3. Inicializar la base de datos

Desde la raíz del proyecto y con el entorno virtual activado, ejecuta:

```bash
python -c "from backend.database import inicializar_base_datos; print(inicializar_base_datos())"
```

Este comando crea las tablas si no existen y siembra los casos y escenarios iniciales. También se ejecuta automáticamente al iniciar el backend, por lo que este paso explícito es opcional.

> **Precaución:** `database/schema.sql` elimina y vuelve a crear las tablas al ejecutarse directamente. No lo ejecutes sobre una base de datos con información que quieras conservar. Usa la función `inicializar_base_datos()` para la inicialización normal de la aplicación.

### 4. Iniciar el backend

En una terminal, desde la raíz del proyecto:

```bash
python backend/app.py
```

La API queda disponible por defecto en `http://127.0.0.1:5000`. Puedes comprobar su estado en `http://127.0.0.1:5000/api/salud`.

### 5. Servir el frontend

En una segunda terminal, desde la raíz del proyecto:

```bash
python -m http.server 8000 --directory frontend
```

Abre `http://127.0.0.1:8000` en el navegador. El frontend usa por defecto la API Flask en el puerto `5000` del mismo host. Ambos servidores deben permanecer activos mientras se utiliza la aplicación.

### 6. Ejecutar pruebas numéricas

Desde la raíz del proyecto:

```bash
python -m unittest discover -s tests -v
```

La suite contiene 17 pruebas: métodos y API de las semanas anteriores, cobertura
de los 12 pares módulo/escenario, parámetros y validaciones, y persistencia,
recuperación y relanzamiento. En particular, la prueba de relanzamiento compara
el nuevo resultado con el guardado usando tolerancia \(10^{-10}\).

Para detener cada servidor, pulsa `Ctrl+C` en su terminal.

### Despliegue en Render

La aplicación está desplegada en [Render](https://proyfinalmetodosnumericos.onrender.com).
Para reproducir el despliegue como Web Service de Python:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn backend.app:app`
- Health check path: `/api/salud`

El sistema usa SQLite local. El filesystem de una instancia Render es efímero
si no se configura un disco persistente; para conservar simulaciones entre
despliegues, adjunta un disco persistente (por ejemplo montado en `/var/data`)
y define `SIMTELE_RISK_DB=/var/data/simtele_risk.db` en las variables de entorno
del servicio. La ruta debe estar dentro del punto de montaje configurado.

### Rutas principales de la API

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/api/salud` | Estado del backend y sistema de referencia. |
| `GET` | `/api/metodos` | Métodos numéricos disponibles. |
| `GET` | `/api/escenarios-modulo` | Parámetros de los 4 módulos y escenarios `NORMAL`, `ESTRES` y `MAL_CONDICIONADO`. |
| `POST` | `/api/metodos/raices` | Ejecutar bisección, Newton-Raphson o secante. |
| `POST` | `/api/metodos/integracion` | Ejecutar trapecio, Simpson 1/3 o Romberg. |
| `POST` | `/api/metodos/edo` | Ejecutar Heun (RK2) o Runge-Kutta clásico (RK4). |
| `POST` | `/api/metodos/interpolacion` | Ejecutar Lagrange, Newton o spline natural. |
| `POST` | `/api/modulos/<modulo>/ejecutar` | Ruta unificada de ejecución numérica para el módulo indicado (1–4). |
| `POST` | `/api/metodos/exacta` | Resolver el sistema por el método exacto. |
| `POST` | `/api/metodos/lu` | Resolver por factorización LU. |
| `POST` | `/api/metodos/jacobi` | Resolver por Jacobi. |
| `POST` | `/api/metodos/gauss-seidel` | Resolver por Gauss-Seidel. |
| `POST` | `/api/metodos/gradiente-conjugado` | Resolver por gradiente conjugado. |
| `GET` | `/api/casos-estudio` | Consultar los casos de estudio. |
| `GET` | `/api/escenarios` | Consultar escenarios. |
| `GET` | `/api/simulaciones` | Consultar simulaciones guardadas. |
| `POST` | `/api/simulaciones` | Guardar una simulación y su configuración/resultados serializados. |
| `GET` | `/api/simulaciones/<id>` | Recuperar el detalle completo de una simulación. |
| `POST` | `/api/simulaciones/<id>/relanzar` | Recalcular desde SQLite y verificar coincidencia numérica dentro de una tolerancia. |

Las solicitudes `POST` de métodos aceptan un objeto JSON. Se puede omitir `A` y `b` para usar el sistema de referencia. Los métodos iterativos aceptan además `x0`, `tolerancia` y `max_iteraciones`.

La ruta unificada recibe, por ejemplo, `{"escenario": "NORMAL", "metodo": "rk4"}` en `POST /api/modulos/1/ejecutar`; los parámetros omitidos toman los valores del preset y los enviados reemplazan sus valores. Los métodos disponibles dependen del módulo; la respuesta contiene la configuración aplicada, el resultado y la tabla detallada correspondiente. El endpoint de relanzamiento acepta `{"tolerancia": 1e-10}` y devuelve `coincide` y `diferencia_maxima`.

## Estructura de directorios

```text
SIMTELE-RISK/
├── backend/
│   ├── app.py                 # API Flask y rutas HTTP
│   ├── database.py            # Persistencia, inicialización y datos semilla
│   ├── errores.py             # Funciones de análisis de errores
│   ├── raices.py              # Bisección, Newton-Raphson y secante
│   ├── integracion.py         # Trapecio, Simpson 1/3 y Romberg
│   ├── edo.py                 # Heun y Runge-Kutta clásico de orden 4
│   ├── interpolacion.py       # Lagrange, Newton y spline natural
│   ├── escenarios_modulo.py   # Escenarios semilla y ejecución por módulo
│   ├── sistemas_lineales.py   # Métodos numéricos para Ax = b
│   └── simtele_risk.db        # Base SQLite predeterminada (se crea al iniciar)
├── database/
│   └── schema.sql             # Esquema SQLite de las seis tablas
├── frontend/
│   ├── app.js                 # Interacción y consumo de la API
│   ├── index.html             # Estructura de la interfaz
│   └── styles.css
├── tests/
│   ├── test_api_semana2.py    # Pruebas de API y persistencia
│   ├── test_semana2.py        # Pruebas focalizadas de métodos numéricos
│   └── test_semana3.py        # Matriz 3×4 y relanzamiento SQLite
└── requirements.txt           # Dependencias de Python
```
