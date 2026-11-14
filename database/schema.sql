-- ============================================================================
-- SIMTELE-RISK - Esquema de base de datos
-- Motor: SQLite 3.35+
-- Descripción: tablas obligatorias del dominio de simulación de riesgo.
-- ============================================================================

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- ---------------------------------------------------------------------------
-- Limpieza (orden inverso a las dependencias)
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS resultado_resumen;
DROP TABLE IF EXISTS iteracion_resultado;
DROP TABLE IF EXISTS ejecucion_metodo;
DROP TABLE IF EXISTS simulacion;
DROP TABLE IF EXISTS escenario;
DROP TABLE IF EXISTS caso_estudio;

-- ---------------------------------------------------------------------------
-- 1. caso_estudio
-- ---------------------------------------------------------------------------
CREATE TABLE caso_estudio (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo          TEXT NOT NULL UNIQUE,
    nombre          TEXT NOT NULL,
    descripcion     TEXT,
    sector          TEXT,
    responsable     TEXT,
    estado          TEXT NOT NULL DEFAULT 'borrador'
                    CHECK (estado IN ('borrador', 'activo', 'en_revision', 'cerrado', 'archivado')),
    fecha_inicio    TEXT,
    fecha_fin       TEXT,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE INDEX idx_caso_estudio_estado ON caso_estudio (estado);

CREATE TRIGGER trg_caso_estudio_updated_at
AFTER UPDATE ON caso_estudio
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE caso_estudio SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- 2. escenario
-- ---------------------------------------------------------------------------
CREATE TABLE escenario (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_estudio_id     INTEGER NOT NULL,
    codigo              TEXT NOT NULL,
    nombre              TEXT NOT NULL,
    descripcion         TEXT,
    tipo                TEXT NOT NULL DEFAULT 'base'
                        CHECK (tipo IN ('base', 'optimista', 'pesimista', 'estres', 'personalizado')),
    probabilidad        REAL
                        CHECK (probabilidad IS NULL OR (probabilidad >= 0 AND probabilidad <= 1)),
    severidad           TEXT
                        CHECK (severidad IS NULL OR severidad IN ('baja', 'media', 'alta', 'critica')),
    parametros          TEXT NOT NULL DEFAULT '{}'
                        CHECK (json_valid(parametros)),
    activo              INTEGER NOT NULL DEFAULT 1
                        CHECK (activo IN (0, 1)),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (caso_estudio_id) REFERENCES caso_estudio (id) ON DELETE CASCADE,
    UNIQUE (caso_estudio_id, codigo)
);

CREATE INDEX idx_escenario_caso_estudio ON escenario (caso_estudio_id);
CREATE INDEX idx_escenario_tipo ON escenario (tipo);

CREATE TRIGGER trg_escenario_updated_at
AFTER UPDATE ON escenario
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE escenario SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- 3. simulacion
-- ---------------------------------------------------------------------------
CREATE TABLE simulacion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id        INTEGER NOT NULL,
    codigo              TEXT NOT NULL,
    nombre              TEXT NOT NULL,
    descripcion         TEXT,
    metodo              TEXT NOT NULL,
    version_modelo      TEXT,
    numero_iteraciones  INTEGER NOT NULL DEFAULT 10000
                        CHECK (numero_iteraciones > 0),
    semilla             INTEGER,
    nivel_confianza     REAL NOT NULL DEFAULT 0.95
                        CHECK (nivel_confianza > 0 AND nivel_confianza < 1),
    parametros          TEXT NOT NULL DEFAULT '{}'
                        CHECK (json_valid(parametros)),
    estado              TEXT NOT NULL DEFAULT 'pendiente'
                        CHECK (estado IN ('pendiente', 'en_ejecucion', 'completada', 'fallida', 'cancelada')),
    fecha_inicio        TEXT,
    fecha_fin           TEXT,
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (escenario_id) REFERENCES escenario (id) ON DELETE CASCADE,
    UNIQUE (escenario_id, codigo),
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE INDEX idx_simulacion_escenario ON simulacion (escenario_id);
CREATE INDEX idx_simulacion_estado ON simulacion (estado);

CREATE TRIGGER trg_simulacion_updated_at
AFTER UPDATE ON simulacion
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE simulacion SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- 4. ejecucion_metodo
-- ---------------------------------------------------------------------------
CREATE TABLE ejecucion_metodo (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacion_id       INTEGER NOT NULL,
    metodo              TEXT NOT NULL,
    numero_ejecucion    INTEGER NOT NULL,
    parametros          TEXT NOT NULL DEFAULT '{}'
                        CHECK (json_valid(parametros)),
    estado              TEXT NOT NULL DEFAULT 'pendiente'
                        CHECK (estado IN ('pendiente', 'en_ejecucion', 'completada', 'fallida', 'cancelada')),
    fecha_inicio        TEXT,
    fecha_fin           TEXT,
    duracion_ms         INTEGER
                        CHECK (duracion_ms IS NULL OR duracion_ms >= 0),
    mensaje_error       TEXT,
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (simulacion_id) REFERENCES simulacion (id) ON DELETE CASCADE,
    UNIQUE (simulacion_id, numero_ejecucion),
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE INDEX idx_ejecucion_metodo_simulacion ON ejecucion_metodo (simulacion_id);
CREATE INDEX idx_ejecucion_metodo_estado ON ejecucion_metodo (estado);

CREATE TRIGGER trg_ejecucion_metodo_updated_at
AFTER UPDATE ON ejecucion_metodo
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE ejecucion_metodo SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- 5. iteracion_resultado
-- ---------------------------------------------------------------------------
CREATE TABLE iteracion_resultado (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_metodo_id     INTEGER NOT NULL,
    numero_iteracion        INTEGER NOT NULL CHECK (numero_iteracion > 0),
    valores_entrada         TEXT NOT NULL DEFAULT '{}'
                            CHECK (json_valid(valores_entrada)),
    valores_salida          TEXT NOT NULL DEFAULT '{}'
                            CHECK (json_valid(valores_salida)),
    perdida                 REAL,
    metrica_principal       REAL,
    es_evento_riesgo        INTEGER NOT NULL DEFAULT 0
                            CHECK (es_evento_riesgo IN (0, 1)),
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ejecucion_metodo_id) REFERENCES ejecucion_metodo (id) ON DELETE CASCADE,
    UNIQUE (ejecucion_metodo_id, numero_iteracion)
);

CREATE INDEX idx_iteracion_resultado_ejecucion ON iteracion_resultado (ejecucion_metodo_id);
CREATE INDEX idx_iteracion_resultado_perdida ON iteracion_resultado (perdida);

-- ---------------------------------------------------------------------------
-- 6. resultado_resumen
-- ---------------------------------------------------------------------------
CREATE TABLE resultado_resumen (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_metodo_id     INTEGER NOT NULL,
    variable                TEXT NOT NULL DEFAULT 'perdida',
    n_iteraciones           INTEGER NOT NULL CHECK (n_iteraciones > 0),
    media                   REAL,
    mediana                 REAL,
    desviacion_estandar     REAL,
    minimo                  REAL,
    maximo                  REAL,
    percentil_90            REAL,
    percentil_95            REAL,
    percentil_99            REAL,
    nivel_confianza         REAL NOT NULL DEFAULT 0.95
                            CHECK (nivel_confianza > 0 AND nivel_confianza < 1),
    var                     REAL,
    cvar                    REAL,
    probabilidad_riesgo     REAL
                            CHECK (probabilidad_riesgo IS NULL OR (probabilidad_riesgo >= 0 AND probabilidad_riesgo <= 1)),
    distribucion_ajustada   TEXT,
    resumen                 TEXT NOT NULL DEFAULT '{}'
                            CHECK (json_valid(resumen)),
    generado_en             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ejecucion_metodo_id) REFERENCES ejecucion_metodo (id) ON DELETE CASCADE,
    UNIQUE (ejecucion_metodo_id, variable)
);

CREATE INDEX idx_resultado_resumen_ejecucion ON resultado_resumen (ejecucion_metodo_id);
CREATE INDEX idx_resultado_resumen_variable ON resultado_resumen (variable);

CREATE TRIGGER trg_resultado_resumen_updated_at
AFTER UPDATE ON resultado_resumen
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE resultado_resumen SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

COMMIT;
