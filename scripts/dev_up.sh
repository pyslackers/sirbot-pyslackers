#!/bin/sh

set -e

docker-compose -p sirbot -f docker/docker-compose.yml up --build --detach
docker logs --follow sirbot_sirbot_1
