-- Inicialización de la base de datos para el sistema de registro universitario

CREATE TABLE IF NOT EXISTS registros (
    id         SERIAL PRIMARY KEY,
    nombre     TEXT NOT NULL,
    comuna     TEXT NOT NULL,
    fecha      DATE NOT NULL,
    carrera    TEXT NOT NULL,
    servidor   TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vista de estadísticas por comuna
CREATE OR REPLACE VIEW stats_por_comuna AS
    SELECT
        comuna,
        COUNT(*) AS total_registros,
        SUM(CASE WHEN carrera = 'Medicina'    OR carrera = 'Medicine'    THEN 1 ELSE 0 END) AS medicina,
        SUM(CASE WHEN carrera = 'Ingeniería'  OR carrera = 'Engineering' THEN 1 ELSE 0 END) AS ingenieria,
        SUM(CASE WHEN carrera = 'Abogacía'    OR carrera = 'Law'         THEN 1 ELSE 0 END) AS abogacia,
        SUM(CASE WHEN carrera = 'Licenciatura'OR carrera = 'Education'   THEN 1 ELSE 0 END) AS licenciatura
    FROM registros
    GROUP BY comuna
    ORDER BY comuna;
