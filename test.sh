#!/bin/sh

set -e

docker build -f Dockerfile -t sirbot-pyslackers . 
docker run --entrypoint scripts/test.sh sirbot-pyslackers 
