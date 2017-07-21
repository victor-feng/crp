#!/bin/bash
sed -i '/new-host/{n;d}' $1/hosts
ip=$(cat $1/mysql.txt | sed -n "8p")
sed -i "/new-host/a $ip" $1/hosts
scp -i $1/../old_id_rsa  $1/mysql.txt root@$ip:/tmp/
