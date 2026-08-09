#!/usr/bin/env bash
set -e

echo "Checking Docker access..."

if docker info >/dev/null 2>&1; then
  echo "Docker is ready."
else
  echo "Docker permission error detected."
  echo ""
  echo "Run these commands in your terminal:"
  echo "  sudo usermod -aG docker \$USER"
  echo "  newgrp docker"
  echo ""
  echo "If newgrp does not work, log out and log back in, then run this script again."
  exit 1
fi

cd "$(dirname "$0")/.."
docker compose up -d

echo ""
echo "Services started:"
echo "  PostgreSQL -> localhost:5432"
echo "  MinIO API  -> localhost:9000"
echo "  MinIO UI   -> http://localhost:9001 (minioadmin / minioadmin)"
echo ""
echo "Next, start the backend:"
echo "  cd backend"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
