# -*- coding: utf-8 -*-
import threading
import subprocess
import os
import time
import json
from crp.log import Log


def async(fun):
    def wraps(*args, **kwargs):
        thread = threading.Thread(target=fun, args=args, kwargs=kwargs)
        thread.daemon = False
        thread.start()
        return thread
    return wraps



def exec_cmd_ten_times(ip,cmd,sleep):
    """
    执行ansiable 命令的公共函数 ，命令执行不成功再 执行10次退出
    :param ip:
    :param cmd:
    :param sleep:
    :return:
    """
    try:
        check_cmd="cat /etc/ansible/hosts | grep %s | wc -l" % ip
        res=os.popen(check_cmd).read().strip()
        #向ansible配置文件中追加ip，如果存在不追加
        if int(res) == 0:
            with open('/etc/ansible/hosts', 'a+') as f:
                f.write('%s\n' % ip)
        for i in range(10):
            time.sleep(sleep)
            p = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
            stdout=p.stdout.read()
            if "SUCCESS" in stdout:
                Log.logger.debug(stdout)
                break
        else:
            Log.logger.debug(stdout)
            Log.logger.debug('execute %s %s cmd 10 times failed'% (ip,cmd))
    except Exception as e:
        err_msg=str(e.args)
        Log.logger.error("CRP exec_db_service error ,error msg is:%s" %err_msg)

def exec_cmd_one_times(ip,cmd):
    """
    执行ansiable 命令的公共函数，只执行一次
    :param ip:
    :param cmd:
    :param sleep:
    :return:
    """
    try:
        check_cmd="cat /etc/ansible/hosts | grep %s | wc -l" % ip
        res=os.popen(check_cmd).read().strip()
        #向ansible配置文件中追加ip，如果存在不追加
        if int(res) == 0:
            with open('/etc/ansible/hosts', 'a+') as f:
                f.write('%s\n' % ip)
        p = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        stdout=p.stdout.read()
        Log.logger.debug(stdout)
        return p
    except Exception as e:
        err_msg=str(e.args)
        Log.logger.error("CRP exec_db_service error ,error msg is:%s" %err_msg)

def get_k8s_err_code(err):
    try:
        code = json.loads(err.body).get("code")
        return code
    except Exception as e:
        return 4444
