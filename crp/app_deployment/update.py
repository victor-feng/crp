#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os
import re
import subprocess
import ast


def config():
    if len(sys.argv) < 5:
        print "Please Input certificate(False), domain, Ip:port"
    print sys.argv, len(sys.argv)
    domain = sys.argv[2]  # 'api.wangyan.systoon.com'
    certificate = sys.argv[1] # certificate or False
    # TODO
    ip_list, port_list = statistics_port_ip(sys.argv)
    # ip_list = [sys.argv[2], sys.argv[3]]  # ['1.1.1.1', '2.2.2.2']
    # port_list = [sys.argv[4], sys.argv[5]]  # [11, 22]
    ip_port = resolve(ip_list, port_list)
    print 'ip + port = ', ip_port
    ips = write_server_config(ip_port)
    print "ips = ", ips
    subdomain = '.'.join(domain.split('.')[:-2])

    conf_url = '/usr/local/nginx/conf/servers_systoon'
    shell_url = '/shell'
    if not os.path.isdir(conf_url):
        subprocess.Popen('mkdir /usr/local/nginx/conf/servers_systoon', shell=True, stdout=subprocess.PIPE)
    if not os.path.exists(shell_url):
        subprocess.Popen('mkdir /shell', shell=True, stdout=subprocess.PIPE)

    nginx_dir = '/usr/local/nginx/conf/servers_systoon'
    nginx_conf = os.path.join(nginx_dir, domain)

    template = '/tmp/template_https' if certificate else '/tmp/template_http'

    tp = open(template, 'r')
    tp_str = tp.read()
    tp.close()

    # 写nginx配置文件
    fp = open(nginx_conf, 'w')
    f_dst1 = re.sub(r't100ToonDomain', domain, tp_str)
    f_dst2 = re.sub('server  IpPort;', ips, f_dst1)

    f_dst4 = re.sub(r'ToonDomain', domain, f_dst2)
    sub_domain = 'http://' + domain + '/'
    f_dst5 = re.sub(r'http://ToonDomain/', sub_domain, f_dst4)

    if "innertoon.com" in domain:
        f_dst3 = re.sub(r' t100SubDomain.innertoon.com','',f_dst5)

    else:
        f_dst3 = re.sub(r'SubDomain', subdomain, f_dst5)

    if certificate: # https
        f_dst3 = re.sub(r'Certificate', certificate, f_dst3)
        pass

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
        content += '\t' + 'server  ' + i + ';' + '\n'
    return content


def statistics_port_ip(args):
    """
    :param args: sys.argv ['/shell/update.py', 'Certificate', 'crp-cluster.syswin.com', '172.28.36.31', '172.28.36.32', '8081', '999']
    :return: ip port
    """
    ip_num = len(args) - 4
    ip_list = []
    port_list = []
    first_ip_index = 3
    last_ip_index = (args.index(args[-2])+1)

    # first_port_index = last_ip_index + 1
    # last_port_index = len(args) - 1

    for ip in args[first_ip_index:last_ip_index+1]:
        ip_list.append(ip)
        if args.index(ip) == last_ip_index:
            break
    # for port in args[first_port_index:last_port_index+1]:
    #     port_list.append(port)
    #     if args.index(port) == last_port_index:
    #         break

    # last_port = args[last_port_index]
    # last_ip = args[last_ip_index]
    for i in range(ip_num):
        port_list.append(args[-1])
    return ip_list, port_list

config()
