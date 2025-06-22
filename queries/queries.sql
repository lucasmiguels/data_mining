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

CREATE TABLE IF NOT EXISTS tarefas (
    id_tarefa TEXT PRIMARY KEY,
    id TEXT,
    ordem TEXT NOT NULL,
    linha TEXT NOT NULL,
    tipo TEXT CHECK (tipo IN ('posicao', 'tempo')),
    datahora TIMESTAMP WITHOUT TIME ZONE,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    conjunto TEXT,  -- 'treino', 'teste', etc
    arquivo_origem TEXT
);

CREATE TABLE IF NOT EXISTS respostas (
    id_resposta TEXT PRIMARY KEY,
    id TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    datahora TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_gps_geom ON gps_dados_onibus USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_gps_datahora ON gps_dados_onibus (datahora);
CREATE INDEX IF NOT EXISTS idx_tarefas_conjunto ON tarefas (conjunto);
