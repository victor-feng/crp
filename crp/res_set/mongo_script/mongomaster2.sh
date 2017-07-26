#!/bin/bash
mip=`cat /tmp/mongo.txt |sed -n "2p"`
sip1=`cat /tmp/mongo.txt |sed -n "4p"`
sip2=`cat /tmp/mongo.txt |sed -n "6p"`
#pkill mongo
sed -i 's/#  keyFile: "\/data\/mongodb\/conf\/keyFile.key"/   keyFile: "\/data\/mongodb\/conf\/keyFile.key"/g' /data/mongodb/conf/mongodb.conf
sed -i 's/#  clusterAuthMode: keyFile/   clusterAuthMode: keyFile/g' /data/mongodb/conf/mongodb.conf
sed -i 's/#  authorization: enabled/   authorization: enabled/g' /data/mongodb/conf/mongodb.conf
sed -i 's/#  replSetName: pmm-mongo/   replSetName: '$1' /g' /data/mongodb/conf/mongodb.conf
runuser -c "/usr/bin/numactl --interleave=all /opt/mongodb/bin/mongod --config=/data/mongodb/conf/mongodb.conf" mongodb01
sleep 2
MongoDB='/opt/mongodb/bin/mongo '$mip':28010 -uadmin -p123456 --authenticationDatabase admin'
$MongoDB <<EOF
rs.initiate(
   {
      _id: "$1",
      version: 1,
      members: [
         { _id: 0, host : "$mip:28010",priority:3},
         { _id: 1, host : "$sip1:28010",priority:2},
         { _id: 2, host : "$sip2:28010",priority:1}
      ]
   }
)
exit;
EOF
