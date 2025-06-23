CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS gps_dados_onibus (
    id TEXT PRIMARY KEY,
    ordem TEXT NOT NULL,
    linha TEXT NOT NULL,
    velocidade REAL,
    datahora TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    datahora_envio TIMESTAMP WITHOUT TIME ZONE,
    datahora_servidor TIMESTAMP WITHOUT TIME ZONE,
    geom GEOMETRY(POINT, 4326),
    origem TEXT
);