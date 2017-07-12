#!/bin/bash

REDISCLI="/usr/local/{{redis_version}}/src/redis-cli -h {{ansible_default_ipv4.address}} -p {{redis_port}}"
LOGFILE="/var/log/keepalived-redis-state.log"

echo "[backup]" >> $LOGFILE
date >> $LOGFILE
echo "Being slave...." >> $LOGFILE 2>&1

# 延迟15s等待数据被对方同步完成之后再切换主从角色
echo "sleep ... " >> $LOGFILE
sleep 15s
echo "Run SLAVEOF cmd ..." >> $LOGFILE
$REDISCLI SLAVEOF {{slaveofIP}} {{redis_port}} >> $LOGFILE  2>&1
