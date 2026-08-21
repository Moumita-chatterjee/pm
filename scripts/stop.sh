#!/usr/bin/env bash
set -euo pipefail

docker stop pm-app > /dev/null 2>&1 || true
docker rm pm-app > /dev/null 2>&1 || true

echo "Stopped"
