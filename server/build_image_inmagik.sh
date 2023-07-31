#!/bin/bash
docker buildx build --platform linux/amd64 . -t docker.inmagik.com/wlm/server
docker push docker.inmagik.com/wlm/server