#!/bin/bash
#IP=`ip addr|grep 172|awk -F " " '{print $2}'|awk -F "/" '{print $1}'`
#sed -i 's/IP/'$IP'/g' /data/mongodb/conf/mongodb.conf
sip1=`cat /tmp/mongo.txt |sed -n "6p"`
shost1=`cat /tmp/mongo.txt |sed -n "5p"`
sed -i "2d" /etc/sysconfig/network
sed -i "/NETWORKING=yes/a\HOSTNAME=$shost1"
hostname $shost1
echo "$sip1" "$shost1" >> /etc/hosts

#sed -i 's/IP/'$sip1'/g' /data/mongodb/conf/mongodb.conf
sed -i 's/bindIp: 127.0.0.1/bindIp: 127.0.0.1,'$sip1'/g' /data/mongodb/conf/mongodb.conf
#echo  "auth          = true" >> /data/mongodb/conf/mongodb.conf
#echo  "keyFile=/data/mongodb/conf/keyFilers0.key" >> /data/mongodb/conf/mongodb.conf
#echo "replSet        = $1" >> /data/mongodb/conf/mongodb.conf 
sed -i 's/#  keyFile: "\/data\/mongodb\/conf\/keyFile.key"/   keyFile: "\/data\/mongodb\/conf\/keyFile.key"/g' /data/mongodb/conf/mongodb.conf
sed -i 's/#  clusterAuthMode: keyFile/   clusterAuthMode: keyFile/g' /data/mongodb/conf/mongodb.conf
sed -i 's/#  authorization: enabled/   authorization: enabled/g' /data/mongodb/conf/mongodb.conf
sed -i 's/#  replSetName: pmm-mongo/   replSetName: '$1' /g' /data/mongodb/conf/mongodb.conf
runuser -c "/usr/bin/numactl --interleave=all /opt/mongodb/bin/mongod --config=/data/mongodb/conf/mongodb.conf" mongodb01
