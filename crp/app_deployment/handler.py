# -*- coding: utf-8 -*-

import time
import subprocess
from crp.openstack import OpenStack
from crp.taskmgr import *
from crp.log import Log
from crp.disconf.disconf_api import *
from crp.utils.aio import exec_cmd_ten_times
from config import APP_ENV, configs

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


DEP_STATUS_CALLBACK = configs[APP_ENV].DEP_STATUS_CALLBACK
OS_DOCKER_LOGS = configs[APP_ENV].OS_DOCKER_LOGS
SCRIPTPATH = configs[APP_ENV].SCRIPTPATH
UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER

def _dep_callback(deploy_id,ip,res_type,msg,vm_state,success,cluster_name,end_flag,deploy_type,unique_flag,cloud=None,deploy_name=None,o_domain=None,o_port=None,domain_flag=None):
    """
    将部署的状态和日志，以及错误信息回调给uop
    :param deploy_id:
    :param ip:
    :param res_type:
    :param err_msg:
    :param vm_state:
    :param success:
    :param cluster_name:
    :param end_flag:
    :param deploy_type:
    :return:
    """
    data = dict()
    data["ip"]=ip
    data["res_type"]=res_type
    data["msg"] = msg
    data["vm_state"] = vm_state
    data["cluster_name"] = cluster_name
    data["end_flag"] = end_flag
    data["deploy_type"] = deploy_type
    data["unique_flag"] = unique_flag
    data["cloud"] = cloud
    data["o_domain"] = o_domain
    data["deploy_name"] = deploy_name
    data["o_port"] = o_port
    data["domain_flag"] = domain_flag
    if success:
        data["result"] = "success"
    else:
        data["result"] = "fail"
    data_str = json.dumps(data)

    headers = {'Content-Type': 'application/json'}
    Log.logger.debug("data string:" + str(data))
    CALLBACK_URL = configs[APP_ENV].UOP_URL + 'api/dep_result/'
    Log.logger.debug("[CRP] _dep_callback callback_url: %s ", CALLBACK_URL)
    res = requests.put(CALLBACK_URL + deploy_id + "/", data=data_str, headers=headers)
    Log.logger.debug("call dep_result callback,res: " + str(res))
    return res


def _dep_detail_callback(deploy_id,deploy_type,set_flag,deploy_msg=None):
    """
    将部署的日志和状态回调给uop
    :param deploy_id:
    :param deploy_type:
    :param set_flag:
    :param deploy_msg:
    :return:
    """
    data = {
        "deploy_id":deploy_id,
        "deploy_type":deploy_type,
        "deploy_msg":deploy_msg,
        "status":"ok",
        "set_flag": set_flag,
    }
    
    data_str = json.dumps(data)

    headers = {'Content-Type': 'application/json'}
    Log.logger.debug("data string:" + str(data))
    Log.logger.debug("[CRP] _dep_detail_callback callback_url: %s ", DEP_STATUS_CALLBACK)
    res = requests.post(DEP_STATUS_CALLBACK, data=data_str, headers=headers)
    Log.logger.debug("call dep_detail_result callback,res: " + str(res))
    return res



def _image_transit_task(task_id = None, result_list = None, obj = None, deploy_id = None, info = None,appinfo=[],deploy_type=None):
    image_uuid=info.get("image_uuid")
    if _check_image_status(image_uuid):
        deploy_flag=obj._deploy_docker(info,deploy_id, image_uuid,appinfo,deploy_type)
        if not deploy_flag:
            TaskManager.task_exit(task_id)
    else:
        #检查镜像五次状态不为active将错误返回给uop
        image_url = info.get('url', '')
        cluster_name = info.get("ins_name", "")
        ip = info.get('ip', [])
        ip = ','.join(ip)
        err_msg="check image five times,image status not active,image url is:%s" % image_url
        _dep_callback(deploy_id, ip, "docker", err_msg, "None", False, cluster_name, True, 'deploy')
    TaskManager.task_exit(task_id)

def _check_image_status(image_uuid):
    nova_client = OpenStack.nova_client
    check_times = 5
    check_interval = 5
    for i in range(check_times):
        img = nova_client.glance.find_image(image_uuid)
        Log.logger.debug("check image status " + str(i) + " times, status: " + img.status.lower()+ " image_uuid:" + image_uuid)
        if (img.status.lower() != "active"):
            time.sleep(check_interval)
        else:
            return True
    return False



def closed_nginx_conf(appinfo,ip):
    try:
        selfdir = os.path.dirname(os.path.abspath(__file__))
        conf_dir="/usr/local/nginx/conf/servers_systoon"
        for info in appinfo:
            ips=info.get("ips",[])
            if ip in ips:
                domain_ip = info.get("domain_ip", "")
                port = info.get("port", "")
                domain = info.get("domain", "")
                close_cmd="sed  -i 's/server  %s:%s/#server  %s:%s/g' %s/%s" % (ip,port,ip,port,conf_dir,domain)
                reload_cmd="/usr/local/nginx/sbin/nginx -s reload"
                an_close_cmd='''ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a "{cmd}"'''.format(nip=domain_ip,dir=selfdir,cmd=close_cmd)
                Log.logger.debug(an_close_cmd)
                an_reload_cmd = '''ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a "{cmd}"'''.format(nip=domain_ip,dir=selfdir,cmd=reload_cmd)
                #开始执行注释nginx配置文件和reload nginx 命令
                exec_cmd_ten_times(domain_ip,an_close_cmd, 1)
                exec_cmd_ten_times(domain_ip,an_reload_cmd, 1)
    except Exception as e:
        msg = "closed_nginx_conf error %s" % e
        Log.logger.error(msg)
        return -1, msg
    return 1, ''

def open_nginx_conf(appinfo,ip):
    try:
        selfdir = os.path.dirname(os.path.abspath(__file__))
        conf_dir = "/usr/local/nginx/conf/servers_systoon"
        for info in appinfo:
            ips=info.get("ips",[])
            if ip in ips:
                domain_ip = info.get("domain_ip", "")
                port = info.get("port", "")
                domain = info.get("domain", "")
                open_cmd="sed  -i 's/#server  %s:%s/server  %s:%s/g' %s/%s" % (ip,port,ip,port,conf_dir,domain)
                reload_cmd="/usr/local/nginx/sbin/nginx -s reload"
                an_open_cmd='''ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a "{cmd}"'''.format(nip=domain_ip,dir=selfdir,cmd=open_cmd)
                Log.logger.debug(an_open_cmd)
                an_reload_cmd = '''ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a "{cmd}"'''.format(nip=domain_ip,dir=selfdir,cmd=reload_cmd)
                #开始执行注释nginx配置文件和reload nginx 命令
                exec_cmd_ten_times(domain_ip,an_open_cmd, 1)
                exec_cmd_ten_times(domain_ip,an_reload_cmd, 1)
    except Exception as e:
        msg = "open_nginx_conf error %s" % e
        Log.logger.error(msg)
        return -1, msg
    return 1, ''


def write_docker_logs_to_file(task_id,result_list=None,os_inst_id=None):
    try:
        if os_inst_id is None:
            TaskManager.task_exit(task_id)
        nova_cli = OpenStack.nova_client
        vm = nova_cli.servers.get(os_inst_id)
        try:
            logs = vm.get_console_output()
        except Exception as e:
            logs='The logs is too big or get docker log error,opsnstack can not get it to crp '
            Log.logger.error('CRP get docker  log from openstack error:%s' % str(e.args))
        os_log_dir=os.path.join(OS_DOCKER_LOGS,os_inst_id)
        os_log_file=os.path.join(os_log_dir,"docker_start.log")
        #目录不存在创建目录
        if not os.path.exists(os_log_dir):
            os.makedirs(os_log_dir)
        #将日志写入文件
        with open(os_log_file, 'w') as f:
            f.write('%s' % str(logs))
        TaskManager.task_exit(task_id)
    except Exception as e:
        Log.logger.error("CRP get log from openstack write to file error: %s" %e )
        TaskManager.task_exit(task_id)

def start_write_log(ip):
    result_list = []
    server = OpenStack.find_vm_from_ipv4(ip=ip)
    os_inst_id = None
    if server:
        os_inst_id=server.id
    timeout = 10000
    sleep_time=1
    Log.logger.debug("Begin wrtite log to file,the docker ip is %s" % ip)
    TaskManager.task_start(sleep_time, timeout, result_list,write_docker_logs_to_file,os_inst_id)


def get_war_from_ftp(project_name,war_url,env):
    err_msg = None
    try:
        base_war_name = "{project_name}.war".format(project_name=project_name)
        war_name = "{project_name}_{env}.war".format(project_name=project_name,env=env)
        url_war_name = war_url.split("/")[-1]
        if base_war_name != url_war_name:
            err_msg = "The war url is error,url war name is not project war name "
            return err_msg
        project_dir_path = os.path.join(UPLOAD_FOLDER,"war/{project_name}".format(project_name=project_name))
        if not os.path.exists(project_dir_path):
            os.makedirs(project_dir_path)
        project_war_path =  os.path.join(project_dir_path,war_name)
        if os.path.exists(project_war_path):
            os.remove(project_war_path)
        wget_cmd = "wget -O {project_war_path} --tries=3 {war_url}".format(project_war_path=project_war_path,war_url=war_url)
        p = subprocess.Popen(
            wget_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        res = p.stdout.read()
        if "ERROR" in res:
            err_msg = res
    except Exception as e:
        err_msg = "get war from frp error:{e}".format(e=str(e))
    return err_msg

def make_database_config(database_config,project_name,ip,env):
    err_msg = None
    try:
        wardeploy_path = os.path.join(UPLOAD_FOLDER,"wardeploy")
        config_filename = "{project_name}_dev".format(project_name=project_name)
        wardeploy_conf_path = os.path.join(wardeploy_path,config_filename)
        if not os.path.exists(wardeploy_path):
            os.makedirs(wardeploy_path)
        project_name_head = "[{project_name}]".format(project_name=project_name)
        ip_text = '\n'.join(ip)
        text = project_name_head + "\n" + ip_text
        project_name_vars = "[{project_name}:vars]".format(project_name=project_name)
        text = text + "\n" + project_name_vars
        domain = "prdomain="
        env = "env={env}".format(env=env)
        text = text + "\n" + domain + "\n" + env
        if database_config:
            database_config = json.loads(database_config)
            mysql_info_list = database_config.get("mysql")
            if mysql_info_list:
                mysql_text = ""
                for mysql_info in mysql_info_list:
                    for k, v in mysql_info.items():
                        mysql_text = mysql_text + "\n" + "{k}={v}".format(k=k, v=v)
                text = text + "\n" + mysql_text
            mycat_info_list = database_config.get("mycat")
            if mycat_info_list:
                mycat_text = ""
                for mycat_info in mycat_info_list:
                    for k, v in mycat_info.items():
                        mycat_text = mycat_text + "\n" + "{k}={v}".format(k=k, v=v)
                text = text + "\n" + mycat_text
        write_to_file(text, wardeploy_conf_path)
    except Exception as e:
        err_msg = "get database config error:{e}".format(e=str(e))
    return  err_msg

def write_to_file(text,path):
    try:
        f=open(path,"w")
        f.write(text)
    finally:
        f.close()


