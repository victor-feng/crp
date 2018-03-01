# -*- coding: utf-8 -*-
#!/urs/bin/python
__author__ = 'wangyanzy'

import sys,os
import subprocess
import urllib2
import json,demjson
import time
import shutil
import re
import logging
from ftplib import FTP

from BeautifulSoup import BeautifulSoup;

ansible_warpath = '/etc/ansible/war'
inventory_path = '/etc/ansible/inventory/wardeploy'

blocker_sta = 0
critical_sta = 20

def send_http_request(url):
    if not url:
        return "error"
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.151 Safari/534.16')
    try:
        response = urllib2.urlopen(req,timeout=3)
    except Exception, e:
        return e
    result = response.read()
    try:
        return json.loads(result)
    except:
        return result

if sys.argv[1] not in ['dev','test','press','preProduction','payself']:
    print "请输入环境参数: eg,dev,test,press"
    exit(1)
env = sys.argv[1]
prodir = ''
if len(sys.argv) > 2:
    prodir = sys.argv[2]

target_dir = os.path.join(prodir,'target')
for item in os.listdir(target_dir):
    if '.war' in item:
        prname = item.split('.')[0]
print 'prname:', prname


# if env in ['dev','test']:
if env in ['xxxx111111']:
    dict_pro = {}
    try:
        for item in send_http_request('http://172.28.4.60:9000/api/projects'):
            dict_pro[item['nm']] = item['k']
        print 'sonarPRname:', dict_pro[prname]
    except Exception as e:
        print('请修改pom文件中name属性为工程名')
        exit(1)

    u_url = 'http://172.28.4.60:9000/dashboard/index/%s'
    html = send_http_request(u_url % dict_pro[prname])
    soup = BeautifulSoup(html)

    # 统计代码覆盖率
    try:
        coverage = soup.find('span', id="m_coverage").text[:-1]
    except:
        coverage = None

    # 统计单元测试成功率
    try:
        suc_density = soup.find('span', id="m_test_success_density").text[:-1]
    except:
        suc_density = None

    # 统计代码质量检测结果: 阻断 严重 主要
    blocker = soup.find('span', id="m_blocker_violations").text
    critical = soup.find('span', id="m_critical_violations").text
    major = soup.find('span', id="m_major_violations").text

    print '\n'+'#'*100
    print 'sonar代码质量检查结果如下:\n代码阻断(合格率: %s):' % blocker_sta, blocker
    print '严重问题(合格率: %s):' % critical_sta, critical
    print '主要错误(自行修改吧):', major+'\n'
    print "请点击sonar链接查看问题:\n", u_url % dict_pro[prname]
    print '\n'

    if (int(blocker) > blocker_sta) or (int(critical) > critical_sta): # or (int(major) >= 150):
        print "代码质量检测不过关涅!!!"
        print "改代码去吧，亲!!!!\n"+'#'*100+'\n'
        exit(1)

#其他环境压测环境和预生产环境
# 显示拷贝war包
prowar = os.path.join(prodir,'target',prname+'.war')
destwar = os.path.join(ansible_warpath, prname+'_'+env+'.war')

shutil.copy(prowar, destwar)

# 执行ansible命令部署应用
ansible_inventory = os.path.join(inventory_path,prname+'_'+env)

ansible_cmd = 'ansible-playbook -i {ansible_inventory} /etc/ansible/roles/wardeploy.yml --private-key=/home/jenkins/.ssh/id_rsa_java_new -e hosts={prname} -t update'.format(
    ansible_inventory=ansible_inventory,
    prname=prname)

print '#'*100
print 'ansible_cmd:', ansible_cmd

p = subprocess.Popen(ansible_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
ret_out = p.stdout.read()
ret_err = p.stderr.read()

failed = 0
if ret_err:
    print 'ERROR'
    print ret_err
    exit(1)
else:
    print 'ansible 部署结果:'
    print ret_out

    ret_li = ret_out.split('TASK')
    for item in ret_li:
        if 'failed:' in item or 'fatal:' in item:
            if 'ignoring' not in item:
                failed = 1

# 查看远程服务器catalina.out输出结果
log_cmd = 'ansible all -i {ansible_inventory}  --private-key=/home/jenkins/.ssh/id_rsa_java_new -u java -m shell -a "cat /home/java/catalina.out"'.format(
    ansible_inventory=ansible_inventory,
    )

plog = subprocess.Popen(log_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print '#'*100
log_out = plog.stdout.read()
log_err = plog.stderr.read()

if log_err:
    print 'ERROR:'
    print log_err
else:
    print 'catalina.out输出结果:'
    print log_out

print 'failed:',failed
if failed:
    exit(1)



if env == 'test':
    # 将war包传给吕杰185服务器
    #scm_cmd = 'scp -P 50022 {destwar} wanggang@10.253.68.185:/home/wanggang/prewar/{prname}.war'.format(destwar=destwar,prname=prname)
    #os.system(scm_cmd)

    # 将war包上传到ftp服务器
    BUILD_NUMBER = os.getenv('BUILD_NUMBER')
    BUILD_TIMESTAMP = os.getenv('BUILD_TIMESTAMP')
    str_build =  '%s_n%s' % (BUILD_TIMESTAMP, BUILD_NUMBER)

    ftp_host = '172.28.26.210'
    ftp_user = 'ftpuser'
    ftp_passwd = 'syswin#123'
    try:
        ftp = FTP(host=ftp_host, user=ftp_user, passwd=ftp_passwd)
        base_dir = '/data/ftpdata/'+env
        ftp.cwd(base_dir)

        if prname in ftp.nlst():
            pass
            # print '%s Folder already exists' % prname
        else:
            ftp.mkd(prname)

        pathname = os.path.join(base_dir, prname, str_build)
        ftp.mkd(pathname)
        ftp.cwd(pathname)

        print pathname;
        f = open(prowar, "rb")
        ftp.storbinary('STOR %s.war' % prname , f, 1024)
        f.close()
    except:
        print '上传ftp失败'
        exit(1)

    http_str = os.path.join(prname, str_build,prname)
    ftp_link = '%s%s.war' % ('http://toonpak.toon.mobi/'+env+'/', http_str)

    print '\033[1;31;47m'
    print '################# war包连接地址: #############'
    print '#\n#', ftp_link
    print '#\n###########################################'
    print '\033[0m'


