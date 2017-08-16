# -*- coding: utf-8 -*-

""" A script fo create mongo cluster.
"""

import os
import json
import logging
import subprocess

from tornado.options import define, options

class MongodbCluster(object):

    def __init__(self, ip_list):
        """
        :param: list
            [
                '172.28.32.60', # slave_ip
                '172.28.32.58', # slave_ip
                '172.28.32.58', # master_ip
            ]
        """
        self.dir = os.path.dirname(os.path.abspath(__file__)) + '/' + 'mongo_script'
        self.ip_slave1 = ip_list[0]
        self.ip_slave2 = ip_list[1]
        self.ip_master1 = ip_list[2]
        self.ip_master2 = ip_list[3]
        self.d = {
            self.ip_slave1: 'mongoslave1.sh',
            self.ip_slave2: 'mongoslave2.sh',
            self.ip_master1: 'mongomaster1.sh',
            }
        self.cmd = ['ansible {vip} -u root --private-key={rsa_dir}/old_id_rsa -m script -a '
                    '"{dir}/mongomaster2.sh sys95"'.format(vip=self.ip_master2, rsa_dir=self.dir, dir=self.dir)]
        self.ip = [self.ip_slave1, self.ip_slave2, self.ip_master1]
        self.new_host = '[new_host]'
        self.write_ip_to_server()
        self.flag = False
        self.telnet_ack()

    def write_ip_to_server(self):
        for ip in self.ip:
            with open('/etc/ansible/hosts', 'a') as f:
                f.write('%s\n' % ip)

    def telnet_ack(self):
        while not self.flag:
            for ip in self.ip:
                p = subprocess.Popen('nmap %s -p 22' % str(ip), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                try:
                    a = p.stdout.readlines()[5]
                except IndexError as e:
                    logging.exception("[MISC] telnet_ack faild, Exception: %s", e.args)
                    a = 'false'
                    break
                if 'open' in a:
                    self.mongodb_cluster_push(ip)
                    self.ip.remove(ip)
            if len(self.ip) == 0:
                self.flag = True

    def mongodb_cluster_push(self, ip):
        # vip_list = list(set(self.ip))
        # vip_list = [ip_master1, ip_slave1, ip_slave2]
        script_name = ['mongoslave1.sh', 'mongoslave2.sh', 'mongomaster1.sh', 'mongomaster2.sh', 'old_id_rsa']
        for i in script_name:
            os.system('chmod 600 {dir}'.format(dir=self.dir + '/' + i))
        #cmd_before = "ansible {vip} --private-key={dir}/old_id_rsa -m synchronize -a 'src=/opt/uop-crp/crp/res_set/" \
        cmd_before = "ansible {vip} --private-key={dir}/old_id_rsa -m synchronize -a 'src=" \
                     "write_mongo_ip.py dest=/tmp/'".format(vip=ip, dir=self.dir)
        logging.info("[MISC] cmd_before: %s", cmd_before)
        authority_cmd = 'ansible {vip} -u root --private-key={dir}/old_id_rsa -m shell -a ' \
                        '"chmod 777 /tmp/write_mongo_ip.py"'.format(vip=ip, dir=self.dir)
        logging.info("[MISC] authority_cmd: %s", authority_cmd)
        cmd1 = 'ansible {vip} -u root --private-key={dir}/old_id_rsa -m shell -a "python /tmp/write_mongo_ip.py' \
               ' {m_ip} {s1_ip} {s2_ip}"'.format(vip=ip, dir=self.dir, m_ip=self.ip_master1, s1_ip=self.ip_slave1, s2_ip=self.ip_slave2)
        logging.info("[MISC] cmd1: %s", cmd1)
        p = subprocess.Popen(cmd_before, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            logging.debug("[MISC] line: %s", line)
        p = subprocess.Popen(authority_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            logging.debug("[MISC] line: %s", line)
        p = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            logging.debug("[MISC] line: %s", line)
        # for ip in self.ip:
        with open('/tmp/hosts', 'w') as f:
            f.write('%s\n' % ip)
        script = self.d.get(ip)
        # if str(ip) != '172.28.36.105':
        cmd_s = 'ansible {vip} -u root --private-key={rsa_dir}/old_id_rsa -m script -a "{dir}/{s} sys95"'.\
                format(vip=ip, rsa_dir=self.dir, dir=self.dir, s=script)
        logging.info("[MISC] cmd_s: %s", cmd_s)

        # else:
        #     cmd_s = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/
        # mongoclu_install/{s}"'.format(vip=ip, s=script)
        p = subprocess.Popen(cmd_s, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            logging.debug("[MISC] line: %s", line)

    def exec_final_script(self):
        """Main method.
        """
        for i in self.cmd:
            p = subprocess.Popen(i, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                logging.debug("[MISC] line: %s", line)


if __name__ == '__main__': 
    options.parse_command_line()

    logging.info('create mongo cluster')
    lst = [ '172.28.36.157',
           '172.28.36.156',
           '172.28.36.155',
           '172.28.36.155',
           ]
    mc = MongodbCluster(lst)
    mc.exec_final_script()

