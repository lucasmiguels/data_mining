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