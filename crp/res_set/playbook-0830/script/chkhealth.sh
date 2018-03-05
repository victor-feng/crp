#!/bin/bash

curl -O http://{{ansible_default_ipv4.address}}:8081/healthchk
if `cat healthchk|egrep -v 'healthchk|success'`;then
    echo 'helthchk is ok'
else
    # curl -c a.txt http://172.28.18.38:8081 >/dev/null
    curl -o dubbo http://172.28.18.38:8081/governance/addresses?keyword={{ansible_default_ipv4.address}}
    #a=`curl -b a.txt http://172.28.18.38:8081/governance/addresses?keyword={{ansible_default_ipv4.address}} |grep "没有搜到匹配的结果" `
    if cat dubbo|grep "没有搜到匹配的结果";then 
        echo "没有注册到dubbo中"
        exit 1
    fi
fi



