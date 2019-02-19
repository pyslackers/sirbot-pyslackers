#!/bin/bash
echo "Uploading image to dockerhub"
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker push pyslackers/sirbot-pyslackers
echo "Sleeping 120 seconds for new image to be handled by dockerhub"
sleep 120

