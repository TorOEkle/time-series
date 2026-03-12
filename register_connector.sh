#!/usr/bin/env bash
# register_connector.sh
# ---------------------
# Registers the QuestDB sink connector with Kafka Connect.
# Run this once after `docker-compose up -d` and the stack is healthy.
#
# Usage:
#   chmod +x register_connector.sh
#   ./register_connector.sh

CONNECT_URL="http://localhost:8083"
CONNECTOR_FILE="connector-sensors.json"

# ── Wait for Kafka Connect to be ready ─────────────────────────────────────
echo "Waiting for Kafka Connect to be ready..."
until curl -sf "${CONNECT_URL}/connectors" > /dev/null; do
  echo "  Not ready yet — retrying in 5s..."
  sleep 5
done
echo "Kafka Connect is up."
echo ""

# ── Register (or update) the connector ─────────────────────────────────────
CONNECTOR_NAME=$(python3 -c "import json; d=json.load(open('${CONNECTOR_FILE}')); print(d['name'])")

EXISTING=$(curl -sf "${CONNECT_URL}/connectors/${CONNECTOR_NAME}" 2>/dev/null)

if [ -n "$EXISTING" ]; then
  echo "Connector '${CONNECTOR_NAME}' already exists — updating config..."
  curl -s -X PUT "${CONNECT_URL}/connectors/${CONNECTOR_NAME}/config" \
    -H "Content-Type: application/json" \
    -d "$(python3 -c "import json; d=json.load(open('${CONNECTOR_FILE}')); print(json.dumps(d['config']))")"
  echo ""
else
  echo "Registering connector '${CONNECTOR_NAME}'..."
  curl -s -X POST "${CONNECT_URL}/connectors" \
    -H "Content-Type: application/json" \
    -d @"${CONNECTOR_FILE}"
  echo ""
fi

# ── Show status ─────────────────────────────────────────────────────────────
echo ""
echo "Connector status:"
curl -sf "${CONNECT_URL}/connectors/${CONNECTOR_NAME}/status" | python3 -m json.tool

echo ""
echo "Done. Data will now flow: producer.py → Kafka → Kafka Connect → QuestDB"
echo ""
echo "Useful commands:"
echo "  List connectors:   curl http://localhost:8083/connectors"
echo "  Check status:      curl http://localhost:8083/connectors/${CONNECTOR_NAME}/status"
echo "  Pause connector:   curl -X PUT http://localhost:8083/connectors/${CONNECTOR_NAME}/pause"
echo "  Delete connector:  curl -X DELETE http://localhost:8083/connectors/${CONNECTOR_NAME}"
