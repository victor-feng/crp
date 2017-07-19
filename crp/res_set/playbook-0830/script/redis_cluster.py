#!/usr/bin/env python
# -*- coding:utf8 -*-
"""
主从redis,keepalived作高可用
请在env.ini中提前配置好一些变量
使用方法
python xxx/redis_cluster.py ip1 ip2 vip
2个ip + 一个虚拟ip作为vip
可以重复执行
"""
__author__ = 'wangyan'

import os,sys
import re
import random
import subprocess
import time
import ConfigParser

# ./playbook目录
play_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
envini = os.path.join(play_dir,'script/env.ini')
inventory_dir = os.path.join(play_dir, 'roles/inventory')
inv_file = os.path.join(inventory_dir,'hosts_redis')
yml_file = os.path.join(play_dir,'roles/redis/redis.yml')

# 获取配置文件env.ini中用户名，key，kafka参数等
conf = ConfigParser.ConfigParser()
conf.read(envini)

try:
    username = conf.get('ansibleuser','username')
    userkey = conf.get('ansibleuser','userkey')
    redis_version = conf.get('redis','redis_version')
    redis_port = conf.get('redis','redis_port')
    network_eth = conf.get('redis','network_eth')
    print username, userkey, redis_version, redis_port,network_eth
except:
    print '配置文件参数不足，请在env.ini中配置相关变量'
    exit(1)

print sys.argv

# 传输三个ip参数
if len(sys.argv) < 4:
    print('请输入主从服务器IP和虚拟IP...')
    sys.exit(1)

# 配置redis hostsfile
redis_master_ip = sys.argv[1]
redis_slave_ip = sys.argv[2]
redis_vip_ip = sys.argv[3]

# 设置keepalived的virtualrouterid
routerID=random.randint(0,255)

redis_template = os.path.join(inventory_dir,'hosts_redis_template')
with open(redis_template,'r') as f:
    redis_str = f.read()

redis_str_new = redis_str.format(redis_master_ip=redis_master_ip,
                 redis_slave_ip=redis_slave_ip,
                 redis_vip_ip=redis_vip_ip,
                 routerID=routerID,
                 network_eth=network_eth,
                 redis_port=redis_port,
                 redis_version=redis_version,
                 )


with open(inv_file, 'w') as f:
    f.write(redis_str_new)

# 执行ansible命令
ansible_cmd = 'ansible-playbook --private-key={userkey} -i {inv_file} -u {username} {yml_file}'.format(
    inv_file=inv_file, userkey=userkey, username=username, yml_file=yml_file)

print 'ansible_cmd:', ansible_cmd

p = subprocess.Popen(ansible_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
outstr = p.stdout.read()
errstr = p.stderr.read()

if outstr:
    print 'stdourt:\n',outstr
else:
    print 'Error:\n', errstr