#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🛑 Stopping Mem0 Local Server..."
docker compose down
echo "✅ Stopped."
