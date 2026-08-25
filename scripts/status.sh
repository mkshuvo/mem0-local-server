#!/usr/bin/env bash
echo "📊 Checking Mem0 Local Server status (port 28842)..."
if curl -s -f http://localhost:28842/health > /dev/null 2>&1; then
  echo "✅ Server is ONLINE and HEALTHY"
  echo "Metrics:"
  curl -s http://localhost:28842/api/v1/stats
  echo ""
else
  echo "❌ Server is OFFLINE or unreachable on port 28842"
  docker ps -a --filter "name=mem0-local-server"
fi
