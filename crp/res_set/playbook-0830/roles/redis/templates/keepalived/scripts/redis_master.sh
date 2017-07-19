#!/bin/bash

REDISCLI="/usr/local/{{redis_version}}/src/redis-cli -h {{ansible_default_ipv4.address}} -p {{redis_port}}"
LOGFILE="/var/log/keepalived-redis-state.log"

echo "[master]" >> $LOGFILE
date >> $LOGFILE
echo "Being master...." >> $LOGFILE 2>&1

echo "Run SLAVEOF cmd ..." >> $LOGFILE
$REDISCLI SLAVEOF {{slaveofIP}} {{redis_port}} >> $LOGFILE  2>&1
$REDISCLI CONFIG SET SLAVE-READ-ONLY NO >> $LOGFILE  2>&1
echo "sleep..." >> $LOGFILE 2>&1
sleep 2s

echo "Run SLAVEOF NO ONE cmd ..." >> $LOGFILE
$REDISCLI SLAVEOF NO ONE >> $LOGFILE 2>&1

