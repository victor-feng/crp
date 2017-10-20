# -*- coding: utf-8 -*-

import logging
import json
import commands
import os
import time
import uuid
from urlparse import urljoin
import subprocess
import threading

from flask_restful import reqparse, Api, Resource
from flask import request
from flask import current_app
import requests
import werkzeug

from crp.app_deployment import app_deploy_blueprint
from crp.app_deployment.errors import user_errors
from crp.utils.docker_tools import image_transit
from crp.utils.aio import async
from crp.openstack import OpenStack
from crp.taskmgr import *
from crp.dns.dns_api import NamedManagerApi
from crp.log import Log
from crp.disconf.disconf_api import *
from crp.disconf.handler import delete_disconf

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from config import APP_ENV, configs


app_deploy_api = Api(app_deploy_blueprint, errors=user_errors)
#TODO: move to global conf
#url = "http://172.28.11.111:8001/cmdb/api/"
#url = "http://uop-test.syswin.com/api/dep_result/"
#url = "http://uop-test.syswin.com/api/dep_result/"
UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER
DEP_STATUS_CALLBACK = configs[APP_ENV].DEP_STATUS_CALLBACK

def _dep_callback(deploy_id,ip,quantity,success):
    data = dict()
    data["ip"]=ip
    data["quantity"]=quantity
    if success:
        data["result"] = "success"
    else:
        data["result"] = "fail"
    data_str = json.dumps(data)

    headers = {'Content-Type': 'application/json'}
    logging.debug("data string:" + str(data))
    #Log.logger.debug("data string:" + str(data))
    CALLBACK_URL = configs[APP_ENV].UOP_URL + 'api/dep_result/'
    logging.debug("[CRP] _dep_callback callback_url: %s ", CALLBACK_URL)
    # CALLBACK_URL = urljoin(current_app.config['UOP_URL'], 'api/dep_result/')
    res = requests.put(CALLBACK_URL + deploy_id + "/", data=data_str, headers=headers)
    logging.debug("call dep_result callback,res: " + str(res))
    #Log.logger.debug("call dep_result callback,res: " + str(res))
    return res


def _dep_detail_callback(deploy_id,deploy_type,ip=None):
    data = {
        "deploy_id":deploy_id,
        "deploy_type":deploy_type,
        "ip":ip,
        "status":"ok",
    }
    
    data_str = json.dumps(data)

    headers = {'Content-Type': 'application/json'}
    logging.debug("data string:" + str(data))
    #Log.logger.debug("data string:" + str(data))
    #CALLBACK_URL = configs[APP_ENV].UOP_URL + 'api/dep_result/'
    logging.debug("[CRP] _dep_detail_callback callback_url: %s ", DEP_STATUS_CALLBACK)
    #DEP_STATUS_CALLBACK="http://127.0.0.1:5000/"
    res = requests.post(DEP_STATUS_CALLBACK, data=data_str, headers=headers)
    logging.debug("call dep_detail_result callback,res: " + str(res))
    #Log.logger.debug("call dep_result callback,res: " + str(res))
    return res



def _query_instance_set_status(task_id=None, result_list=None, osins_id_list=None, deploy_id=None,ip=None,quantity=0):
    rollback_flag = False
    osint_id_wait_query = list(set(osins_id_list) - set(result_list))
    logging.debug("Query Task ID "+task_id.__str__()+", remain "+osint_id_wait_query[:].__str__())
    #Log.logger.debug("Query Task ID "+task_id.__str__()+", remain "+osint_id_wait_query[:].__str__())
    logging.debug("Test Task Scheduler Class result_list object id is " + id(result_list).__str__() +
    #Log.logger.debug("Test Task Scheduler Class result_list object id is " + id(result_list).__str__() +
                     ", Content is " + result_list[:].__str__())
    nova_client = OpenStack.nova_client

    for int_id in osint_id_wait_query:
        time.sleep(1)
        vm = nova_client.servers.get(int_id)
        vm_state = getattr(vm, 'OS-EXT-STS:vm_state')
        #Log.logger.debug("Task ID "+task_id.__str__()+" query Instance ID "+int_id.__str__()+" Status is "+ vm_state)
        logging.debug("Task ID "+task_id.__str__()+" query Instance ID "+int_id.__str__()+" Status is "+ vm_state)
        if vm_state == 'active' or vm_state == 'stopped':
            result_list.append(int_id)
        if vm_state == 'error':
            rollback_flag = True

    if result_list.__len__() == osins_id_list.__len__():
        # TODO(thread exit): 执行成功调用UOP CallBack停止定时任务退出任务线程
        _dep_callback(deploy_id,ip,quantity,True)
        logging.debug("Task ID "+task_id.__str__()+" all instance create success." +
        #Log.logger.debug("Task ID "+task_id.__str__()+" all instance create success." +
                         " instance id set is "+result_list[:].__str__())
        TaskManager.task_exit(task_id)

    if rollback_flag:
        fail_list = list(set(osins_id_list) - set(result_list))
        logging.debug("Task ID "+task_id.__str__()+" have one or more instance create failed." +
        #Log.logger.debug("Task ID "+task_id.__str__()+" have one or more instance create failed." +
                         " Successful instance id set is "+result_list[:].__str__() +
                         " Failed instance id set is "+fail_list[:].__str__())
        # 删除全部，完成rollback
        #for int_id in osins_id_list:
         #   nova_client.servers.delete(int_id)

        # TODO(thread exit): 执行失败调用UOP CallBack停止定时任务退出任务线程
        _dep_callback(deploy_id,ip,quantity,False)
        # 停止定时任务并退出
        TaskManager.task_exit(task_id)


def _image_transit_task(task_id = None, result_list = None, obj = None, deploy_id = None, ip = None, quantity=0 ,image_url = None):
    err_msg, image_uuid = image_transit(image_url, action='deploy')
    if err_msg is None:
        #Log.logger.debug(
        logging.debug(
            "Transit harbor docker image success. The result glance image UUID is " + image_uuid)
        if _check_image_status(image_uuid):
            obj._deploy_docker(ip,quantity,deploy_id, image_uuid)
    else:
        #Log.logger.error(
        logging.error(
            "Transit harbor docker image failed. image_url is " + str(image_url) + " error msg:" + err_msg)
    TaskManager.task_exit(task_id)

def _check_image_status(image_uuid):
    nova_client = OpenStack.nova_client
    check_times = 5
    check_interval = 5
    for i in range(check_times):
        img = nova_client.images.get(image_uuid)
        logging.debug("check image status " + str(i) + " times, status: " + img.status.lower())
        #Log.logger.debug("check image status " + str(i) + " times, status: " + img.status.lower())
        if (img.status.lower() != "active"):
            time.sleep(check_interval)
        else:
            return True
    return False


class AppDeploy(Resource):

    def run_cmd(self, cmd):
        msg = ''
        p = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True)
        while True:
            line = p.stdout.readline()
            Log.logger.debug('The nginx config push result is %s' % line)
            if not line and p.poll() is not None:
                break
            else:
                msg += line
                Log.logger.debug('The nginx config push msg is %s' % msg)
        code = p.wait()
        return msg, code

    def do_app_push(self, app):
        # TODO: do app push
        def do_push_nginx_config(kwargs):
            """
            need the nip domain ip
            nip:这是nginx那台机器的ip
            need write the update file into vm
            :param kwargs:
            :return:
            """
            selfdir = os.path.dirname(os.path.abspath(__file__))
            nip = kwargs.get('nip')
            with open('/etc/ansible/hosts', 'w') as f:
                f.write('%s\n' % nip)
            Log.logger.debug('----->start push:{}dir:{}'.format(kwargs, selfdir))
            self.run_cmd(
                "ansible {nip} --private-key={dir}/id_rsa_98 -a 'yum install rsync -y'".format(nip=nip,dir=selfdir))
            self.run_cmd(
                "ansible {nip} --private-key={dir}/id_rsa_98 -m synchronize -a 'src={dir}/update.py dest=/tmp/'".format(
                    nip=nip, dir=selfdir))
            self.run_cmd(
                "ansible {nip} --private-key={dir}/id_rsa_98 -m synchronize -a 'src={dir}/template dest=/tmp/'".format(
                    nip=nip, dir=selfdir))
            Log.logger.debug('------>上传配置文件完成')
            self.run_cmd("ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a 'chmod 777 /tmp/update.py'".format(
                nip=nip, dir=selfdir))
            self.run_cmd("ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a 'chmod 777 /tmp/template'".format(
                nip=nip, dir=selfdir))
            self.run_cmd(
                'ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a '
                '"/tmp/update.py {domain} {ip} {port}"'.format(
                    nip=kwargs.get('nip'),
                    dir=selfdir,
                    domain=kwargs.get('domain'),
                    ip=kwargs.get('ip'),
                    port=kwargs.get('port')))
            Log.logger.debug('------>end push')

        real_ip = ''
        ips = app.get('ips')
        Log.logger.debug("####current compute instance is:{}".format(app))
        domain_ip = app.get('domain_ip', "")
        domain = app.get('domain', '')
        for ip in ips:
            ip_str = ip + ' '
            real_ip += ip_str
        ports = str(app.get('port'))
        Log.logger.debug(
            'the receive (domain, nginx, ip, port) is (%s, %s, %s, %s)' %
            (domain, domain_ip, real_ip, ports))
        try:
            do_push_nginx_config({'nip': domain_ip,
                                'domain': domain,
                                'ip': real_ip.strip(),
                                'port': ports.strip()})
        except Exception as e:
            Log.logger.debug("error:{}".format(e))

    @async
    def run_delete_cmd(self, **kwargs):
        selfdir = os.path.dirname(os.path.abspath(__file__))
        domain_list = kwargs.get("domain_list")
        disconf_list = kwargs.get("disconf_list")
        # Log.logger.debug("---------start delete disconf profiles-------")
        # delete_disconf(disconf_list)
        Log.logger.debug("---------start delete nginx profiles-------")
        for dl in domain_list:
            nip = dl.get("domain_ip")
            domain = dl.get('domain')
            if not nip or not domain:
                logging.info("nginx ip or domain is null, do nothing")
                continue
            self.run_cmd(
                "ansible {nip} --private-key={dir}/id_rsa_98 -a 'yum install rsync -y'".format(nip=nip, dir=selfdir))
            self.run_cmd(
                "ansible {nip} --private-key={dir}/id_rsa_98 -m synchronize -a 'src={dir}/delete.py dest=/tmp/'".format(
                    nip=nip, dir=selfdir))
            Log.logger.debug('------>上传删除脚本完成')
            self.run_cmd("ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a 'chmod 777 /tmp/delete.py'".format(
                nip=nip, dir=selfdir))
            self.run_cmd(
                'ansible {nip} --private-key={dir}/id_rsa_98 -m shell -a '
                '"/tmp/delete.py {domain}"'.format(
                    nip=nip,
                    dir=selfdir,
                    domain=domain)
            )
        Log.logger.debug("---------stop delete nginx profiles: success-------")

    def delete(self):
        code = 200
        msg = "ok"
        try:
            request_data = json.loads(request.data)
            disconf_list = request_data.get('disconf_list')
            domain_list = request_data.get('domain_list')
            self.run_delete_cmd(domain_list=domain_list, disconf_list=disconf_list)
        except Exception as msg:
            Log.logger.error("delete nginx ip error {}".format(msg))
            code = 500
            msg = msg
        res = {
            "code": code,
            "result": {
                "res": "",
                "msg": msg
            }
        }
        return res, code

    def post(self):
        code = 200
        msg = "ok"
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('mysql', type=dict)
            parser.add_argument('docker', type=list, location='json')
            parser.add_argument('deploy_id', type=str)
            parser.add_argument('mongodb', type=str)
            parser.add_argument('dns', type=list, location='json')
            parser.add_argument('appinfo', type=list, location='json')
            parser.add_argument('disconf_server_info', type=list, location='json')
            #parser.add_argument('file', type=werkz
            # eug.datastructures.FileStorage, location='files')
            args = parser.parse_args()
            #logging.debug("AppDeploy receive post request. args is " + str(args))
            Log.logger.debug("AppDeploy receive post request. args is " + str(args))
            deploy_id = args.deploy_id
            logging.debug("deploy_id is " + str(deploy_id))
            docker = args.docker
            mongodb = args.mongodb
            mysql = args.mysql
            dns = args.dns
            disconf_server_info = args.disconf_server_info
            appinfo = args.appinfo
            print "appinfo", appinfo
            logging.debug("Thread exec start")
            t = threading.Thread(target=self.deploy_anything, args=(mongodb, mysql, docker, dns, deploy_id, appinfo, disconf_server_info))
            t.start()
            logging.debug("Thread exec done")

        except Exception as e:
            logging.exception("AppDeploy exception: ")
            # Log.logger.error("AppDeploy exception: " + e.message)
            code = 500
            msg = "internal server error: " + e.message

        res = {
            "code": code,
            "result": {
                "res": "",
                "msg": msg
            }
        }
        return res, code

    def deploy_anything(self, mongodb, mysql, docker, dns, deploy_id, appinfo, disconf_server_info):
        try:
            lock = threading.RLock()
            lock.acquire()
            code = 200
            msg = "ok"
            mongodb_res = True
            sql_ret = True
            if not appinfo:
                Log.logger.info("No nginx ip information, no need to push nginx something")
            for app in appinfo:
                self.do_app_push(app)
                _dep_detail_callback(deploy_id,"deploy_nginx")
            if mongodb:
                logging.debug("The mongodb data is %s" % mongodb)
                mongodb_res = self._deploy_mongodb(mongodb)
                _dep_detail_callback(deploy_id,"deploy_mongodb")
            if mysql:
                sql_ret = self._deploy_mysql(mysql, docker)
                _dep_detail_callback(deploy_id,"deploy_mysql")

            #logging.debug("Docker is " + str(docker))
            #for i in docker:
            #    while True:
            #        ips = i.get('ip')
            #        length_ip = len(ips)
            #        if length_ip > 0:
            #            logging.debug('ip and url: ' + str(ips) + str(i.get('url')))
            #            ip = ips[0]
            #            # self._image_transit(deploy_id, docker.get("ip"), docker.get("image_url"))
            #            self._image_transit(deploy_id, ip, i.get('url'))
            #            ips.pop(0)
            #        else:
            #            break

            #添加dns解析
            for item in dns:
                domain_name = item.get('domain','')
                domain_ip = item.get('domain_ip','')
                Log.logger.debug('domain_name:%s,domain_ip:%s' % (domain_name,domain_ip))
                if len(domain_name.strip()) != 0 and len(domain_ip.strip()) != 0:
                    dns_api = NamedManagerApi()
                    msg = dns_api.named_dns_domain_add(domain_name=domain_name, domain_ip=domain_ip)
                    Log.logger.debug('The dns add result: %s' % msg)
                else:
                    Log.logger.debug('domain_name:{domain_name},domain_ip:{domain_ip} is null'.format(domain_name=domain_name,domain_ip=domain_ip))
                _dep_detail_callback(deploy_id,"deploy_dns")


            #添加disconf配置
            for disconf_info in disconf_server_info:
                Log.logger.debug('The disconf_info: %s' % disconf_info)
                disconf_api_connect = DisconfServerApi(disconf_info)
                if disconf_info.get('disconf_env','').isdigit():
                    env_id = disconf_info.get('disconf_env')
                else:
                    env_id = disconf_api_connect.disconf_env_id(env_name=disconf_info.get('disconf_env'))

                if len(disconf_info.get('disconf_admin_content','').strip()) == 0:
                    disconf_admin_name = exchange_disconf_name(disconf_info.get('disconf_content'))
                else:
                    disconf_admin_name = exchange_disconf_name(disconf_info.get('disconf_admin_content'))

                result,message = disconf_api_connect.disconf_add_app_config_api_file(
                                                app_name=disconf_info.get('disconf_app_name'),
                                                myfilerar=disconf_admin_name,
                                                version=disconf_info.get('disconf_version'),
                                                env_id=env_id
                                                )
                Log.logger.debug("disconf result:{result},{message}".format(result=result,message=message))
            if disconf_server_info:
                _dep_detail_callback(deploy_id,"deploy_disconf")
            quantity=0
            for info in docker:
                ips = info.get('ip') 
                quantity=quantity+len(ips)
            logging.debug("Docker is " + str(docker))
            for i in docker:
                while True:
                    ips = i.get('ip')
                    length_ip = len(ips)
                    if length_ip > 0:
                        logging.debug('ip and url: ' + str(ips) + str(i.get('url')))
                        ip = ips[0]
                        # self._image_transit(deploy_id, docker.get("ip"), docker.get("image_url"))
                        self._image_transit(deploy_id, ip,quantity,i.get('url'))
                        ips.pop(0)
                        #_dep_detail_callback(deploy_id,"deploy_docker",ip)
                    else:
                        break
            
            if not (sql_ret and mongodb_res):
                res = _dep_callback(deploy_id, False)
                if res.status_code == 500:
                    code = 500
                    msg = "uop server error"

            lock.release()
        except Exception as e:
            code = 500
            msg = "internal server error: " + str(e.message)
        return code, msg

    def _deploy_mongodb(self, mongodb):
        res = None
        old_db_list = []
        new_db_list = []
        logging.debug("args is %s" % mongodb)
        mongodb = eval(mongodb)
        db_username = mongodb.get('mongodb_username', '')
        db_password = mongodb.get('mongodb_password', '')
        mongodb_username = mongodb.get('db_username', '')
        mongodb_password = mongodb.get('db_password', '')
        vip1 = mongodb.get('vip1', '')
        vip2 = mongodb.get('vip2', '')
        vip3 = mongodb.get('vip3', '')
        port = mongodb.get('port', '')
        database = mongodb.get('database', '')
        path_filename = mongodb.get("path_filename", '')
        if not path_filename:
            return True
        ips = [vip1, vip2, vip3]

        local_path = path_filename[0]
        remote_path = '/tmp/' + path_filename[1]
        logging.debug("local_path and remote_path is %s-%s" % (local_path, remote_path))
        sh_path = self.mongodb_command_file(mongodb_password, mongodb_username, port, database, local_path)
        logging.debug("start deploy mongodb cluster", sh_path)

        # for ip in ips:
        #     host_path = self.mongodb_hosts_file(ip)
        #     ansible_cmd = 'ansible -i ' + host_path + ' ' + ip + ' ' + '
        # --private-key=crp/res_set/playbook-0830/old_id_rsa -m'
        #     ansible_sql_cmd = ansible_cmd + ' synchronize -a "src=' + local_path + ' dest=' + remote_path + '"'
        #     ansible_sh_cmd = ansible_cmd + ' shell -a "%s < %s"' % (configs[APP_ENV].MONGODB_PATH, remote_path)
        #     if self._exec_ansible_cmd(ansible_sql_cmd):
        #         res = self._exec_ansible_cmd(ansible_sh_cmd)
        #         logging.debug("end deploy mongodb cluster")
        #     else:
        #         res = False
        # return res

        # 只需要对主节点进行认证操作
        host_path = self.mongodb_hosts_file(vip3)
        ansible_cmd = 'ansible -i ' + host_path + ' ' + vip3 + ' ' + ' --private-key=crp/res_set/playbook-0830/old_id_rsa -m'
        ansible_sql_cmd = ansible_cmd + ' synchronize -a "src=' + sh_path + ' dest=' + remote_path + '"'
        ansible_sh_cmd = ansible_cmd + ' shell -a "%s < %s"' % (configs[APP_ENV].MONGODB_PATH, remote_path)

        if self._exec_ansible_cmd(ansible_sql_cmd):
            if self._exec_ansible_cmd(ansible_sh_cmd):

                sh_path = self.mongodb_command_file(mongodb_password, mongodb_username, port, database, "")
                ansible_sql_cmd = ansible_cmd + ' synchronize -a "src=' + sh_path + ' dest=' + remote_path + '"'
                query_current_db = ansible_cmd + 'shell -a "%s < %s"' % (configs[APP_ENV].MONGODB_PATH, remote_path)

                if self._exec_ansible_cmd(ansible_sql_cmd):
                    logging.debug("upload query file success and then get the db name")
                    status, output = commands.getstatusoutput(query_current_db)
                    output_list = output.split('\n')[5:-1]   # ['admin  0.000GB', 'local  0.001GB']
                    for i in output_list:
                        old_db_list.append(i.split(' ')[0])  # ['admin', 'local']
                    logging.debug("the db list is %s" % old_db_list)
                    for db in old_db_list:  # need get the new created db
                        # if db == 'admin' or 'local':
                        if db not in ['admin', 'local']:
                            new_db_list.append(db)
                    logging.debug("the new create db list is %s" % new_db_list)
                    if len(new_db_list):
                        auth_path = self.mongodb_auth_file(mongodb_username, mongodb_password, new_db_list)
                        ansible_sql_cmd = ansible_cmd + ' synchronize -a "src=' + auth_path + ' dest=' + remote_path + '"'
                        exec_auth_file = ansible_cmd + ' shell -a "%s < %s"' % \
                                                         (configs[APP_ENV].MONGODB_AUTH_PATH, remote_path)
                        logging.debug("start upload auth file")
                        if self._exec_ansible_cmd(ansible_sql_cmd):
                            logging.debug("end upload and start exec auth file")
                            status, output = commands.getstatusoutput(exec_auth_file)
                            logging.debug("end exec auth file status is %s output is %s" % (status, output))

                            self.ansible_exec(host_path, vip3, remote_path)  # del the ansible file had uploaded

                            logging.debug("del the ansible file successful")
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def ansible_exec(self, host_path, vip3, file_path):
        cmd = 'ansible -i ' + host_path + ' ' + vip3 + ' ' + ' --private-key=crp/res_set/playbook-0830/old_id_rsa -m'
        exec_del_cmd = cmd + 'shell -a "rm -f %s"' % file_path
        status, output = commands.getstatusoutput(exec_del_cmd)
        if not status:
            res = 'del success'
            logging.debug("%s" % res)
        else:
            logging.debug("%s" % output)

    def mongodb_auth_file(self, username, password, db_list):
        auth_path = os.path.join(UPLOAD_FOLDER, 'mongodb_auth.js')
        with open(auth_path, 'wb+') as f:
            for db in db_list:
                f.write("use %s\n" % db)
                f.write('db.createUser({user: "%s",pwd: "%s",roles: [ { role: "readWrite", db: "%s" } ]})' %
                        (username, password, db)
                        )
        return auth_path

    def mongodb_command_file(self, username, password, port, db, script_file):
        sh_path = ""
        logging.debug("sh_path is %s" % script_file)
        if script_file:
            sh_path = os.path.join(UPLOAD_FOLDER, 'mongodb.js')
            with open(script_file, 'r') as f2:
                file_script = f2.readlines()
            with open(sh_path, 'wb+') as f:
                f.write("use admin\n")
                f.write("db.auth('admin','123456')\n")
                for i in file_script:
                    f.write(i)
            logging.debug("end write sh_path****")
        else:
            sh_path = os.path.join(UPLOAD_FOLDER, 'query_mongodb.js')
            with open(sh_path, 'wb+') as f:
                f.write("use admin\n")
                f.write("db.auth('admin','123456')\n")
                f.write("show dbs\n")
            logging.debug("end write query_mongodb sh_path+++")
        return sh_path

    def mongodb_hosts_file(self, ip):
        path = os.path.join('/etc', 'ansible', 'hosts')
        with open(path, "wb+") as file_object:
            file_object.write(ip)
        return path

    def exec_final_script(self, cmd):
        for i in cmd:
            p = subprocess.Popen(i, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                print line,

    def clear_hosts_file(self, work_dir):
        with open(work_dir + '/hosts', 'w') as f:
            f.write(' ')

    def _deploy_mysql(self,mysql, docker):
        database_user = mysql.get("database_user")
        database_password = mysql.get("database_password")
        mysql_password = mysql.get("mysql_password")
        mysql_user = mysql.get("mysql_user")
        ip = mysql.get("ip")
        port = mysql.get("port")
        app_ips = [ _docker.get('ip') for _docker in docker ]
        ips = []
        for _ips in app_ips:
            ips.extend(_ips)

        # sql = args.mysql.get("sql_script").replace('\xc2\xa0', ' ')
        path_filename = mysql.get("path_filename")
        if not path_filename:
            return True
        # if sql:
        #     sql_srcipt_file_name = self._make_sql_script_file(workdir,sql)

        local_path = path_filename[0]
        remote_path = '/root/' + path_filename[1]
        content = "source " + remote_path + "\nquit "
        if not os.path.exists(os.path.join(UPLOAD_FOLDER, 'mysql')):
            os.makedirs(os.path.join(UPLOAD_FOLDER, 'mysql'))
        sh_path = self._excute_mysql_cmd(mysql_password, mysql_user, port, content)
        host_path = self._make_hosts_file(ip)
        ansible_cmd = 'ansible -i ' + host_path + ' ip ' +  ' --private-key=crp/res_set/playbook-0830/old_id_rsa -u root -m'
        ansible_sql_cmd = ansible_cmd + ' copy -a "src=' + local_path + ' dest=' + remote_path + '"'
        ansible_sh_cmd =  ansible_cmd + ' script -a ' + sh_path
        if self._exec_ansible_cmd(ansible_sql_cmd):
            if self._exec_ansible_cmd(ansible_sh_cmd):
                show_path = self._excute_mysql_cmd(mysql_password, mysql_user, port, 'show databases;')
                ansible_show_databases_cmd = ansible_cmd + " script -a " + show_path\
                                             + " |grep 'stdout' |awk -F: '{print $NF}' |head -1 |awk -F, '{print $1}'"
                (status, output) = commands.getstatusoutput(ansible_show_databases_cmd)
                ##########  去掉影响查询新增数据库的干扰字符 ##########
                output = output.replace('-', '').replace('+', '').replace('|','')
                databases = output.split('\\r\\n')[3:-2][3:]
                #####################################################
                if databases:
                    for data_name in databases:
                        data_name = data_name.strip(' ')
                        cmd = ''
                        for app_ip in ips:
                            cmd1 = "create user \'" + database_user + "\'@\'" + app_ip + "\' identified by  \'" + database_password + "\' ;\n"
                            cmd2 = "grant select, update, insert, delete, execute on " + data_name + ".* to \'" + database_user +\
                                   "\'@\'" + app_ip + "\';\n"
                            cmd += cmd1 + cmd2
                        create_path = self._excute_mysql_cmd(mysql_password, mysql_user, port, cmd)
                        ansible_create_cmd = ansible_cmd + ' script -a ' + create_path
                        if not self._exec_ansible_cmd(ansible_create_cmd):
                            return False
                    return True
            return False
        else:
             return False

    def _exec_ansible_cmd(self,cmd):
        (status, output) = commands.getstatusoutput(cmd)
        if output.lower().find("error") == -1 and output.lower().find("failed") == -1:
            logging.debug("ansible exec succeed,command: " + str(cmd) + " output: " + output)
            #Log.logger.debug("ansible exec succeed,command: " + str(cmd) + " output: " + output)
            return True
        logging.debug("ansible exec failed,command: " + str(cmd) + " output: " + output)
        #Log.logger.debug("ansible exec failed,command: " + str(cmd) + " output: " + output)
        return False

    def _excute_mysql_cmd(self, password, user, port, content):
        sh_path = os.path.join(UPLOAD_FOLDER, 'mysql', 'tmp.sh')
        with open(sh_path, "wb+") as file_object:
            file_object.write("#!/bin/bash\n")
            file_object.write("TMP_PWD=$MYSQL_PWD\n")
            file_object.write("export MYSQL_PWD=" + password + "\n")
            file_object.write("mysql -u" + user + " -P" + port + " -e \"\n")
            file_object.write(content)
            file_object.write("\"\n")
            file_object.write("export MYSQL_PWD=$TMP_PWD\n")
            file_object.write("exit;")
        return sh_path

    def _make_sql_script_file(self,workdir,sql,db_type):
        file_name = db_type + "_crp_" + str(uuid.uuid1()) + ".sql"
        with open(workdir + '/' + file_name, "wb+") as file_object:
            file_object.write(sql + "\n")
        return file_name

    def _make_hosts_file(self, ip):
        myhosts_path = os.path.join(UPLOAD_FOLDER, 'mysql', 'myhosts')
        with open(myhosts_path, "wb+") as file_object:
            file_object.write('[ip]' + os.linesep)
            file_object.write(ip)
        return myhosts_path

    def _deploy_docker(self, ip,quantity ,deploy_id, image_uuid):
        server = OpenStack.find_vm_from_ipv4(ip = ip)
        newserver = OpenStack.nova_client.servers.rebuild(server=server, image=image_uuid)
        # newserver = OpenStack.nova_client.servers.rebuild(server=server, image='3027f868-8f87-45cd-b85b-8b0da3ecaa84')
        vm_id_list = []
        # Log.logger.debug("Add the id type is" + type(newserver.id))
        logging.debug("Add the id type is" + str(newserver.id))
        vm_id_list.append(newserver.id)
        result_list = []
        timeout = 10
        TaskManager.task_start(SLEEP_TIME, timeout, result_list, _query_instance_set_status, vm_id_list, deploy_id,ip,quantity)

    def _image_transit(self,deploy_id, ip,quantity ,image_url):
        result_list = []
        timeout = 10
        TaskManager.task_start(SLEEP_TIME, timeout, result_list, _image_transit_task, self, deploy_id, ip,quantity, image_url)


class Upload(Resource):
    def post(self):
        try:
            UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
            type = request.form.get('type','')

            if type == 'disconf':
                file = request.files['file']
                disconf_file_name = file.filename
                disconf_file_path = request.form.get('disconf_file_path')
                disconf_abspath = os.path.dirname(disconf_file_path)
                if not os.path.exists(disconf_abspath):
                    os.makedirs(disconf_abspath)
                file.save(disconf_file_path)
                result = "{disconf_file_name} upload success".format(disconf_file_name=disconf_file_name)
            else:
                file_dic = {}
                for _type, file in request.files.items():
                    if not os.path.exists(os.path.join(UPLOAD_FOLDER, _type)):
                        os.makedirs(os.path.join(UPLOAD_FOLDER, _type))
                    file_path = os.path.join(UPLOAD_FOLDER, _type, file.filename)
                    file.save(file_path)
                    file_dic[_type] = (file_path, file.filename)
                    result = file_dic
        except Exception as e:
            return {
                'code': 500,
                'msg': e.message
            }
        return {
            'code': 200,
            'msg': '上传成功！',
            'file_info': result,
        }


app_deploy_api.add_resource(AppDeploy, '/deploys')
app_deploy_api.add_resource(Upload, '/upload')
