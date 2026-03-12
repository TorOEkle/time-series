# Streaming data pipeline — local learning environment

A local streaming pipeline for learning Kafka, Kafka Connect, QuestDB, and Grafana.
Simulates IoT sensor data flowing through a production-grade ingestion stack.

```
producer.py → Kafka → Kafka Connect → QuestDB → Grafana
```

---

## Stack

| Service | Purpose | URL |
|---|---|---|
| Apache Kafka | Message broker | `localhost:9092` |
| Kafka Connect | Managed pipeline, Kafka → QuestDB | `http://localhost:8083` |
| QuestDB | Time-series database | `http://localhost:9000` |
| Grafana | Dashboards | `http://localhost:3000` |

---

## Quick start

**Prerequisites:** Docker, Docker Compose, Python 3.9+

```bash
# 1. Clone / navigate to the project folder
cd streaming-project

# 2. Install Python dependency
pip install -r requirements.txt

# 3. Start the stack
docker-compose up -d

# 4. Register the Kafka Connect connector (run once)
chmod +x register_connector.sh
./register_connector.sh

# 5. Start producing simulated sensor data
python producer.py
```

Data is now flowing. Open `http://localhost:9000` and run:

```sql
SELECT * FROM sensors LATEST ON timestamp PARTITION BY sensor_id;
```

---

## Project structure

```
streaming-project/
├── docker-compose.yml        # Kafka + Kafka Connect + QuestDB + Grafana
├── producer.py               # Simulates 5 sensors, publishes to Kafka
├── requirements.txt          # Python deps (confluent-kafka)
├── connector-sensors.json    # Kafka Connect sink connector config
├── register_connector.sh     # Registers connector via REST API
├── grafana/
│   └── dashboards/           # Exported Grafana dashboard JSON (Phase 2)
├── flink/                    # Phase 3 — stream processing
├── README.md
└── plan.md                   # Phase-by-phase learning plan
```

---

## What the producer simulates

Five sensors across three locations publish once per second:

| Sensor | Location | Fields |
|---|---|---|
| sensor_01 | warehouse_A | temperature, humidity, pressure |
| sensor_02 | warehouse_A | temperature, humidity, pressure |
| sensor_03 | warehouse_B | temperature, humidity, pressure |
| sensor_04 | warehouse_B | temperature, humidity, pressure |
| sensor_05 | office | temperature, humidity, pressure |

Each sensor has its own baseline values with a slow sine-wave drift over 5-minute cycles plus random noise. ~2% of readings include a random spike to keep dashboards interesting.

---

## How Kafka Connect works here

Instead of a hand-written consumer script, Kafka Connect manages the Kafka → QuestDB pipeline as a configured service. The connector is defined in `connector-sensors.json` and registered once via the Connect REST API. It then runs permanently inside its own container, tracking offsets and handling retries automatically.

To check the connector is running:

```bash
curl http://localhost:8083/connectors/questdb-sink-sensors/status
```

Expected output:

```json
{
  "name": "questdb-sink-sensors",
  "connector": { "state": "RUNNING", ... },
  "tasks": [{ "id": 0, "state": "RUNNING", ... }]
}
```

---

## Connecting Grafana to QuestDB

1. Open Grafana at `http://localhost:3000` (login: `admin` / `admin`)
2. Go to **Connections → Data sources → Add new**
3. Choose **PostgreSQL**
4. Fill in:
   - Host: `questdb:8812`
   - Database: `qdb`
   - User: `admin`
   - Password: `quest`
   - TLS/SSL mode: `disable`
5. Click **Save & test**

Useful queries for dashboard panels:

```sql
-- Latest reading per sensor
SELECT * FROM sensors LATEST ON timestamp PARTITION BY sensor_id;

-- Average temperature in 10-second buckets (last 10 minutes)
SELECT timestamp, sensor_id, avg(temperature) AS avg_temp
FROM sensors
WHERE timestamp > dateadd('m', -10, now())
SAMPLE BY 10s;

-- Current humidity across all sensors
SELECT sensor_id, last(humidity) AS humidity
FROM sensors
LATEST ON timestamp PARTITION BY sensor_id;
```

---

## Useful commands

```bash
# Watch raw messages arriving on the sensors topic
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic sensors --from-beginning

# List all Kafka topics
docker exec -it kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092

# Pause the connector (stops ingestion without losing offset)
curl -X PUT http://localhost:8083/connectors/questdb-sink-sensors/pause

# Resume the connector
curl -X PUT http://localhost:8083/connectors/questdb-sink-sensors/resume

# Wipe everything and start fresh
docker-compose down -v
```

---

## Learning roadmap

See `plan.md` for the full phase-by-phase plan.

| Phase | Focus | Status |
|---|---|---|
| 1 | Kafka + Kafka Connect + simulated data | ✅ complete |
| 2 | Grafana dashboard | next |
| 3 | Apache Flink stream processing | later |
| 4 | Resilience & operations | later |
