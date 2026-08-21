#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

docker build -t pm-app .
docker rm -f pm-app > /dev/null 2>&1 || true
mkdir -p data

ENV_FILE_ARGS=()
if [ -f .env ]; then
  ENV_FILE_ARGS=(--env-file .env)
fi

docker run -d --name pm-app -p 8000:8000 "${ENV_FILE_ARGS[@]}" -v "$(pwd)/data:/app/data" pm-app

echo "Running at http://localhost:8000"
