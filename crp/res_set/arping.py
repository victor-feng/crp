#!/usr/bin/env python
#coding:utf-8


import os,sys,time



ip = sys.argv[1]
cmd = "route -n  | grep -w UG | awk '{print $2}'"
gateway = '.'.join(ip.split('.')[:3]) + '.1'
net = "eth0"
gateway=os.popen(cmd).read().strip()
for i in range(10):
    time(6)
    check_cmd = "ip addr | grep {ip} | wc -l ".format(ip=ip)
    res = os.popen(cmd).read().strip()
    if int(res) > 0:
        arping_cmd = "arping -c 4 -I {net} -s {ip} {gateway}".format(net=net,ip=ip,gateway=gateway)
        print arping_cmd
        os.system(arping_cmd)
        break
else:
    print "execute arping failed"
