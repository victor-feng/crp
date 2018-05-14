#!/bin/bash

ip1=`ip addr|grep "scope global"|awk -F ' ' '{print $2}'|awk -F '/' '{print $1}'|awk -F '.' '{print $1}'`
ip2=`ip addr|grep "scope global"|awk -F ' ' '{print $2}'|awk -F '/' '{print $1}'|awk -F '.' '{print $2}'`
ip3=`ip addr|grep "scope global"|awk -F ' ' '{print $2}'|awk -F '/' '{print $1}'|awk -F '.' '{print $3}'`
ping $ip1.$ip2.$ip3.1 -c 2
touch /tmp/uop.txt