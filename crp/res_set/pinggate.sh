#!/bin/bash

gateway=`route -n | grep UG | grep -v UGH | awk '{print $2}'`
ping $gateway -c 4
touch /tmp/uop.txt