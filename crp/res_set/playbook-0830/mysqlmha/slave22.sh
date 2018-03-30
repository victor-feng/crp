#!/bin/bash
#mv /data /data1
#mkdir /data
#fdisk /dev/vdb <<EOF
#n
#p
#1
#
#
#w
#
#EOF
#sleep 5s
#mkfs.ext4 /dev/vdb1
#
#sleep 8s
#echo "/dev/vdb1       /data         ext4    defaults,noatime,nodiratime,nobarrier   1 1" >> /etc/fstab
#mount -a
#cp -r /data1/* /data
#chmod 700 /data
#chown -R mysql.mysql /data

#sed -i "3,6d" /usr/local/zabbix/etc/zabbix_agentd.conf
#echo "Server=127.0.0.1,10.253.68.205,10.253.68.60,10.253.68.80" >> /usr/local/zabbix/etc/zabbix_agentd.conf
#echo "StartAgents=8" >> /usr/local/zabbix/etc/zabbix_agentd.conf
#echo "ServerActive=10.253.68.70:10051" >> /usr/local/zabbix/etc/zabbix_agentd.conf
#echo "Hostname=$(ifconfig|grep Bcast|awk '{print $2}'|awk -F ":" '{print $2}')" >>/usr/local/zabbix/etc/zabbix_agentd.conf
#/etc/init.d/zabbix_agentd restart >>/dev/null

#sed -i "81d" /usr/local/nagios/etc/nrpe.cfg
#sed -i "/nrpe_group=nagios/a\allowed_hosts=127.0.0.1,10.253.68.0/24" /usr/local/nagios/etc/nrpe.cfg

#kill -9 $(ps -ef|grep nagios|grep nrpe|awk '{print $2}')
#/usr/local/nagios/bin/nrpe -d -c /usr/local/nagios/etc/nrpe.cfg

#echo "4lbxB%]Fkxm6" |passwd --stdin "nagios"
#echo "qZ0ye4uv\$rH{" |passwd --stdin "zabbix"

mysql1=$(cat /tmp/mysql.txt |sed -n '1p')
ip1=$(cat /tmp/mysql.txt |sed -n '2p')
mysql2=$(cat /tmp/mysql.txt |sed -n '3p')
ip2=$(cat /tmp/mysql.txt |sed -n '4p')
mysql3=$(cat /tmp/mysql.txt |sed -n '5p')
ip3=$(cat /tmp/mysql.txt |sed -n '6p')
lvs1=$(cat /tmp/mysql.txt |sed -n '7p')
lip1=$(cat /tmp/mysql.txt |sed -n '8p')
lvs2=$(cat /tmp/mysql.txt |sed -n '9p')  
lip2=$(cat /tmp/mysql.txt |sed -n '10p')
#gat=$(cat /tmp/mysql.txt |sed -n "16p")
echo "$ip1 $mysql1" >>/etc/hosts
echo "$ip2 $mysql2" >>/etc/hosts
echo "$ip3 $mysql3" >>/etc/hosts
echo "$lip1 $lvs1" >>/etc/hosts
echo "$lip2 $lvs2" >>/etc/hosts

sed -i "2d" /etc/sysconfig/network
sed -i "/NETWORKING=yes/a\HOSTNAME=$mysql3" /etc/sysconfig/network
hostname $mysql3
echo "$mysql3" > /usr/local/host_conf                           
#修改lvs_real的vip
LVIP=$(cat /tmp/mysql.txt |sed -n '12p')
sed -i 's/LVIP/'$LVIP'/g' /usr/local/bin/lvs_real 
/usr/local/bin/lvs_real start
    
#ser_id=$(cat /data/3316/conf/my.cnf |grep -w server_id|grep "="|awk -F "=" '{print $2}'|awk '{gsub(/ /,"")}1')
#id=$(($ser_id-3))
#sed -i "12d" /data/3316/conf/my.cnf 
#sed -i "/server_id/a server_id=$id" /data/3316/conf/my.cnf
num1=`cat /tmp/mysql.txt |sed -n '6p'|awk -F "." '{print $3}'`
num2=`cat /tmp/mysql.txt |sed -n '6p'|awk -F "." '{print $4}'`
serverid="$num2"3316
sed -i 's/server_id        = 2043316/server_id        = '$serverid'/g' /data/3316/conf/my.cnf
#sed -i "/#enforce_gtid_consistency = ON/a relay_log_purge=0" /data/3316/conf/my3316.cnf
#打开read_only，relay_log_info_repository，master_info_repository
sed -i "54d" /data/3316/conf/my.cnf
sed -i "/skip_slave_start/a\read_only                 = on " /data/3316/conf/my.cnf
sed -i "56,57d" /data/3316/conf/my.cnf
sed -i "/skip_slave_start/a\relay_log_info_repository = TABLE" /data/3316/conf/my.cnf
sed -i "/skip_slave_start/a\master_info_repository    = TABLE" /data/3316/conf/my.cnf

rm -rf /data/3316/data/auto.cnf
###################启动mysql
#sed -i '$s/^/#/' /data/3316/script/start_3316.sh
#/bin/sh /data/3316/script/start_3316.sh > /dev/null 2>&1
/etc/init.d/m3316 restart
#$bin $id 需要在master.txt中取
masterip=$(cat /tmp/mysql.txt |sed -n '2p')
slaveip1=$(cat /tmp/mysql.txt |sed -n '4p'|awk -F "." '{print $1}')
slaveip2=$(cat /tmp/mysql.txt |sed -n '4p'|awk -F "." '{print $2}')
slaveip3=$(cat /tmp/mysql.txt |sed -n '4p'|awk -F "." '{print $3}')
MYSQL_CMD="mysql -ukvm -pKvmanger@2wg -P3316 -h127.0.0.1"
bin=$(cat /tmp/master.txt |grep bin|awk -F " " '{print $1}')
id=$(cat /tmp/master.txt |grep bin|awk -F " " '{print $2}')
#config slave
$MYSQL_CMD<< EOF
CHANGE MASTER TO
MASTER_HOST="$masterip", 
MASTER_USER='rep3316',
MASTER_PASSWORD='1*87xE&1a',
MASTER_PORT=3316,
MASTER_LOG_FILE="$bin",
MASTER_LOG_POS=$id,
MASTER_CONNECT_RETRY=10; 
EOF
$MYSQL_CMD -e "start slave;"
#启动mysql后需要给mha的用户授权
$MYSQL_CMD -e "GRANT REPLICATION SLAVE,REPLICATION CLIENT ON *.* TO rep3316@'$slaveip1.$slaveip2.$slaveip3.%' IDENTIFIED BY '1*87xE&1a';"
$MYSQL_CMD -e "GRANT ALL PRIVILEGES ON *.* TO 'mha'@'%' IDENTIFIED BY 'Mha.Sys17Q4' WITH GRANT OPTION;"
$MYSQL_CMD -e "FLUSH   PRIVILEGES;"

