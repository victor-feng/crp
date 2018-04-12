#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os
import re
import subprocess
import ast


def config():
    #/tmp/update.py -certificate={certificate} -domain={domain} -ip={ip} -port={port}
    if len(sys.argv) < 5:
        print "Please Input certificate(False), domain, Ip:port"
    print sys.argv, len(sys.argv)
    length_args = len(sys.argv)
    domain = sys.argv[2].split("=")[1]  # 'api.wangyan.systoon.com'
    certificate = sys.argv[1].split("=")[1]  # certificate or False

    # TODO
    ip_list = sys.argv[3].split("=")[1].split(",")
    port_list = [sys.argv[4].split("=")[1]]
    # ip_list = [sys.argv[2], sys.argv[3]]  # ['1.1.1.1', '2.2.2.2']
    # port_list = [sys.argv[4], sys.argv[5]]  # [11, 22]
    print '-----', ip_list, port_list
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

    template = '/tmp/template_https' if certificate != "0" else '/tmp/template_http'

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

    if certificate != "0": # https
        f_dst3 = re.sub(r'Certificate', certificate, f_dst3)

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
    :param args: sys.argv ['/shell/update.py', 'Certificate', 'crp-cluster.syswin.com',
    '172.28.36.31', '172.28.36.32', '8081', '999']

    ['/shell/update.py', 'crp-cluster.syswin.com',
    '172.28.36.31', '999']
    :return: ip port
    """
    length = len(args)
    if length % 2 == 0:
        # no certificate
        num_ip_port = length - 2
        ip_num = num_ip_port - num_ip_port/2
        first_ip_index = 2
    else:
        # 5 - 3 - 1
        # 7 - 3 - 2
        # 9 - 3 - 3
        num_ip_port = length - 3
        ip_num = num_ip_port - num_ip_port/2
        first_ip_index = 3
        # last_ip_index = (args.index(args[-2])+1)
    last_ip_tag = ip_num + 1
    last_ip_index = (args.index(args[-last_ip_tag]))

    # first_port_index = last_ip_index + 1
    # last_port_index = len(args) - 1
    ip_list = []
    port_list = []
    for ip in args[first_ip_index:last_ip_index+1]:
        ip_list.append(ip)
        if args.index(ip) == last_ip_index:
            break
    for i in range(ip_num):
        port_list.append(args[-1])
    return ip_list

config()
