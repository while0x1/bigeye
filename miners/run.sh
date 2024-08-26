#!/bin/bash
case $1 in
2023) cd ./miners/gpu && ./cltuna 127.0.0.1 $1;;
*) cd ./miners/cpu/ && ./cpu-sha256 $1;;
esac
