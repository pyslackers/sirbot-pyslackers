#!/bin/sh

set -e

docker build -f docker/dockerfile -t sirbot-pyslackers .
docker run --entrypoint scripts/test.sh sirbot-pyslackers 
