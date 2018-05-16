#!/bin/bash 

docker rmi -f $(docker images -q)
docker pull reg1.syswin.com/base/os69:v0.1

