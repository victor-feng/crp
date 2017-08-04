# -*- coding: utf-8 -*-
import logging
import json
import commands
import os
import time
import uuid
import paramiko
import ansible.runner
import ansible.playbook
import ansible.inventory
from ansible import callbacks
from ansible import utils


class ServerError(Exception):
    pass

class AnsibleDeployApi(object):
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def deploy_exec_command(self):
        pass






class ParamikoDeployApi(object):
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.trans = None
        self.ssh = None
        self.sftp = None
        self.connect()


    def connect(self):
        self.trans = paramiko.Transport((self.host, self.port))
        self.trans.connect(username=self.username, password=self.password)

    def ssh_instance(self):
        self.ssh = paramiko.SSHClient()
        self.ssh._transport = self.trans

    def sftp_instance(self):
        self.sftp = paramiko.SFTPClient.from_transport(self.trans)

    def deploy_command(self, cmd):
        try:
            self.ssh_instance()
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
        except Exception as e:
            raise ServerError(e.message)
        return stdout.read().decode().strip()


    def deploy_get(self, remotepath, localpath):
        try:
            self.sftp_instance()
            self.sftp.get(remotepath, localpath)
        except Exception as e:
            raise ServerError(e.message)
        return "download from {remotepath} to {localpath} is success".format(remotepath=remotepath, localpath=localpath)

    def deploy_put(self, localpath, remotepath):
        try:
            self.sftp_instance()
            self.sftp.get(localpath, remotepath)
        except Exception as e:
            raise ServerError(e.message)
        return "upload from {remotepath} to {localpath} is success".format(remotepath=remotepath, localpath=localpath)

    def connect_close(self):
        self.trans.close()


if __name__ == '__main__':
    deploy_instance = ParamikoDeployApi(host='192.168.70.138', port=22, username='root', password='123456')
    cmd = ''
    print deploy_instance.deploy_command(cmd)
    #print deploy_instance.deploy_get('/root/hello.py', '/root/20170728.py')
    deploy_instance.connect_close()