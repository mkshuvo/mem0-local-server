#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🚀 Starting Mem0 Local Server..."
docker compose up -d --build

echo "⏳ Waiting for server healthcheck..."
for i in {1..30}; do
  if curl -s -f http://localhost:28842/health > /dev/null 2>&1; then
    echo "✅ Mem0 Local Server is live and healthy at http://localhost:28842"
    exit 0
  fi
  sleep 1
done

echo "⚠️ Server started but healthcheck took longer than expected. Run 'docker compose logs -f' to inspect."
