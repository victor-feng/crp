#!/usr/bin/env python
#coding:utf-8


import os,sys



ip = sys.argv[1]
cmd = "route -n"
gateway = '.'.join(ip.split('.')[:3]) + '.1'
net = "eth0"
result=os.popen(cmd).read().strip().split('\n')
for res in result:
    r=res.split()
    if "UG" in r:
        gateway = r[1]
        net = r[-1]
arping_cmd = "arping -c 4 -I {net} -s {ip} {gateway}".format(net=net,ip=ip,gateway=gateway)
os.system(arping_cmd)
