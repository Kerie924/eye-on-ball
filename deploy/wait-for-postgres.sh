#!/usr/bin/env bash
# Wait until local Postgres (docker compose) accepts connections.
set -euo pipefail

HOST="${POSTGRES_HOST:-127.0.0.1}"
PORT="${POSTGRES_PORT:-5432}"
TRIES="${POSTGRES_WAIT_TRIES:-30}"

for i in $(seq 1 "${TRIES}"); do
  if (echo >"/dev/tcp/${HOST}/${PORT}") >/dev/null 2>&1; then
    exit 0
  fi
  # Fallback if /dev/tcp is unavailable
  if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -h "${HOST}" -p "${PORT}" >/dev/null 2>&1; then
      exit 0
    fi
  elif command -v nc >/dev/null 2>&1; then
    if nc -z "${HOST}" "${PORT}" >/dev/null 2>&1; then
      exit 0
    fi
  fi
  sleep 1
done

echo "Postgres not reachable at ${HOST}:${PORT} after ${TRIES}s" >&2
echo "Start it with: cd /opt/lance-on/deploy && sudo docker compose -f docker-compose.prod.yml --env-file postgres.env up -d" >&2
exit 1
