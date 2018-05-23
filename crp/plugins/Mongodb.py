# coding=utf8
import os
import time
import subprocess
from crp.log import Log
from crp.plugins.BasePlugin import BasePlugin
from config import APP_ENV, configs

class MongodbCluster(BasePlugin):

    def __init__(self, ip_list, version):
        """
        172.28.36.230
        172.28.36.23
        172.28.36.231
        :param cmd_list:
        """
        BasePlugin.__init__(self, version)
        self.dir = os.path.dirname(
            os.path.abspath(__file__)) + '/' + 'mongo_script'
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.ip_slave1 = ip_list[0]
        self.ip_slave2 = ip_list[1]
        self.ip_master1 = ip_list[2]
        self.ip_master2 = ip_list[3]
        self.d = {
            self.ip_slave1: 'mongoslave1.sh',
            self.ip_slave2: 'mongoslave2.sh',
            self.ip_master1: 'mongomaster1.sh',
        }
        self.cmd = [
            'ansible {vip} -u root --private-key={rsa_dir}/old_id_rsa -m script -a '
            '"{dir}/mongomaster2.sh {db_name}"'.format(
                vip=self.ip_master2,
                rsa_dir=self.dir,
                dir=self.dir,
                db_name=configs[APP_ENV].MONGODB_NAME)]
        self.ip = [self.ip_slave1, self.ip_slave2, self.ip_master1]
        self.new_host = '[new_host]'
        self.write_ip_to_server()
        self.flag = False
        self.telnet_ack()

    def write_ip_to_server(self):
        for ip in self.ip:
            check_cmd = "cat /etc/ansible/hosts | grep %s | wc -l" % ip
            res = os.popen(check_cmd).read().strip()
            # 向ansible配置文件中追加ip，如果存在不追加
            if int(res) == 0:
                with open('/etc/ansible/hosts', 'a+') as f:
                    f.write('%s\n' % ip)

    def telnet_ack(self):
        start_time = time.time()
        while not self.flag:
            for ip in self.ip:
                time.sleep(3)
                p = subprocess.Popen(
                    'nmap %s -p 22' %
                    str(ip),
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                try:
                    a = p.stdout.read()
                    Log.logger.debug('nmap ack  %s result:%s' % (ip,a))
                except IndexError as e:
                    a = 'false'
                    Log.logger.debug('%s' % e)
                    break
                if 'open' in a:
                    self.mongodb_cluster_push(ip)
                    self.ip.remove(ip)
            end_time = time.time()
            if start_time - end_time > 180:
                break
            if len(self.ip) == 0:
                self.flag = True

    def mongodb_cluster_push(self, ip):
        # vip_list = list(set(self.ip))
        # vip_list = [ip_master1, ip_slave1, ip_slave2]
        script_name = [
            'mongoslave1.sh',
            'mongoslave2.sh',
            'mongomaster1.sh',
            'mongomaster2.sh',
            'old_id_rsa']
        for i in script_name:
            os.system('chmod 600 {dir}'.format(dir=self.dir + '/' + i))
        cmd_before = "ansible {vip} --private-key={dir}/old_id_rsa -m synchronize -a 'src={current_dir}/" \
                     "write_mongo_ip.py dest=/tmp/'".format(vip=ip, dir=self.dir, current_dir=self.current_dir)
        authority_cmd = 'ansible {vip} -u root --private-key={dir}/old_id_rsa -m shell -a ' \
                        '"chmod 777 /tmp/write_mongo_ip.py"'.format(vip=ip, dir=self.dir)
        cmd1 = 'ansible {vip} -u root --private-key={dir}/old_id_rsa -m shell -a "python /tmp/write_mongo_ip.py' \
               ' {m_ip} {s1_ip} {s2_ip}"'.format(vip=ip, dir=self.dir, m_ip=self.ip_master1, s1_ip=self.ip_slave1, s2_ip=self.ip_slave2)
        Log.logger.debug('开始上传脚本%s' % ip)
        p = subprocess.Popen(
            cmd_before,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        Log.logger.debug('mongodb cluster cmd before:%s' % p.stdout.read())
        Log.logger.debug('开始修改权限%s' % ip)
        p = subprocess.Popen(
            authority_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        Log.logger.debug('mongodb cluster authority:%s' % p.stdout.read())
        Log.logger.debug('脚本上传完成,开始执行脚本%s' % ip)
        p = subprocess.Popen(
            cmd1,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        Log.logger.debug('mongodb cluster exec write script:%s' % p.stdout.read())
        Log.logger.debug('脚本执行完毕 接下来会部署%s' % ip)
        # for ip in self.ip:
        with open('/tmp/hosts', 'w') as f:
            f.write('%s\n' % ip)
        print '-----', ip, type(ip)
        script = self.d.get(ip)
        cmd_s = 'ansible {vip} -u root --private-key={rsa_dir}/old_id_rsa -m script -a "{dir}/{s} {db_name}"'.\
                format(vip=ip, rsa_dir=self.dir, dir=self.dir, s=script, db_name=configs[APP_ENV].MONGODB_NAME)
        p = subprocess.Popen(
            cmd_s,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        Log.logger.debug(
                'mongodb cluster push result:%s, -----%s' %
                (p.stdout.read(), ip))

    def exec_final_script(self):
        for i in self.cmd:
            p = subprocess.Popen(
                i,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            Log.logger.debug('mongodb cluster push result:%s' % p.stdout.read())

    def push(self, *args, **kwargs):
        ip = kwargs["ip"]
        self.mongodb_cluster_push(ip)

    def info(self, *args, **kwargs):
        pass

    def verify(self, *args, **kwargs):
        self.telnet_ack()
        pass

