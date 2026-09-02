#!/usr/bin/env bash
# Stable backend start (no --reload) for local chat demos.
set -euo pipefail
cd "$(dirname "$0")"
pkill -f 'uvicorn app.main:app' 2>/dev/null || true
sleep 1
nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  > /tmp/planning-advisor-backend.log 2>&1 &
disown || true
echo "Starting backend (pid $!)..."
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null; then
    echo "Backend ready: http://127.0.0.1:8000/health"
    exit 0
  fi
  sleep 1
done
echo "Backend failed to become healthy. Log:"
tail -n 40 /tmp/planning-advisor-backend.log
exit 1
