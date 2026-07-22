# Neutramol BI Pipeline

Pipeline Python que conecta à plataforma **ThingsBoard** (`mhocloud.com`) e salva telemetria, histórico e alarmes em um banco **SQLite** pronto para consumo no Power BI.

## Clientes e dispositivos mapeados

| Cliente | Device ID | Chaves |
|---|---|---|
| Petrobrás RPBC / Usina Colorado | `2a2202e0-...` | AI1-AI3, DI1-DI8, MI/MB |
| Keeper RPBC | `c80b3ec0-...` | AI1-AI5, DI1-DI8 |
| Petrobrás REVAP | `abad0020-...` | AI1-AI6, DI8 |
| Petrobrás REGAP | `55935550-...` | AI1-AI3, DI3-DI7 |
| Petrobrás RECAP | `a35f4c70-...` | AI1-AI3, DI3-DI6 |
| Citrosuco Araras | `3c0433b0-...` | MI/MB (Modbus) |
| Gelita Mococa | `2bc7b6f0-...` | AI1 |
| Ternium RJ | `4a4b4d60-...` | MI/MB (Modbus) |

## Instalação

```bash
cd neutramol_bi
pip install -r requirements.txt
cp .env.example .env
# edite o .env com seu usuário/senha do ThingsBoard
```

## Uso

```bash
# 1. Inicializar banco (primeira vez)
python main.py init

# 2. Sincronizar valores atuais
python main.py sync-latest

# 3. Buscar histórico (últimos 30 dias na 1ª execução, depois incremental)
python main.py sync-history

# 4. Sincronizar alarmes
python main.py sync-alarms

# 5. Tudo de uma vez
python main.py sync-all

# 6. Rodar em loop (a cada 5 minutos)
python main.py scheduler --interval 5
```

## Banco de dados — tabelas para Power BI

### `telemetry_latest`
Valores mais recentes por dispositivo/chave.

| Coluna | Descrição |
|---|---|
| `device_id` | UUID do dispositivo |
| `key` | Chave (AI1, DI3, MI5…) |
| `raw_value` | Valor bruto do sensor (ADC) |
| `calibrated_value` | Valor calibrado (kg, litros, Hz…) |
| `ts` | Timestamp UNIX ms |
| `ts_dt` | Timestamp ISO 8601 (UTC) |
| `fetched_at` | Quando foi buscado |

### `telemetry_history`
Série histórica completa (uma linha por leitura).

| Coluna | Descrição |
|---|---|
| `device_id` | UUID do dispositivo |
| `key` | Chave |
| `raw_value` / `calibrated_value` | Valores |
| `ts` | Timestamp UNIX ms |
| `ts_dt` | Timestamp ISO 8601 |

### `alarms`
Alarmes por dispositivo.

| Coluna | Descrição |
|---|---|
| `device_id` | UUID do dispositivo |
| `alarm_type` | Tipo do alarme |
| `severity` | CRITICAL / MAJOR / MINOR / WARNING |
| `status` | ACTIVE / CLEARED / ACKNOWLEDGED |
| `created_dt` / `end_dt` | Datas ISO 8601 |

### `devices`
Metadados dos dispositivos (JOIN para nome e cliente).

## Power BI — conexão

1. **Get Data → SQLite** (ou use o conector ODBC para SQLite)
2. Aponte para o arquivo `neutramol.db`
3. Recomendado: criar uma Measure `Calibrated Value = SELECTEDVALUE(telemetry_latest[calibrated_value])`
4. Para JOIN: relacione `devices.id` ↔ `telemetry_history.device_id`

## Arquitetura

```
ThingsBoard API (mhocloud.com)
    ↓  tb_client.py
pipeline.py  ←  registry.py (calibração automática AI→kg/litros/Hz)
    ↓
database.py  →  neutramol.db (SQLite)
    ↓
Power BI / Excel / DBeaver
```
