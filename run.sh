# Create network
podman network create questdb-network

# Start containers on network
podman run -d \
  --name questdb \
  --network questdb-network \
  -p 9000:9000 -p 8812:8812 -p 9009:9009 \
  -e QDB_PG_USER=admin \
  -e QDB_PG_PASSWORD=admin \
  questdb/questdb:latest

podman run -d \
  --name grafana \
  --network questdb-network \
  -p 3000:3000 \
  grafana/grafana-oss:latest

# Verify network
#podman network inspect questdb-network

# Test connection
#podman exec -it grafana ping questdb