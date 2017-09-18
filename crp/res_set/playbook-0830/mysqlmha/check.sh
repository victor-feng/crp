#!/bin/bash
sed -i '/new-host/{n;d}' $1/hosts
ip=$(cat $1/mysql.txt | sed -n "2p")
sed -i "/new-host/a $ip" $1/hosts
ansible -i $1/hosts  new-host -u root --private-key=$1/../old_id_rsa -m command -a "mysql -ukvm -pKvmanger@2wg -P3316 -h127.0.0.1 -e 'show databases;'"

sed -i '/new-host/{n;d}' $1/hosts
ip=$(cat $1/mysql.txt | sed -n "4p")
sed -i "/new-host/a $ip" $1/hosts
ansible -i $1/hosts  new-host -u root --private-key=$1/../old_id_rsa -m command -a "mysql -ukvm -pKvmanger@2wg -P3316 -h127.0.0.1 -e 'show databases;'"

sed -i '/new-host/{n;d}' $1/hosts
ip=$(cat $1/mysql.txt | sed -n "6p")
sed -i "/new-host/a $ip" $1/hosts
ansible -i $1/hosts  new-host -u root --private-key=$1/../old_id_rsa -m command -a "mysql -ukvm -pKvmanger@2wg -P3316 -h127.0.0.1 -e 'show databases;'"

sed -i '/new-host/{n;d}' $1/hosts
ip=$(cat $1/mysql.txt | sed -n "8p")
sed -i "/new-host/a $ip" $1/hosts
ansible -i $1/hosts  new-host -u root --private-key=$1/../old_id_rsa -m command -a "ip addr"

sed -i '/new-host/{n;d}' $1/hosts
ip=$(cat $1/mysql.txt | sed -n "10p")
sed -i "/new-host/a $ip" $1/hosts
ansible -i $1/hosts  new-host -u root --private-key=$1/../old_id_rsa -m command -a "ip addr"