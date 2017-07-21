# -*- coding: utf-8 -*-
import paramiko
import subprocess
import time

DNS_CONDIG = {
        'host': '172.28.50.141',
        'port': 22,
        'username': 'root',
        'password': '123456',
        'domain_path': '/var/named/syswin.com.zone',
        'rndc_path': '/usr/sbin/rndc'
        }
response = {'success': False, 'error': ''}


class ServerError(Exception):
    pass


class DnsConfig(object):

    __instance = None

    def __init__(self, host=DNS_CONDIG['host'], port=DNS_CONDIG['port'], username=DNS_CONDIG['username'], password=DNS_CONDIG['password'], path=DNS_CONDIG['domain_path']):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.path = path
        self.ssh = None
        self.trans = None

    @classmethod
    def singleton(cls):
        if cls.__instance:
            return cls.__instance
        else:
            cls.__instance = cls()
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
        my_record = "%s\.        IN        A        %s\n" % (domain_name, ip)
        cmd = "sed -i  \'$a%s\' %s" % (my_record, self.path)
        try:
            self.connect()
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            result = stderr.read()
            self.close()
            if len(result) == 0:
                response['success'] = True
                response['error'] = 'Add [ %s ] success!' % domain_name
            else:
                raise ServerError('Add dns error: %s' % result)
        except Exception as e:
            raise ServerError('Add dns error: %s' % e.message)
        return response

    def query(self, domain_name):
        my_record = '^%s. ' % domain_name
        cmd = "grep \'%s\' %s" % (my_record, self.path)
        try:
            self.connect()
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
        my_record = "^%s\. " % domain_name
        cmd = "sed -i  \'/%s/d\' %s" % (my_record, self.path)
        try:
            self.connect()
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
            rndc_path = DNS_CONDIG['rndc_path']
            rndc_cmd = "%s -s %s reload >/dev/null" % (rndc_path, self.host)
            retcode = subprocess.call(rndc_cmd, shell=True)
            if retcode != 0:
                raise ServerError('Dns reload failed!')
            else:
                reload_response = 'Dns reload success'
        except Exception as e:
            raise ServerError('Dns reload error: %s' % e.message)
        return reload_response

    def close(self):
        self.trans.close()


if __name__ == '__main__':
    dns_connect = DnsConfig.singleton()
    name = raw_input('please input:').strip()
    print dns_connect.add(domain_name=name, ip='192.168.70.130')
    print dns_connect.query(domain_name=name)
    print dns_connect.delete(domain_name=name)
    #time.sleep(50)
    #dns_connect.close()








