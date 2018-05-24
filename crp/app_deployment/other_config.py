#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys,os
import re
import subprocess
import ast
from jinja2 import Environment, FileSystemLoader

BASE_PATH = "/usr/local/nginx/conf/servers_systoon"
TEMPLATE_PATH = "/tmp"
# BASE_PATH = "/home/mcq/tlp"
# TEMPLATE_PATH = "/home/mcq/tlp"


class Params(object):
    """
        参数
    """
    def __init__(self, domain, project, ips, 
                        dpath=None, template=None, certificate=None):
        self.domain = domain
        self.project = project
        self.ips = ips if isinstance(ips, list) else [ips]
        self.dpath = '/' + dpath.strip('/') + '/' if dpath.strip('/') else '/'
        self.template = template
        self.certificate = certificate


def cover_temp(domain, objs, conf_path):
    """
        写配置文件
    """
    if not isinstance(objs, list):
        objs = [objs]

    env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
    t = env.get_template(objs[0].template)
    content = t.render(domain=domain, objs=objs)

    content_list = content.split('\n')
    txt = [i for i in content_list if i.strip()]

    with open(conf_path, 'wb') as f:
        f.write('\n'.join(txt))


def update_or_extend(new_obj, conf_path):
    """
        更新或扩展
    """
    with open(conf_path, 'rb') as f:
        content_list = f.read().split('#<Necessary>')

    old_objs = []
    for i in range(1, len(content_list)):
        old_objs.append(Params(**ast.literal_eval(content_list[i].strip())))

    for index, obj in enumerate(old_objs):
        if new_obj.project == obj.project:
            del old_objs[index]
            break

    old_objs.append(new_obj)
    
    cover_temp(new_obj.domain, old_objs, conf_path)


def remove(del_obj, conf_path):
    with open(conf_path, 'rb') as f:
        content_list = f.read().split('#<Necessary>')

    old_objs = []
    for i in range(1, len(content_list)):
        old_objs.append(Params(**ast.literal_eval(content_list[i].strip())))

    if len(old_objs) < 2 and old_objs[0].project == del_obj.project:
        subprocess.Popen(
            'rm {conf}'.format(conf=conf_path), shell=True, stdout=subprocess.PIPE)
        return

    for index, obj in enumerate(old_objs):
        if del_obj.project == obj.project:
            del old_objs[index]

    cover_temp(del_obj.domain, old_objs, conf_path)


def get_obj(**kwargs):
    """
        参数实例化
    """
    certificate = kwargs.get('-certificate', "")
    project = kwargs.get('-project', "") + ".com"
    domain = kwargs.get('-domain', "")
    domain_path = kwargs.get('-domain_path', "")
    ip_list = kwargs.get('-ip', "").split(",")
    port = kwargs.get('-port', 80)

    ips = ['{i}:{port}'.format(i=i, port=port) for i in ip_list]

    template = 'other_template_https' if certificate else 'other_template_http'

    obj = Params(domain, project, ips, domain_path, template, certificate)
    return obj


def create(**kwargs):
    obj = get_obj(**kwargs)
    # dir
    if not os.path.isdir(BASE_PATH):
        subprocess.Popen(
            'mkdir {path}'.format(path=BASE_PATH), shell=True, stdout=subprocess.PIPE)

    nginx_conf = os.path.join(BASE_PATH, obj.domain)

    if os.path.exists(nginx_conf):
        update_or_extend(obj, nginx_conf)
    else:
        cover_temp(domain, obj, nginx_conf)


def delete(**kwargs):
    del_obj = get_obj(**kwargs)
    nginx_conf = os.path.join(BASE_PATH, del_obj.domain)

    if not os.path.exists(nginx_conf):
        print "File is not exists"; return

    remove(del_obj, nginx_conf)


if __name__ == '__main__':
    cmd = sys.argv[1]
    kwargs = dict([sys.argv[i].split("=") for i in range(2, len(sys.argv))])

    # domain exists
    domain = kwargs.get('-domain', '')
    nginx_conf = os.path.join(BASE_PATH, domain)
    if os.path.exists(nginx_conf):
        with open(nginx_conf, 'rb') as f:
            fp = f.read()
        my_domain = re.findall(r'#<Necessary>', fp, flags=re.M)
        assert my_domain, "Domain already existed in {p},used in k8s app".format(p=BASE_PATH)

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
