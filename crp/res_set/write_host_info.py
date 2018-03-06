#!/usr/bin/env python
#coding:utf-8


import os

def write_host_info():
    hosts_path="/etc/hosts"
    cmd = "hostname"
    hostname = os.popen(cmd).read().strip()
    ip = "127.0.0.1"
    host_info = "{ip} {hostname}".format(ip=ip,hostname=hostname)
    check_cmd = "cat {hosts_path} |grep '{host_info}' |wc -l".format(hosts_path=hosts_path,host_info=host_info)
    res = os.popen(check_cmd).read().strip()

    if int(res) == 0:
        #write_to_file(host_info,hosts_path)
        with open(hosts_path,"a+") as f:
            f.write(host_info)



if __name__ == "__main__":
    write_host_info()
