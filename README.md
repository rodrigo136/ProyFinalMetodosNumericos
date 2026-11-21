# SIMTELE-RISK

**Sistema Integrado de Métodos Numéricos para Transporte por Cable**

Proyecto final de Métodos Numéricos que reúne herramientas de análisis de sistemas lineales y escenarios de riesgo inspirados en la operación de la red **Mi Teleférico**, en La Paz, Bolivia. La aplicación permite elegir casos de estudio, configurar métodos numéricos, revisar iteraciones y conservar simulaciones en una base SQLite.

> SIMTELE-RISK es un proyecto académico. Sus modelos y resultados no sustituyen los análisis de ingeniería, los sistemas de seguridad ni los procedimientos operativos oficiales de Mi Teleférico.

## Descripción del proyecto

La red de transporte por cable de La Paz opera en un entorno donde la seguridad, el mantenimiento y la calidad de las mediciones son importantes para la continuidad del servicio. SIMTELE-RISK utiliza ese contexto como marco para estudiar métodos numéricos y organizar casos y escenarios de simulación.

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
| Cálculo numérico | Python | Algoritmos para sistemas lineales y utilidades de análisis de error. |

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

Al iniciar la API, el backend crea el esquema si todavía no existe y carga los casos y escenarios iniciales. Por defecto, la base activa está en `backend/simtele_risk.db`; se puede cambiar su ubicación mediante la variable de entorno `SIMTELE_RISK_DB`.

## Cobertura matemática

### Análisis de errores

El proyecto incluye utilidades para calcular y analizar:

- **Error absoluto:** \(E_a = |x_{\text{real}} - x_{\text{aprox}}|\).
- **Error relativo:** \(E_r = E_a / |x_{\text{real}}|\), cuando el valor real no es cero. El error porcentual es \(100 E_r\).
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

### Métodos numéricos de la Semana 2

Se agregan los módulos `backend/raices.py`, `backend/integracion.py`,
`backend/edo.py` y `backend/interpolacion.py`. Los métodos reportan sus
iteraciones o tablas, errores disponibles, referencias analíticas cuando
corresponden y estados de convergencia/estabilidad. Las referencias iguales a
cero dejan el error relativo como no disponible, y se rechazan entradas o
resultados no finitos.

Los cuatro módulos incluyen escenarios reproducibles `NORMAL`, `ESTRES` y
`MAL_CONDICIONADO`. El escenario de estrés representa exigencia física u
operativa; el mal condicionado representa sensibilidad matemática. La
configuración de oscilaciones incluye además una excitación próxima a la
frecuencia natural. Son modelos académicos, no ajustes ni recomendaciones para
la operación real de Mi Teleférico.

- **Módulo 1:** frenado con Heun/RK4, cuadraturas de la velocidad y raíces del
  instante de parada.
- **Módulo 2:** raíces del deterioro respecto al umbral. El calibrador de
  sistemas lineales ya existente permanece disponible.
- **Módulo 3:** sistema masa-resorte-amortiguador forzado, y cuadraturas de
  \(x(t)^2\).
- **Módulo 4:** Lagrange, Newton por diferencias divididas y splines cúbicos
  naturales evaluados en lecturas ocultas.

El panel nuevo ofrece dos gráficos Canvas sin dependencias externas, tablas
detalladas y parámetros del escenario. Las ejecuciones numéricas se guardan en
la misma tabla SQLite de simulaciones y aparecen en el historial existente.

## Instalación y ejecución

### Requisitos

- Python 3.10 o posterior.
- `pip`.
- Un navegador web moderno.

Las dependencias Python están listadas en [`requirements.txt`](requirements.txt): Flask y NumPy.

### 1. Clonar el repositorio

Sustituye `<URL_DEL_REPOSITORIO>` por la URL del repositorio:

```bash
git clone <URL_DEL_REPOSITORIO> SIMTELE-RISK
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

Para detener cada servidor, pulsa `Ctrl+C` en su terminal.

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

Las solicitudes `POST` de métodos aceptan un objeto JSON. Se puede omitir `A` y `b` para usar el sistema de referencia. Los métodos iterativos aceptan además `x0`, `tolerancia` y `max_iteraciones`.

Las rutas de métodos nuevos reciben `{"modulo": 1, "escenario": "NORMAL", "metodo": "rk4"}`. Los métodos disponibles dependen del módulo; la respuesta contiene la configuración aplicada, el resultado y la tabla detallada correspondiente.

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
├── docs/                      # Documentación complementaria
├── frontend/
│   ├── app.js                 # Interacción y consumo de la API
│   ├── index.html             # Estructura de la interfaz
│   └── styles.css             # Estilos y diseño adaptable
├── tests/
│   └── test_semana2.py        # Pruebas focalizadas de los métodos nuevos
└── requirements.txt           # Dependencias de Python
```
