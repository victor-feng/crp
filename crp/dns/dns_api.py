# -*- coding: utf-8 -*-
import paramiko
import subprocess
import time

DNS_CONDIG = {
        'host': '172.28.50.141',
        'port': 22,
        'username': 'root',
        'password': '123456'
        }
response = {'success': False, 'error': ''}


def domain_name_to_zone(domain_name):
    zone = '.'.join(domain_name.split('.')[-2:])
    path = '/var/named/%s.zone' % zone
    return {'zone':zone,'path':path}



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

if __name__ == '__main__':
    print time.time()
    dns_api = DnsApi()
    name = raw_input('please input:').strip()
    #print dns_api.dns_query(domain_name=name)
    print dns_api.dns_add(domain_name=name, ip='192.168.70.130')
    #print dns_api.dns_delete(domain_name=name)
    #print dns_api.dns_query(domain_name=name)
    #print dns_connect.add(domain_name=name, ip='192.168.70.130')
    #print dns_connect.query(domain_name=name)
    #print dns_connect.delete(domain_name=name)
    #print dns_connect.reload()
    #time.sleep(50)
    #dns_connect.close()
    print time.time()








