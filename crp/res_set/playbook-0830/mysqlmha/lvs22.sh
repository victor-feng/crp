#!/bin/bash
#修改hosts

sed -i "3,6d" /usr/local/zabbix/etc/zabbix_agentd.conf
echo "Server=127.0.0.1,10.253.68.205,10.253.68.60,10.253.68.80" >> /usr/local/zabbix/etc/zabbix_agentd.conf
echo "StartAgents=8" >> /usr/local/zabbix/etc/zabbix_agentd.conf
echo "ServerActive=10.253.68.70:10051" >> /usr/local/zabbix/etc/zabbix_agentd.conf
echo "Hostname=$(ifconfig|grep Bcast|awk '{print $2}'|awk -F ":" '{print $2}')" >>/usr/local/zabbix/etc/zabbix_agentd.conf
/etc/init.d/zabbix_agentd restart >>/dev/null

sed -i "81d" /usr/local/nagios/etc/nrpe.cfg
sed -i "/nrpe_group=nagios/a\allowed_hosts=127.0.0.1,10.253.68.0/24" /usr/local/nagios/etc/nrpe.cfg

kill -9 $(ps -ef|grep nagios|grep nrpe|awk '{print $2}')
/usr/local/nagios/bin/nrpe -d -c /usr/local/nagios/etc/nrpe.cfg

echo "4lbxB%]Fkxm6" |passwd --stdin "nagios"
echo "qZ0ye4uv\$rH{" |passwd --stdin "zabbix"

#添加hosts
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
gat=$(cat /tmp/mysql.txt |sed -n "16p")
echo "$ip1 $mysql1" >>/etc/hosts
echo "$ip2 $mysql2" >>/etc/hosts
echo "$ip3 $mysql3" >>/etc/hosts
echo "$lip1 $lvs1" >>/etc/hosts
echo "$lip2 $lvs2" >>/etc/hosts
num2=`cat /tmp/mysql.txt |sed -n '8p'|awk -F "." '{print $4}'`

sed -i "2d" /etc/sysconfig/network
sed -i "/NETWORKING=yes/a\HOSTNAME=$lvs2" /etc/sysconfig/network
hostname $lvs2
echo "$lvs2" > /usr/local/host_conf

VIP=$(cat /tmp/mysql.txt |sed -n '12p')
SIP1=$(cat /tmp/mysql.txt |sed -n '4p')
SIP2=$(cat /tmp/mysql.txt |sed -n '6p')
sed -i 's/ID_NAME/lvs/g' /etc/keepalived/keepalived.conf
sed -i 's/GROUP_NAME/mysqlclu/g' /etc/keepalived/keepalived.conf
sed -i 's/MASTER/BACKUP/g' /etc/keepalived/keepalived.conf
sed -i 's/VIP/'$VIP'/g' /etc/keepalived/keepalived.conf
sed -i 's/V_PORT/'$VIP' 3316/g' /etc/keepalived/keepalived.conf
sed -i 's/R_PORT1/'$SIP1' 3316/g' /etc/keepalived/keepalived.conf
sed -i 's/R_PORT2/'$SIP2' 3316/g' /etc/keepalived/keepalived.conf
sed -i 's/connect_port PORT/connect_port 3316/g' /etc/keepalived/keepalived.conf
#sed -i 's/priority 200/priority 150/g' /etc/keepalived/keepalived.conf
sed -i 's/virtual_router_id 51/virtual_router_id '$num2'/g' /etc/keepalived/keepalived.conf
/etc/init.d/keepalived restart

ipvsadm
