"""
producer.py — Simulated IoT sensor data producer
-------------------------------------------------
Publishes fake sensor readings to the Kafka topic 'sensors' once per second.

Each message is a JSON object:
  {
    "sensor_id": "sensor_03",
    "location":  "warehouse_B",
    "temperature": 21.4,
    "humidity":    58.2,
    "pressure":   1013.1,
    "timestamp":  "2024-03-12T10:00:00.123456"
  }

Usage:
  pip install confluent-kafka
  python producer.py

Optional env vars:
  KAFKA_BOOTSTRAP_SERVERS  (default: localhost:9092)
  KAFKA_TOPIC              (default: sensors)
  PUBLISH_INTERVAL_SEC     (default: 1.0)
"""

import json
import math
import os
import random
import time
from datetime import datetime, timezone

from confluent_kafka import Producer

# ── Config ─────────────────────────────────────────────────────────────────
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC             = os.getenv("KAFKA_TOPIC", "sensors")
INTERVAL          = float(os.getenv("PUBLISH_INTERVAL_SEC", "1.0"))

# ── Sensor definitions ──────────────────────────────────────────────────────
SENSORS = [
    {"sensor_id": "sensor_01", "location": "warehouse_A"},
    {"sensor_id": "sensor_02", "location": "warehouse_A"},
    {"sensor_id": "sensor_03", "location": "warehouse_B"},
    {"sensor_id": "sensor_04", "location": "warehouse_B"},
    {"sensor_id": "sensor_05", "location": "office"},
]

# Baseline values per sensor — gives each one a slightly different "normal"
BASELINES = {
    "sensor_01": {"temperature": 22.0, "humidity": 55.0, "pressure": 1013.0},
    "sensor_02": {"temperature": 21.0, "humidity": 60.0, "pressure": 1012.5},
    "sensor_03": {"temperature": 19.5, "humidity": 65.0, "pressure": 1011.0},
    "sensor_04": {"temperature": 20.5, "humidity": 62.0, "pressure": 1013.5},
    "sensor_05": {"temperature": 23.0, "humidity": 45.0, "pressure": 1014.0},
}


def simulate_reading(sensor: dict, tick: int) -> dict:
    """Generate a realistic-ish reading with slow drift + small noise."""
    sid = sensor["sensor_id"]
    base = BASELINES[sid]

    # Slow sine-wave drift over ~5-minute cycles + Gaussian noise
    drift = math.sin(tick / 300 * 2 * math.pi)

    temperature = round(base["temperature"] + drift * 2.0 + random.gauss(0, 0.2), 2)
    humidity    = round(base["humidity"]    + drift * 3.0 + random.gauss(0, 0.5), 2)
    pressure    = round(base["pressure"]   + drift * 1.5 + random.gauss(0, 0.1), 2)

    # Occasionally inject a spike to make dashboards interesting (~2% chance)
    if random.random() < 0.02:
        temperature += random.choice([-5, 5])

    return {
        "sensor_id":   sid,
        "location":    sensor["location"],
        "temperature": temperature,
        "humidity":    max(0.0, min(100.0, humidity)),
        "pressure":    pressure,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }


def delivery_report(err, msg):
    """Called by Kafka once a message is acknowledged (or fails)."""
    if err:
        print(f"  [ERROR] Delivery failed for {msg.key()}: {err}")


def wait_for_kafka(producer: Producer, retries: int = 10, delay: float = 3.0):
    """Block until Kafka is reachable, with a retry loop."""
    print(f"Connecting to Kafka at {BOOTSTRAP_SERVERS} ...")
    for attempt in range(1, retries + 1):
        try:
            meta = producer.list_topics(timeout=5)
            print(f"  Connected — {len(meta.topics)} topic(s) visible.\n")
            return
        except Exception as exc:
            print(f"  Attempt {attempt}/{retries} failed: {exc}")
            if attempt < retries:
                time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after multiple retries. Is docker-compose up?")


def main():
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})
    wait_for_kafka(producer)

    print(f"Publishing to topic '{TOPIC}' every {INTERVAL}s  (Ctrl+C to stop)\n")

    tick = 0
    try:
        while True:
            for sensor in SENSORS:
                reading = simulate_reading(sensor, tick)
                payload = json.dumps(reading).encode("utf-8")

                producer.produce(
                    topic=TOPIC,
                    key=reading["sensor_id"].encode("utf-8"),
                    value=payload,
                    callback=delivery_report,
                )

            # Flush once per batch (all 5 sensors)
            producer.poll(0)

            print(
                f"[tick {tick:>6}]  "
                f"sensor_01 temp={BASELINES['sensor_01']['temperature']:.1f}°C  "
                f"published {len(SENSORS)} readings"
            )

            tick += 1
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        producer.flush()
        print("Done.")


if __name__ == "__main__":
    main()
