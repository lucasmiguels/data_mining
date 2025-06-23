# Projeto de Análise e Predição de Linhas de Ônibus

Este projeto tem como objetivo realizar o processamento, análise e modelagem de trajetórias de ônibus com base em dados GPS. A partir dos dados brutos, temos:
- Ingestão de dados no banco PostGIS usando multi-processing
- Criação de tabelas e views no banco para facilitar o uso dos dados
- Identificar pontos de início e fim das rotas.
- Mapas interativos das rotas.

## Estrutura do Projeto
```
├── load/ # Scripts para carga e população do banco PostGIS
├── maps/ # Mapas gerados em formato HTML
├── queries/ # Consultas SQL utilizadas no projeto
├── src/ # Código-fonte principal (processamento e criação dos mapas)
├── .gitignore # Arquivos e pastas ignorados no versionamento
└── README.md # Este arquivo
```

## Como Executar

1. Crie o banco de dados PostGIS.
2. Execute os scripts da pasta `load/` para popular o banco.
3. Rode o script de endpoints localizado na pasta `src/` para:
   - Identificar os endpoints das linhas.
   - Reconstruir as rotas.
   - Gerar os mapas interativos.

### Exemplo de execução:
```bash
python src/endpoints.py
```

## Próximos Passos

- Criar dataset consolidado com as features extraídas: posição relativa, horário, dia da semana, velocidade e sentido.
- Treinar modelos para predição de posição futura ou horário dos ônibus com base na posição atual, horário e dia da semana.
- Explorar diferentes algoritmos de machine learning para previsão, como:
  - Random Forest
  - LightGBM
- Avaliar os modelos com métricas específicas:
  - Erro médio absoluto (MAE)
  - Raiz do erro quadrático médio (RMSE)
