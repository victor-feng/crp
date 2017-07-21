#!/bin/bash
#修改hosts
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
MVIP=$(cat /tmp/mysql.txt |sed -n '14p')
#gat=$(cat /tmp/mysql.txt |sed -n "16p")
echo "$ip1 $mysql1" >>/etc/hosts
echo "$ip2 $mysql2" >>/etc/hosts
echo "$ip3 $mysql3" >>/etc/hosts
echo "$lip1 $lvs1" >>/etc/hosts
echo "$lip2 $lvs2" >>/etc/hosts

sed -i "2d" /etc/sysconfig/network
sed -i "/NETWORKING=yes/a\HOSTNAME=$mysql1" /etc/sysconfig/network
hostname $mysql1
#手动添加mha的vip
ip addr add $MVIP/32 dev eth0

echo "$mysql1" > /usr/local/host_conf
#配置lvs的vip，但不启动脚本
LVIP=$(cat /tmp/mysql.txt |sed -n '12p')
sed -i 's/LVIP/'$LVIP'/g' /usr/local/bin/lvs_real

#需要先把11.2上的meaasge.txt信息传到mysql1，然后筛选出mysql2的ip
slaveip1=$(cat /tmp/mysql.txt |sed -n '4p')
slaveip2=$(cat /tmp/mysql.txt |sed -n '6p')
slaveip_1=$(cat /tmp/mysql.txt |sed -n '4p'|awk -F "." '{print $1}')
slaveip_2=$(cat /tmp/mysql.txt |sed -n '4p'|awk -F "." '{print $2}')
slaveip_3=$(cat /tmp/mysql.txt |sed -n '4p'|awk -F "." '{print $3}')

#修改master的server_id
num1=`cat /tmp/mysql.txt |sed -n '2p'|awk -F "." '{print $3}'`
num2=`cat /tmp/mysql.txt |sed -n '2p'|awk -F "." '{print $4}'`
serverid="$num2"3316
sed -i 's/server_id        = 2043316/server_id        = '$serverid'/g' /data/3316/conf/my.cnf
#sed -i "/#enforce_gtid_consistency = ON/a relay_log_purge=0" /data/3316/conf/my3316.cnf
###################启动mysql
/etc/init.d/m3316 start
#定义登陆命令
MYSQL_CMD="mysql -ukvm -pKvmanger@2wg -P3316 -h127.0.0.1"
#授权给slave权限
#$MYSQL_CMD -e "GRANT REPLICATION SLAVE,REPLICATION CLIENT ON *.* TO rep3316@'$slaveip1' IDENTIFIED BY 'mysqlrel';"
#$MYSQL_CMD -e "GRANT REPLICATION SLAVE,REPLICATION CLIENT ON *.* TO rep3316@'$slaveip2' IDENTIFIED BY 'mysqlrel';"
$MYSQL_CMD -e "GRANT REPLICATION SLAVE,REPLICATION CLIENT ON *.* TO rep3316@'$slaveip_1.$slaveip_2.$slaveip_3.%' IDENTIFIED BY '1*87xE&1a';"
#查看是否授权
#select host,user from mysql.user;
#授权给mha用户权限
$MYSQL_CMD -e "GRANT ALL PRIVILEGES ON *.* TO 'mha'@'$slaveip_1.$slaveip_2.$slaveip_3.%' IDENTIFIED BY 'O[NI6I~4a' WITH GRANT OPTION;"
$MYSQL_CMD -e "FLUSH   PRIVILEGES;"
#查找binlog和pos到master.txt
echo "---------show master status result-----------" 
$MYSQL_CMD -e "show master status;" |grep "bin" > /tmp/master.txt
#拷贝master.txt到两个从节点
runuser -c "scp /tmp/master.txt mysql@$slaveip1:/tmp/" mysql
runuser -c "scp /tmp/master.txt mysql@$slaveip2:/tmp/" mysql

