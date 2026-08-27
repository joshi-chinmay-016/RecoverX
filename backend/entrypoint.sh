#!/bin/bash
set -e

echo "=== [RecoverX] Starting Application Container ==="

# 1. Run Alembic database migrations
echo "[RecoverX] Running database migrations (alembic upgrade head)..."
alembic upgrade head

# 2. Bootstrap initial demo users and tenant merchants (idempotent)
echo "[RecoverX] Bootstrapping demo accounts and merchant memberships..."
python scripts/create_demo_user.py

# 3. If a custom command is provided (e.g. Docker Compose worker or dev reload), execute it
if [ $# -gt 0 ]; then
    echo "[RecoverX] Executing custom command: $@"
    exec "$@"
fi

# 4. Default: Start Uvicorn API server
PORT_NUMBER="${PORT:-8000}"
echo "[RecoverX] Starting Uvicorn API server on 0.0.0.0:${PORT_NUMBER}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT_NUMBER}"
