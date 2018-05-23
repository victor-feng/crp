# -*- coding: utf-8 -*-
import threading
import subprocess
import os
import time
import json
import re
from crp.log import Log



def async(fun):
    def wraps(*args, **kwargs):
        thread = threading.Thread(target=fun, args=args, kwargs=kwargs)
        thread.daemon = False
        thread.start()
        return thread
    return wraps


def isopenrc(rc_path,res):
    def _deco(func):
        def wrapper(*args, **kwargs):
            if rc_path:
                ret=func(*args, **kwargs)
            else:
                ret = res
            return  ret
        return wrapper
    return _deco


def exec_cmd_ten_times(ip,cmd,sleep):
    """
    执行ansiable 命令的公共函数 ，命令执行不成功再 执行10次退出
    :param ip:
    :param cmd:
    :param sleep:
    :return:
    """
    exec_flag = True
    err_msg = None
    out = ""
    try:
        check_cmd="cat /etc/ansible/hosts | grep  -w '%s' | wc -l" % ip
        res=os.popen(check_cmd).read().strip()
        #向ansible配置文件中追加ip，如果存在不追加
        Log.logger.debug("Check cmd is{check_cmd} res is{res}".format(check_cmd=check_cmd,res=res))
        if int(res) == 0:
            with open('/etc/ansible/hosts', 'a+') as f:
                f.write('%s\n' % ip)
        for i in range(10):
            time.sleep(sleep)
            flag=check_remote_host(ip)
            if not flag:continue
            stdout=exec_cmd(cmd)
            out = out + ','+ stdout
            if "SUCCESS" in stdout:
                Log.logger.debug(cmd)
                Log.logger.debug(stdout)
                break
        else:
            stdout = out.split(',')[-1] if out.split(',') else ''
            err_msg = 'execute %s %s cmd 10 times failed %s'% (ip,cmd,stdout)
            exec_flag = False
            Log.logger.debug(err_msg)
    except Exception as e:
        exec_flag = False
        err_msg=str(e)
        Log.logger.error("CRP exec_db_service error ,error msg is:%s" %err_msg)
    return exec_flag,err_msg

def exec_cmd_one_times(ip,cmd):
    """
    执行ansiable 命令的公共函数，只执行一次
    :param ip:
    :param cmd:
    :param sleep:
    :return:
    """
    try:
        check_cmd="cat /etc/ansible/hosts | grep -w '%s' | wc -l" % ip
        res=os.popen(check_cmd).read().strip()
        #向ansible配置文件中追加ip，如果存在不追加
        if int(res) == 0:
            with open('/etc/ansible/hosts', 'a+') as f:
                f.write('%s\n' % ip)
        stdout=exec_cmd(cmd)
        Log.logger.debug(stdout)
        return stdout
    except Exception as e:
        err_msg=str(e.args)
        Log.logger.error("CRP exec_db_service error ,error msg is:%s" %err_msg)

def get_k8s_err_code(err):
    try:
        code = json.loads(err.body).get("code")
        return code
    except Exception as e:
        return 4444

def response_data(code, msg, data):
    ret = {
        'code': code,
        'result': {
            'msg': msg,
            'data': data,
        }
    }
    return ret


def check_remote_host(ip):
    try:
        cmd = "nmap %s -p 22" % ip
        res=exec_cmd(cmd)
        if "open" in res:
            flag=True
        else:
            flag=False
    except Exception as e:
        flag=False
    Log.logger.debug("Check remote host %s is %s" % (ip,str(flag)))
    return flag

def exec_cmd(cmd):
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    stdout = p.stdout.read()
    return stdout
