#!/usr/bin/env bash
set -euo pipefail

echo "==> Green CDN: Playground setup (Linux/macOS)"

# Ensure we're in repo root (script may be called from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is not installed. Please install Docker Desktop first." >&2
  exit 1
fi

# Compose command shim
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "Error: docker compose or docker-compose not found." >&2
  exit 1
fi

# Create .env if missing (uses demo data if WattTime creds not provided)
if [ ! -f .env ]; then
  cp env_example.txt .env
  echo "Created .env from env_example.txt (using demo data unless you add WattTime credentials)."
fi

echo "==> Building images (first run only)"
$COMPOSE build

echo "==> Starting services"
$COMPOSE up -d

echo "==> Waiting a few seconds for services to become ready..."
sleep 3

echo "\nGreen CDN is starting. Access points:"
echo "- Weight Manager:     http://localhost:5000"
echo "- Weight Viewer:      http://localhost:5001"
echo "- HAProxy Stats:      http://localhost:8404/stats"
echo "- Test Load Balancer: http://localhost:80"
echo "- Historical Sim:     http://localhost:5000/historical-simulation"

echo "\nTips:"
echo "- For real WattTime data, set WATTTIME_USERNAME and WATTTIME_PASSWORD in .env and restart."
echo "- To view logs: $COMPOSE logs -f"
echo "- To stop:      $COMPOSE down"


