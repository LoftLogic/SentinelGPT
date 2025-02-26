#!/bin/bash
# Remove all containers with names containing "tool-runner-image"
docker rm -f $(docker ps -a --filter "ancestor=tool-runner-image" -q)

# Remove all containers with names containing "worker-image"
docker rm -f $(docker ps -a --filter "ancestor=worker-image" -q)

# Prune all dangling images (untagged images)
docker image prune -f
