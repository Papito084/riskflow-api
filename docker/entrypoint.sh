#!/bin/sh
set -e

echo "==> RiskFlow API Container Starting..."

# Wait for PostgreSQL
if [ -n "$POSTGRES_SERVER" ]; then
  echo "Waiting for PostgreSQL at $POSTGRES_SERVER:${POSTGRES_PORT:-5432}..."
  while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('$POSTGRES_SERVER', int('${POSTGRES_PORT:-5432}')))
    s.close()
    exit(0)
except Exception:
    exit(1)
  "; do
    sleep 1
  done
  echo "PostgreSQL is reachable!"
fi

# Run Database Migrations via Alembic
echo "==> Running database migrations (alembic upgrade head)..."
alembic upgrade head

# Automated data seeding (enabled by default unless explicitly disabled)
if [ "$SEED_ON_STARTUP" != "false" ]; then
  echo "==> Seeding database with realistic demo dataset..."
  python scripts/seed_data.py || echo "Warning: Seed script encountered an issue or data exists."
fi

echo "==> Launching RiskFlow API Service..."
exec "$@"
