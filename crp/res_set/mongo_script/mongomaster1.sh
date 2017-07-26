#!/bin/bash
#IP=`ip addr|grep 172|awk -F " " '{print $2}'|awk -F "/" '{print $1}'`
#sed -i 's/IP/'$IP'/g' /data/mongodb/conf/mongodb.conf
mip=`cat /tmp/mongo.txt |sed -n "2p"`
mhost=`cat /tmp/mongo.txt |sed -n "1p"`
sed -i "2d" /etc/sysconfig/network
sed -i "/NETWORKING=yes/a\HOSTNAME=$mhost"
hostname $mhost
echo "$sip1" "$shost1" >> /etc/hosts
sed -i 's/bindIp: 127.0.0.1/bindIp: 127.0.0.1,'$mip'/g' /data/mongodb/conf/mongodb.conf
runuser -c "/usr/bin/numactl --interleave=all /opt/mongodb/bin/mongod --config=/data/mongodb/conf/mongodb.conf" mongodb01
sleep 5s
#################
MongoDB='/opt/mongodb/bin/mongo '$mip':28010'
$MongoDB <<EOF
use admin
db.createUser(  
{  
    user: "admin",  
    pwd: "123456",  
    roles:  
    [  
      {role: "userAdminAnyDatabase", db: "admin"},
      {role: "readAnyDatabase", db: "admin" },
      {role: "dbOwner", db: "admin" },
      {role: "userAdmin", db: "admin" },
      {role: "root", db: "admin" },
      {role: "dbAdmin", db: "admin" },
      {role: "clusterAdmin", db: "admin" }
    ]  
  }  
)
exit;
EOF

$MongoDB <<EOF
use admin
db.auth('admin','123456')
exit;
EOF

###########
sleep 2
#pkill mongo
#pid=`ps -ef|grep mongo|awk -F " " '{print $2}'|sed -n '1p'`
#kill -9 $pid
runuser -c "/opt/mongodb/bin/mongod --config=/data/mongodb/conf/mongodb.conf --shutdown" mongodb01
