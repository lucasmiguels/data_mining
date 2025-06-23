CREATE INDEX IF NOT EXISTS idx_gps_geom ON gps_dados_onibus USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_gps_datahora ON gps_dados_onibus (datahora);
CREATE INDEX IF NOT EXISTS idx_tarefas_conjunto ON tarefas (conjunto);