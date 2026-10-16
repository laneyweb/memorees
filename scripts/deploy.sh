#!/bin/sh
# Memorees deploy — stamps version provenance, then (re)builds.
# Usage:  sh scripts/deploy.sh
set -e
cd "$(dirname "$0")/.."
export BUILD_HASH="$(git rev-parse --short HEAD)"
export BUILD_DATE="$(date -u +%FT%TZ)"
echo "Deploying build $BUILD_HASH ($BUILD_DATE)"
docker compose up -d --build "$@"
docker compose ps
