#!/usr/bin/env python
#coding:utf-8


import os,sys



def write_host_info(dns_ip_list):
    hosts_path="/etc/hosts"
    dns_path = "/etc/resolv.conf"
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
    for dns_ip in dns_ip_list:
        dns_info = "nameserver {dns_ip}".format(dns_ip=dns_ip)
        check_dns_cmd = "cat {dns_path} | grep '{dns_info}' |wc -l".format(dns_path=dns_path,dns_info=dns_info)
        dns_res = os.popen(check_dns_cmd).read().strip()
        if int(dns_res) == 0:
            with open(dns_path,"a+") as f:
                f.write(dns_info + '\n')




if __name__ == "__main__":
    dns_ip_list = sys.argv[1]
    dns_ip_list = dns_ip_list.strip().split(',')
    write_host_info(dns_ip_list)
