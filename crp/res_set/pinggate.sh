#!/bin/bash

gateway=`route -n | grep -w 'UG'| awk '{print $2}'`
ping $gateway -c 4
touch /tmp/uop.txt