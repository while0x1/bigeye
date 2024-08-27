#!/bin/bash
# example how to run the miner in an endless loop
#
# simple config for 1 GPU:
#  "AUTO_SPAWN_MINERS": true,
#  "MINER_EXECUTABLE": "miners/gpu/run.sh",
#  "MINERS": "127.0.0.1:2023",
#
while true; do ./cltuna 0.0.0.0 $1; sleep 1; done
