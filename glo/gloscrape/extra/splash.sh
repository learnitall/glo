#!/bin/env bash
# Having some stability issues with splash.
# This is a script to run it forever.
# I would use --restart-always but there is
# an open bug for non-root containers:
# https://github.com/containers/podman/issues/8047

while true
do
    podman run --rm -p 8050:8050 docker.io/scrapinghub/splash
done
