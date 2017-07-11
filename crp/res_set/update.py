#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os
import re
import subprocess
import ast


def config():
    if len(sys.argv) < 4:
        print "Please Input domain, Ip:port"
    print sys.argv
    domain = sys.argv[1]  # 'api.wangyan.systoon.com'
    ip_list = ast.literal_eval(sys.argv[2])  # ['1.1.1.1', '2.2.2.2']
    port_list = ast.literal_eval(sys.argv[3])  # [11, 22]
    ip_port = resolve(ip_list, port_list)
    print 'ip + port = ', ip_port
    ips = write_server_config(ip_port)
    ip_1 = sys.argv[2]     # '172.28.265.32:8081'
    subdomain = '.'.join(domain.split('.')[:-2])

    conf_url = '/usr/local/nginx/conf/servers_systoon'
    shell_url = '/shell'
    if not os.path.isdir(conf_url):
        subprocess.Popen('mkdir /usr/local/nginx/conf/servers_systoon', shell=True, stdout=subprocess.PIPE)
    if not os.path.exists(shell_url):
        subprocess.Popen('mkdir /shell', shell=True, stdout=subprocess.PIPE)

    nginx_dir = '/usr/local/nginx/conf/servers_systoon'
    nginx_conf = os.path.join(nginx_dir, domain)

    template = '/shell/template'
    tp = open(template, 'r')
    tp_str = tp.read()
    tp.close()

    # 写nginx配置文件
    fp = open(nginx_conf, 'w')
    f_dst1 = re.sub(r'ToonDomain', domain, tp_str)
    f_dst2 = re.sub(r'server  IpPort', ips, f_dst1)
    if "innertoon.com" in domain:
        f_dst3 = re.sub(r' t100SubDomain.innertoon.com','',f_dst2)

    else:
        f_dst3 = re.sub(r'SubDomain', subdomain, f_dst2)

    fp.write(f_dst3)
    fp.close()

    # 执行nginx reload
    subprocess.Popen('/usr/local/nginx/sbin/nginx -s reload', shell=True, stdout=subprocess.PIPE)


def resolve(ip_list, port_list):
    res_list = []
    ip_num = len(ip_list)
    # port_num = len(port_list)
    if ip_num > 0:
        for ip in ip_list:
            for port in port_list:
                res_list.append(str(ip)+':'+str(port))
                port_list.pop(0)
                break
    return res_list


def write_server_config(ip_port):
    content = ''
    for i in ip_port:
        content += 'server  ' + i + '\n'
    return content

config()
