#!/bin/bash
docker build . -t docker.inmagik.com/wlm/server
docker push docker.inmagik.com/wlm/server