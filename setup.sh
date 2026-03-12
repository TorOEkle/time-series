# 1. Bring up the stack (Kafka Connect takes ~60s on first run to download the plugin)
docker-compose up -d

# 2. Register the connector — run once, it persists across restarts
chmod +x register_connector.sh
./register_connector.sh

# 3. Start producing data
python producer.py
