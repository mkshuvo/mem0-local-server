#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
BACKUP_FILE="${DIR}/data/mem0-backup-$(date +%Y%m%d-%H%M%S).json"

echo "💾 Creating backup to ${BACKUP_FILE}..."
curl -s -X POST http://localhost:28842/api/v1/export -o "${BACKUP_FILE}"
echo "✅ Backup created successfully: ${BACKUP_FILE}"
