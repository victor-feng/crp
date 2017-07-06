#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os
import re
import subprocess

if len(sys.argv) < 3:
    print "Please Input domain, Ip:port"

domain = sys.argv[1]  # 'api.wangyan.systoon.com'
ips = sys.argv[2]     #'172.28.265.32:8081'
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
f_dst2 = re.sub(r'IpPort', ips, f_dst1)
if "innertoon.com" in domain:
    f_dst3 = re.sub(r' t100SubDomain.innertoon.com','',f_dst2)

else:
    f_dst3 = re.sub(r'SubDomain', subdomain, f_dst2)

fp.write(f_dst3)
fp.close()

# 执行nginx reload
subprocess.Popen('/usr/local/nginx/sbin/nginx -s reload', shell=True, stdout=subprocess.PIPE)
