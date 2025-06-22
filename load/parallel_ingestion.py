import os
import json
import hashlib
import psycopg2
from pathlib import Path
from datetime import datetime
from psycopg2.extras import execute_values
from multiprocessing import Pool, cpu_count


def parse_ts(ms):
    return datetime.fromtimestamp(int(ms) / 1000)

def gerar_id(ordem, datahora):
    chave = f"{ordem}_{datahora.isoformat()}"
    return hashlib.md5(chave.encode()).hexdigest()

def load_gps_json(filepath, origem):
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    registros = []
    for d in data:
        try:
            ordem = d["ordem"]
            linha = d["linha"]
            velocidade = float(d.get("velocidade", "0").replace(",", "."))
            lat = float(d["latitude"].replace(",", "."))
            lon = float(d["longitude"].replace(",", "."))
            datahora = parse_ts(d["datahora"])
            data_envio = parse_ts(d["datahoraenvio"])
            data_servidor = parse_ts(d["datahoraservidor"])
            geom = f"SRID=4326;POINT({lon} {lat})"
            id_hash = gerar_id(ordem, datahora)
            registros.append((id_hash, ordem, linha, velocidade, datahora, data_envio, data_servidor, geom, origem))
        except Exception as e:
            print(f"[ERRO GPS] {filepath.name}: {e}")
    return registros


def load_tarefas(filepath, conjunto):
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    tarefas = []
    if not data:
        return tarefas

    primeiro = data[0]
    if "datahora" in primeiro:
        tipo = "posicao"
    elif "latitude" in primeiro and "longitude" in primeiro:
        tipo = "tempo"
    else:
        print(f"[ERRO TAREFA] {filepath.name}: Formato desconhecido.")
        return tarefas

    for d in data:
        try:
            id_raw = str(d["id"])
            id_tarefa = f"{id_raw}_{filepath.name}"
            ordem = d["ordem"]
            linha = d["linha"]

            if tipo == "posicao":
                datahora = parse_ts(d["datahora"])
                lat = None
                lon = None
            else:
                datahora = None
                lat = float(d["latitude"].replace(",", "."))
                lon = float(d["longitude"].replace(",", "."))

            tarefas.append((id_tarefa, id_raw, ordem, linha, tipo, datahora, lat, lon, conjunto, filepath.name))
        except Exception as e:
            print(f"[ERRO TAREFA] {filepath.name}: {e}")
    return tarefas

def load_respostas(filepath):
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    respostas = []
    if not data:
        return respostas

    posicao = "latitude" in data[0]
    for d in data:
        try:
            id_raw = str(d["id"])
            id_resposta = f"{id_raw}_{filepath.name}"
            if posicao:
                lat = float(d["latitude"].replace(",", "."))
                lon = float(d["longitude"].replace(",", "."))
                datahora = None
            else:
                lat = None
                lon = None
                datahora = parse_ts(d["datahora"])
            respostas.append((id_resposta, id_raw, lat, lon, datahora))
        except Exception as e:
            print(f"[ERRO RESPOSTA] {filepath.name}: {e}")
    return respostas


def insert_batch(conn, query, data, table, pasta=None, conflict_fields=None):
    if not data:
        return
    with conn.cursor() as cur:
        try:
            if conflict_fields:
                conflict_clause = f"ON CONFLICT ({', '.join(conflict_fields)}) DO NOTHING"
                full_query = query + conflict_clause
            else:
                full_query = query
            execute_values(cur, full_query, data)
            conn.commit()
            print(f"[OK] Inseridos {len(data)} registros em {table} (pasta {pasta})")
        except Exception as e:
            print(f"[ERRO INSERT {table}] {e}")
            conn.rollback()

def processar_pasta(pasta_path):
    data_pasta = pasta_path.name
    if data_pasta < "2024-05-11":
        origem = "historico"
    elif data_pasta < "2024-05-16":
        origem = "treino"
    else:
        origem = "final"

    print(f"Processando pasta {data_pasta} ({pasta_path})")

    conn = psycopg2.connect(
        host="localhost", dbname="geodata",
        user="postgres", password="postgres", port="5432"
    )

    for file in pasta_path.glob("*.json"):
        print(f"→ Verificando arquivo: {file.name}")
        if file.name.startswith(data_pasta):
            registros_raw = load_gps_json(file, origem)
            registros_dict = {r[0]: r for r in registros_raw}
            registros = list(registros_dict.values())
            insert_batch(conn, """
                INSERT INTO gps_dados_onibus 
                (id, ordem, linha, velocidade, datahora, datahora_envio, datahora_servidor, geom, origem)
                VALUES %s
            """, registros, "gps_dados_onibus", data_pasta, conflict_fields=["id"])

        elif file.name.startswith("treino"):
            tarefas = load_tarefas(file, "treino")
            insert_batch(conn, """
                INSERT INTO tarefas 
                (id_tarefa, id, ordem, linha, tipo, datahora, latitude, longitude, conjunto, arquivo_origem)
                VALUES %s
            """, tarefas, "tarefas", data_pasta, conflict_fields=["id_tarefa"])

        elif file.name.startswith("teste"):
            tarefas = load_tarefas(file, "teste")
            insert_batch(conn, """
                INSERT INTO tarefas 
                (id_tarefa, id, ordem, linha, tipo, datahora, latitude, longitude, conjunto, arquivo_origem)
                VALUES %s
            """, tarefas, "tarefas", data_pasta, conflict_fields=["id_tarefa"])

        elif file.name.startswith("resposta"):
            respostas = load_respostas(file)
            insert_batch(conn, """
                INSERT INTO respostas 
                (id_resposta, id, latitude, longitude, datahora)
                VALUES %s
            """, respostas, "respostas", data_pasta, conflict_fields=["id_resposta"])

    conn.close()

def main():
    pasta_base = Path("../dados")
    pastas = sorted([p for p in pasta_base.iterdir() if p.is_dir() and p.name.startswith("2024-")])

    with Pool(processes=6) as pool:
        pool.map(processar_pasta, pastas)

if __name__ == "__main__":
    main()
