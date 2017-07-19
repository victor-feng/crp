#!/bin/bash

ALIVE=`/usr/local/{{redis_version}}/src/redis-cli -h {{ansible_default_ipv4.address}} -p {{redis_port}} PING`

if [ "$ALIVE" == "PONG" ];then
  echo $ALIVE
  exit 0
else
  echo $ALIVE
  exit 1
fi
