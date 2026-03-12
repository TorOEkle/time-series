# Streaming data learning project — plan

## Goal

Build a local streaming pipeline to learn how Kafka, QuestDB, and Grafana work together. Start with Kafka Connect as the production-grade ingestion pattern, then add stream processing complexity in later phases.

---

## Current state

- `docker-compose.yml` — Kafka + Kafka Connect + QuestDB + Grafana ✅
- `producer.py` — simulates 5 sensors, publishes to `sensors` topic ✅
- `connector-sensors.json` — QuestDB sink connector config ✅
- `register_connector.sh` — registers connector via Kafka Connect REST API ✅
- Grafana dashboard: not yet set up
- Flink: Phase 3

---

## Stack

| Component | Role | Status |
|---|---|---|
| Apache Kafka | Message broker, topic storage | ✅ running |
| Kafka Connect | Managed consumer, Kafka → QuestDB | ✅ running |
| QuestDB sink connector | Translates JSON → ILP, writes rows | ✅ configured |
| `producer.py` | Simulates sensor data | ✅ ready |
| QuestDB | Time-series storage | ✅ running |
| Grafana | Dashboards | ✅ running, dashboard pending |
| Apache Flink | Stream processing | Phase 3 |

> **Why Kafka Connect instead of `consumer.py`?**
> Kafka Connect is the production pattern — the pipeline is defined as config (JSON),
> not application code. It handles offset tracking, retries, and parallelism automatically.
> Adding a new topic later means one new JSON file and a single `curl` POST — no code changes.

---

## Phase 1 — Kafka + Kafka Connect + simulated data ✅

**Goal:** Get data flowing end-to-end from a Python script into QuestDB via Kafka Connect.

### Steps

1. **docker-compose.yml** ✅
   - Kafka in KRaft mode (no Zookeeper)
   - Kafka Connect with QuestDB sink connector plugin
   - QuestDB + Grafana

2. **`producer.py`** ✅
   - 5 simulated sensors across 2 warehouses + 1 office
   - Fields: `temperature`, `humidity`, `pressure`
   - Tags: `sensor_id`, `location`
   - Publishes JSON to topic `sensors` once per second
   - Includes slow sine-wave drift + random spikes for realistic data

3. **`connector-sensors.json`** ✅
   - QuestDB sink connector reading from `sensors` topic
   - Maps JSON fields to QuestDB columns
   - Tags (`sensor_id`, `location`) become indexed symbol columns
   - Numerics (`temperature`, `humidity`, `pressure`) become double columns

4. **`register_connector.sh`** ✅
   - Idempotent — safe to run multiple times
   - Waits for Kafka Connect to be healthy before registering
   - Prints connector status on completion

### Verify it works

```bash
# 1. Bring up the stack
docker-compose up -d

# 2. Register the connector (once)
./register_connector.sh

# 3. Start producing data
python producer.py

# 4. Open QuestDB console → http://localhost:9000
SELECT * FROM sensors LIMIT 20;
SELECT * FROM sensors LATEST ON timestamp PARTITION BY sensor_id;
```

### Deliverables
- [x] `docker-compose.yml` with Kafka + Kafka Connect + QuestDB + Grafana
- [x] `producer.py`
- [x] `connector-sensors.json`
- [x] `register_connector.sh`
- [ ] Data confirmed flowing in QuestDB console

---

## Phase 2 — Grafana dashboard

**Goal:** Visualise the streaming data with live-updating panels.

### Steps

1. **Connect Grafana to QuestDB**
   - Add a PostgreSQL datasource in Grafana (`http://localhost:3000`)
   - Host: `questdb:8812`
   - Database: `qdb`, user: `admin`, password: `quest`
   - SSL mode: disable

2. **Build a dashboard**
   - Time-series panel — temperature over time per sensor
   - Stat panel — latest reading per sensor (`LATEST ON`)
   - Gauge panel — current humidity range across all sensors
   - Set auto-refresh to 5s

3. **Learn QuestDB time-series SQL**
   - `SAMPLE BY 10s` — downsample to 10-second buckets
   - `LATEST ON timestamp PARTITION BY sensor_id` — last value per sensor
   - `WHERE timestamp > dateadd('m', -5, now())` — rolling 5-minute window

4. **Export dashboard JSON**
   - Save to `grafana/dashboards/sensors.json` for version control

### Deliverables
- [ ] Grafana datasource connected to QuestDB
- [ ] Dashboard with at least 3 panels
- [ ] Queries using `SAMPLE BY` and `LATEST ON`
- [ ] Dashboard JSON exported

---

## Phase 3 — Add Apache Flink

**Goal:** Introduce stateful stream processing between Kafka and QuestDB.

### How it fits in

Flink slots in between Kafka and Kafka Connect — it reads from the raw `sensors` topic,
processes the stream, and writes aggregated results to a new topic `sensors_agg`.
A second Kafka Connect connector then picks up `sensors_agg` and writes to a separate
QuestDB table. The existing pipeline is untouched.

```
producer.py → sensors topic → Flink → sensors_agg topic → Kafka Connect → QuestDB
                                  ↓ (raw, unchanged)
                           Kafka Connect → QuestDB (existing)
```

### Steps

1. **Add Flink to docker-compose.yml**
   - JobManager + TaskManager containers
   - Flink UI at `http://localhost:8081`

2. **Write a Flink job** (`flink/sensor_aggregator.py` via PyFlink)
   - Read from `sensors` Kafka topic
   - Apply a 30-second tumbling window
   - Compute `min`, `max`, `avg` per `sensor_id` per window
   - Write results to `sensors_agg` Kafka topic

3. **Add a second connector** (`connector-sensors-agg.json`)
   - Same pattern as `connector-sensors.json`
   - Reads `sensors_agg`, writes to QuestDB table `sensors_aggregated`
   - Register with `register_connector.sh` (update script to loop all JSONs)

4. **Extend Grafana dashboard**
   - Add panels comparing raw vs windowed aggregations
   - Overlay avg temperature with raw scatter

### Deliverables
- [ ] Flink running in docker-compose
- [ ] `sensor_aggregator.py` Flink job
- [ ] `connector-sensors-agg.json`
- [ ] `sensors_aggregated` table populated in QuestDB
- [ ] Updated Grafana dashboard

---

## Phase 4 — Resilience & operations

**Goal:** Understand what makes the pipeline robust and how to operate it.

### Topics to explore

- **Kafka retention** — messages persist on disk; what happens if Connect goes down and restarts?
- **Consumer group offsets** — Kafka Connect tracks exactly where it stopped; replay by resetting offsets
- **Dead letter topic** — route malformed messages to a `sensors_dlq` topic instead of dropping them
- **QuestDB WAL mode** — write-ahead log protects against data loss on crash
- **Flink checkpointing** — Flink snapshots state to S3/disk; jobs resume from last checkpoint
- **Schema evolution** — add a new field to the producer; what breaks, what doesn't?
- **Connector parallelism** — increase `tasks.max` and add partitions; watch throughput scale

### Exercises

- Stop Kafka Connect mid-run, restart it — does it resume without data loss?
- Send a malformed JSON from a producer — where does the message end up?
- `docker-compose stop questdb` then restart — is all data intact?
- Reset the connector offset to replay the last 10 minutes of data

---

## File structure

```
streaming-project/
├── docker-compose.yml            # Full stack
├── producer.py                   # Simulated sensor data
├── requirements.txt              # confluent-kafka
├── connector-sensors.json        # Kafka Connect → QuestDB config
├── register_connector.sh         # Registers connector via REST API
├── flink/                        # Phase 3
│   └── sensor_aggregator.py
├── grafana/
│   └── dashboards/
│       └── sensors.json          # Exported dashboard (Phase 2)
├── README.md
└── plan.md                       # This file
```

---

## Useful commands

```bash
# ── Docker ──────────────────────────────────────────────────────────────────
docker-compose up -d              # Start all services
docker-compose down               # Stop (keeps volumes)
docker-compose down -v            # Stop + wipe all data

# ── Kafka ────────────────────────────────────────────────────────────────────
# List topics
docker exec -it kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Watch messages arriving on the sensors topic (debug)
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic sensors --from-beginning

# ── Kafka Connect ────────────────────────────────────────────────────────────
curl http://localhost:8083/connectors                                    # list
curl http://localhost:8083/connectors/questdb-sink-sensors/status        # status
curl -X PUT http://localhost:8083/connectors/questdb-sink-sensors/pause  # pause
curl -X DELETE http://localhost:8083/connectors/questdb-sink-sensors     # delete

# ── QuestDB ──────────────────────────────────────────────────────────────────
# Open http://localhost:9000 and run SQL, e.g.:
# SELECT * FROM sensors LATEST ON timestamp PARTITION BY sensor_id;
# SELECT sensor_id, avg(temperature) FROM sensors SAMPLE BY 10s;
```
