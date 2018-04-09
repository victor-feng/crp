# -*- coding: utf-8 -*-
import paramiko
import subprocess
import time
import requests
import json
from config import APP_ENV, configs


response = {'success': False, 'error': ''}
DNS_CONDIG = configs[APP_ENV].DNS_CONDIG
NAMEDMANAGER_URL = configs[APP_ENV].NAMEDMANAGER_URL
NAMEDMANAGER_HEADERS = {'content-type': 'application/json'}


def domain_name_to_zone(domain_name):
    zone = '.'.join(domain_name.split('.')[-2:])
    path = '/var/named/%s.zone' % zone
    return {'zone':zone,'path':path}

def exchange_domain_to_zone_and_name(domain_name):
    zone = '.'.join(domain_name.split('.')[-2:])
    record_name = '.'.join(domain_name.split('.')[:-2])
    return {'zone':zone,'record_name':record_name}

class ServerError(Exception):
    pass


class DnsShellCmd(object):

    @staticmethod
    def add_cmd(domain_name, ip):
        zone = domain_name_to_zone(domain_name)
        my_record = "%s\.        IN        A        %s\n" % (domain_name, ip)
        cmd = "sed -i  \'$a%s\' %s" % (my_record, zone['path'])
        return cmd

    @staticmethod
    def query_cmd(domain_name):
        zone = domain_name_to_zone(domain_name)
        my_record = '^%s. ' % domain_name
        cmd = "grep \'%s\' %s" % (my_record, zone['path'])
        return cmd

    @staticmethod
    def delete_cmd(domain_name):
        zone = domain_name_to_zone(domain_name)
        my_record = "^%s\. " % domain_name
        cmd = "sed -i  \'/%s/d\' %s" % (my_record, zone['path'])
        return cmd

    @staticmethod
    def reload_cmd():
        cmd = "service named restart"
        return cmd

    @staticmethod
    def zone_add_cmd(domain_name):
        zone = domain_name_to_zone(domain_name)
        cmd1 = "sed 's/syswin.com/%s/g' /var/named/zone.exa >>/etc/named.rfc1912.zones && echo '' || echo 'fail'" % zone['zone']
        cmd2 = "sed 's/syswin.com/%s/g' /var/named/examples.zone >>%s && echo '' || echo 'fail'" % (zone['zone'], zone['path'])
        return [cmd1,cmd2]

    @staticmethod
    def zone_query_cmd(domain_name):
        zone = domain_name_to_zone(domain_name)
        zone_file = "%s.zone" % zone['zone']
        cmd1 = "grep -q \"%s\" /etc/named.rfc1912.zones && echo '' || echo 'fail'" % zone_file
        cmd2 = "[ -f /var/named/%s ] && echo '' || echo 'fail'" % zone_file
        return [cmd1,cmd2]

    @staticmethod
    def modify_serial_cmd(domain_name):
        zone = domain_name_to_zone(domain_name)
        cmd = "sed -i '3c\                                        '$(date +%s)'	     ; serial\' {path}".format(path=zone['path'])
        return cmd


class DnsConfig(object):

    __instance = None

    def __init__(self, host=DNS_CONDIG['host'], port=DNS_CONDIG['port'], username=DNS_CONDIG['username'], password=DNS_CONDIG['password']):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh = None
        self.trans = None

    @classmethod
    def singleton(cls):
        if cls.__instance:
            print "cls exist"
            return cls.__instance
        else:
            cls.__instance = cls()
            print "no cls"
            return cls.__instance

    def connect(self):
        try:
            self.trans = paramiko.Transport((self.host, self.port))
            self.trans.connect(username=self.username, password=self.password)
            self.ssh = paramiko.SSHClient()
            self.ssh._transport = self.trans
        except Exception as e:
            raise ServerError('connect dns server error:%s' % e.message)

    def add(self, domain_name, ip):
        try:
            self.connect()
            cmd = DnsShellCmd.add_cmd(domain_name, ip)
            serial_cmd = DnsShellCmd.modify_serial_cmd(domain_name)
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            stdin1, stdout1, stderr1 = self.ssh.exec_command(serial_cmd)
            result = stderr.read()
            self.close()
            if len(result) == 0:
                response['success'] = True
                response['error'] = 'Add [ %s ] success' % domain_name
            else:
                raise ServerError('Add dns error: %s' % result)
        except Exception as e:
            raise ServerError('Add dns error: %s' % e.message)
        return response

    def query(self, domain_name):
        try:
            self.connect()
            cmd = DnsShellCmd.query_cmd(domain_name)
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            result_err = stderr.read()
            result_out = stdout.read()
            self.close()
            if len(result_err) == 0:
                if len(result_out) == 0:
                    response['success'] = False
                    response['error'] = "no this domain name"
                else:
                    response['success'] = True
                    response['error'] = "[ %s ] is exist" % domain_name
            else:
                raise ServerError('Query Dns Error: %s' % result_err)
        except Exception as e:
            raise ServerError('Query Dns Error: %s' % e.message)
        return response

    def delete(self, domain_name):
        try:
            self.connect()
            cmd = DnsShellCmd.delete_cmd(domain_name)
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            result = stderr.read()
            self.close()
            if len(result) == 0:
                response['success'] = True
                response['error'] = "Delete [ %s ] success" % domain_name
            else:
                raise ServerError('Query Dns Error: %s' % result)
        except Exception as e:
            raise ServerError('Delete Dns Error: %s' % e.message)
        return response

    def reload(self):
        try:
            self.connect()
            cmd = DnsShellCmd.reload_cmd()
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            result = stderr.read()
            print stderr.read()
            self.close()
            if len(result) == 0:
                reload_response = "Dns reload success"
            else:
                raise ServerError('Dns reload error: %s' % result)
        except Exception as e:
            raise ServerError('Dns reload error: %s' % e.message)
        return reload_response

    def zone_query(self,domain_name):
        try:
            self.connect()
            cmd = DnsShellCmd.zone_query_cmd(domain_name)
            stdin1, stdout1, stderr1 = self.ssh.exec_command(cmd[0])
            stdin2, stdout2, stderr2 = self.ssh.exec_command(cmd[1])
            result1 = stdout1.read()
            result2 = stdout2.read()
            self.close()
            if (len(result1) == 1) and (len(result2) == 1):
                response['success'] = True
                response['error'] = "zone is exist"
            else:
                raise ServerError('zone is not exist')
        except Exception as e:
            raise ServerError('Zone Query Error: %s' % e.message)
        return response

    def zone_add(self,domain_name):
        try:
            self.connect()
            cmd = DnsShellCmd.zone_add_cmd(domain_name)
            print cmd[0],cmd[1]
            stdin1, stdout1, stderr1 = self.ssh.exec_command(cmd[0])
            stdin2, stdout2, stderr2 = self.ssh.exec_command(cmd[1])
            result1 = stdout1.read()
            result2 = stdout2.read()
            self.close()
            if (len(result1) == 1) and (len(result2) == 1):
                response['success'] = True
                response['error'] = "zone add success"
            else:
                raise ServerError('zone add error')
        except Exception as e:
            raise ServerError(e.message)
        return response

    def close(self):
        self.trans.close()

class DnsApi(DnsConfig):
    def __init__(self):
        super(DnsConfig, self).__init__()
        self.dns_connect = DnsConfig.singleton()

    def dns_add(self, domain_name, ip):
        try:
            self.dns_connect.zone_query(domain_name=domain_name)
            query_res = self.dns_connect.query(domain_name=domain_name)

            if query_res['success']:
                raise ServerError(query_res.get('error'))

            res = self.dns_connect.add(domain_name=domain_name, ip=ip)
            self.dns_connect.reload()
        except ServerError as e:
            res = e.message
        return res

    def dns_delete(self, domain_name):
        try:
            self.dns_connect.zone_query(domain_name=domain_name)
            query_res = self.dns_connect.query(domain_name=domain_name)

            if not query_res['success']:
                raise ServerError(query_res.get('error'))

            res = self.dns_connect.delete(domain_name=domain_name)
            self.dns_connect.reload()
        except ServerError as e:
            res = e.message
        return res

    def dns_query(self, domain_name):
        try:
            self.dns_connect.zone_query(domain_name=domain_name)
            res = self.dns_connect.query(domain_name=domain_name)
        except ServerError as e:
            res = e.message
        return res


class NamedManagerApi(object):
    def __init__(self,env):
        self.env=env

    def named_zone_query(self,zone_name):
        """
        data格式：
        {"method":"getdomains"}
        :param zone_name:
        :return:
        """
        try:
            data = {"method":"getdomains"}
            url=NAMEDMANAGER_URL.get(self.env)
            rep = requests.post(url, data=json.dumps(data), headers=NAMEDMANAGER_HEADERS)
            ret_json = json.loads(rep.text)
            result = ret_json.get('zone')
            if (result is not None) and (len(result) != 0):
                if zone_name in result:
                    res = zone_name
                else:
                    res = ''
            else:
                raise ServerError('zone list is null')
        except Exception as e:
            raise ServerError(e.message)
        return res

    def named_domain_query(self,domain_name):
        """
        data 格式：
        {"method":"getDns","domain":"syswin.com","recordname":"shulitest"}
        :param domain_name:
        :return:
        """
        try:
            exchange_result = exchange_domain_to_zone_and_name(domain_name)
            domain = exchange_result.get('zone')
            record_name = exchange_result.get('record_name')
            data = {"method":"getDns","domain":domain,"recordname":record_name}
            url = NAMEDMANAGER_URL.get(self.env)
            rep = requests.post(url, data=json.dumps(data), headers=NAMEDMANAGER_HEADERS)
            print rep.text
            ret_json = json.loads(rep.text)
            if ret_json.get('result') == 'success':
                res = ret_json.get('domainip')
            else:
                raise ServerError('domain query error')
        except Exception as e:
            raise ServerError(e.message)
        return res

    def named_domain_add(self,domain_name,domain_ip):
        """
        data格式：
        {"method":"adddns","domain":"syswin.com","recordname":"testgg","hostip":"172.28.31.33"}
        :param domain_name:
        :param domain_ip:
        :return:
        """
        try:
            exchange_result = exchange_domain_to_zone_and_name(domain_name)
            domain = exchange_result.get('zone')
            record_name = exchange_result.get('record_name')
            data = {"method":"adddns","domain":domain,"recordname":record_name,"hostip":domain_ip}
            url = NAMEDMANAGER_URL.get(self.env)
            rep = requests.post(url, data=json.dumps(data), headers=NAMEDMANAGER_HEADERS,timeout=120)
            ret_json = json.loads(rep.text)
            if ret_json.get('result') == 'success':
                res = ret_json.get('content')
            else:
                raise ServerError('add domain error:{message}'.format(message=ret_json.get('message')))
        except Exception as e:
            raise ServerError(e.message)
        return res

    def named_domain_delete(self,domain_name):
        pass

    def named_dns_domain_add(self, domain_name, domain_ip):
        """
        添加的时候做了域是否存在的判断；
        :param domain_name:
        :param domain_ip:
        :return:
        """
        err_msg = None
        try:
            exchange_result = exchange_domain_to_zone_and_name(domain_name)
            domain = exchange_result.get('zone')
            zone_result = self.named_zone_query(zone_name=domain)
            if len(zone_result) != 0:
                self.named_domain_add(domain_name=domain_name,domain_ip=domain_ip)
                res = 'name: {domain_name}, ip: {domain_ip}'.format(domain_name=domain_name,domain_ip=domain_ip)
            else:
                raise ServerError('The zone [{zone_name}] does not exist'.format(zone_name=domain))
        except Exception as e:
            res=None
            err_msg = "dns add namemanager error {e}".format(e=str(e))
        return err_msg,res


if __name__ == '__main__':
    print time.time()
    named_connect = NamedManagerApi()
    #print named_connect.named_zone_query(zone_name='syswin.com')
    #print named_connect.named_domain_query(domain_name='test8.beijing1.com')
    #print named_connect.named_domain_add(domain_name='test8.beijing.com',domain_ip='10.0.0.2')
    print named_connect.named_dns_domain_add(domain_name='yyyyy.sina.com',domain_ip='10.0.0.3')
    #print named_connect.named_domain_query(domain_name='test1.syswin.com')








