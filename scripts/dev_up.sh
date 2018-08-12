#!/bin/sh

set -e

docker-compose -p sirbot -f docker/docker-compose.dev.yml up --build --detach
docker logs --follow sirbot_sirbot_1
