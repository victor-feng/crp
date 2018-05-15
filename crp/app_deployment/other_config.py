#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os
import re
import subprocess


BASE_PATH = "/usr/local/nginx/conf/servers_systoon"
TEMPLATE_PATH = "/tmp"
# BASE_PATH = "/home/mcq/tmp"
# TEMPLATE_PATH = "/home/mcq/tmp"


def create(**kwargs):
    """
        create config
    """
    # params
    certificate = kwargs.get('-certificate', "")
    project = kwargs.get('-project', "")
    domain = kwargs.get('-domain', "")
    domain_path = kwargs.get('-domain_path', "")
    ip_list = kwargs.get('-ip', "").split(",")
    port = kwargs.get('-port', 80)

    template = '{}/other_template_https'.format(TEMPLATE_PATH) \
            if certificate else '{}/other_template_http'.format(TEMPLATE_PATH)

    if not all([project, domain, ip_list]):
        print "Error: params value error"; return

    # dir
    if not os.path.isdir(BASE_PATH):
        subprocess.Popen(
            'mkdir {}'.format(BASE_PATH), shell=True, stdout=subprocess.PIPE)

    nginx_conf = os.path.join(BASE_PATH, domain)

    # params contact
    ip_port = ['{}:{}'.format(i, port) for i in ip_list]
    ips = write_server_config(ip_port)

    if os.path.exists(nginx_conf):
        with open(nginx_conf, 'rb') as f:
            all_c = f.read()
            content = all_c.split("# --- divid ---")

        # if re.findall(project, content[0]):
        #     print "Error: project already exists !"; return
        # if re.findall(project, content[2]):
        #     print "Error: domain_path already exists !"; return


        content[2] = "# --- divid ---" + content[2]
        tp = sub_content(
            template, project, ips, domain, domain_path, certificate).split("# --- divid ---")

        if re.findall(project, content[0]):
            tmp = [i.strip() for i in content[0].split('upstream') if project in i]
            content = re.sub(tmp[0], tp[0].lstrip('upstream').strip(), all_c)
        else:
            tp = [i + "# --- divid ---" for i in tp]
            content.insert(1, tp[0])
            content.insert(4, tp[2])
            content = "".join(content)
    else:
        content =sub_content(
            template, project, ips, domain, domain_path, certificate)

    fp = open(nginx_conf, 'wb')
    fp.write(content)
    fp.close()

    # reload nginx
    subprocess.Popen('/usr/local/nginx/sbin/nginx -s reload', shell=True, stdout=subprocess.PIPE)


# def update(**kwargs):
#     """
#         update config
#     """
#     certificate = kwargs.get('-certificate', "")
#     project = kwargs.get('-project', "")
#     domain = kwargs.get('-domain', "")
#     domain_path = kwargs.get('-domain_path', "")
#     ip_list = kwargs.get('-ip', "").split(",")
#     port = kwargs.get('-port', 80)
# 
#     template = '{}/other_template_https'.format(TEMPLATE_PATH) \
#             if certificate else '{}/other_template_http'.format(TEMPLATE_PATH)
# 
#     nginx_conf = os.path.join(BASE_PATH, domain)
#     if not os.path.exists(nginx_conf):
#         return "Error: config file not exists"
# 
#     ip_port = ['{}:{}'.format(i, port) for i in ip_list]
#     ips = write_server_config(ip_port)
# 
#     if os.path.exists(nginx_conf):
#         with open(nginx_conf, 'rb') as f:
#             content = f.read()
#             fp = content.split("# --- divid ---")
# 
#         if not re.findall(project, fp[0]):
#             return "Error: project not exists !"
# 
#         tp = sub_content(
#             template, project, ips, domain, domain_path, certificate).split("# --- divid ---")
# 
#         tmp = [i.strip() for i in fp[0].split('upstream') if project in i]
#         content = re.sub(tmp[0], tp[0].lstrip('upstream').strip(), content)
# 
#     fp = open(nginx_conf, 'wb')
#     fp.write(content)
#     fp.close()
# 
#     # reload nginx
#     subprocess.Popen('/usr/local/nginx/sbin/nginx -s reload', shell=True, stdout=subprocess.PIPE)


def delete(**kwargs):
    """
        delete config 
    """
    project = kwargs.get('-project', "")
    domain = kwargs.get('-domain', "")

    if not os.path.isdir(BASE_PATH):
        subprocess.Popen(
            'mkdir {}'.format(BASE_PATH), shell=True, stdout=subprocess.PIPE)

    nginx_conf = os.path.join(BASE_PATH, domain)
    if not os.path.exists(nginx_conf):
        print "File is not exists"; return

    with open(nginx_conf, 'rb') as f:
        tp = f.read().split("# --- divid ---")

    # logic judgment
    if project not in tp[0]:
        print "Error: project not exists"; return
    if project not in tp[2]:
        print "Error: domain path not exists"; return
    if len(filter(lambda x: len(x) > 0, 
                  tp[0].strip().split('upstream'))) <= 1:
        subprocess.Popen(
            'rm {}'.format(nginx_conf), shell=True, stdout=subprocess.PIPE)
        return

    # upstream part
    result = []
    for i in tp[0].split('upstream'):
        if project in i or not i.strip():
            continue
        result.append('  upstream' + i.rstrip() + '\n')

    # server part
    result.append('  # --- divid ---' + tp[1] + '# --- divid ---')

    # location part
    tmp = []
    for i in tp[2].split('location'):
        if project in i or not i.strip():
            continue
        tmp.append('\t  location' + i.rstrip() + '\n')
    result.append(''.join(tmp))

    # final part
    result.append('\t  # --- divid ---' + tp[3])

    # write file
    with open(nginx_conf, 'wb') as f:
        f.write('\n'.join(result))
    # reload nginx
    subprocess.Popen('/usr/local/nginx/sbin/nginx -s reload', shell=True, stdout=subprocess.PIPE)


def sub_content(template, project, ips, domain, domain_path, certificate):
    with open(template, 'rb') as f:
        tp_str = f.read().strip()

    content = re.sub(r'Project', project, tp_str)
    content = re.sub(
        r'server  IpPort max_fails=1 fail_timeout=10s;', ips, content)

    content = re.sub(r'Domain', domain, content)
    if domain_path:
        content = re.sub(r'DPath', domain_path + '/', content)
    else:
        content = re.sub(r'DPath', '', content)

    # if "innertoon.com" in domain:
    #     f_dst3 = re.sub(r' t100SubDomain.innertoon.com','',f_dst5)

    # else:
    #     f_dst3 = re.sub(r'SubDomain', subdomain, f_dst5)

    if certificate:
        content = re.sub(r'Certificate', certificate, content)
    return content


def write_server_config(ip_port):
    content = ''
    for i in ip_port:
        content += '\t' + 'server  ' + i + ' max_fails=1 fail_timeout=10s'+ ';' + '\n'
    return content.lstrip('\t').rstrip('\n')


if __name__ == '__main__':
    cmd = sys.argv[1]
    kwargs = dict([sys.argv[i].split("=") for i in range(2, len(sys.argv))])
    if cmd == '-c':
        create(**kwargs)
    elif cmd == '-d':
        delete(**kwargs)
    else:
        print """
            python other_config.py 
                -cmd (-c create; -d delete)
                -certificate={certificate} 
                -project={project} 
                -domain={domain} 
                -domain_path={domain_path} 
                -ip={ip-multi} 
                -port={port}
            """
