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
from crp.openstack import OpenStack
from crp.taskmgr import *
from crp.log import Log

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

def _dep_callback(deploy_id, success):
    data = dict()
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


def _query_instance_set_status(task_id=None, result_list=None, osins_id_list=None, deploy_id=None):
    rollback_flag = False
    osint_id_wait_query = list(set(osins_id_list) - set(result_list))
    logging.debug("Query Task ID "+task_id.__str__()+", remain "+osint_id_wait_query[:].__str__())
    #Log.logger.debug("Query Task ID "+task_id.__str__()+", remain "+osint_id_wait_query[:].__str__())
    logging.debug("Test Task Scheduler Class result_list object id is " + id(result_list).__str__() +
    #Log.logger.debug("Test Task Scheduler Class result_list object id is " + id(result_list).__str__() +
                     ", Content is " + result_list[:].__str__())
    nova_client = OpenStack.nova_client

    for int_id in osint_id_wait_query:
        vm = nova_client.servers.get(int_id)
        vm_state = getattr(vm, 'OS-EXT-STS:vm_state')
        #Log.logger.debug("Task ID "+task_id.__str__()+" query Instance ID "+int_id.__str__()+" Status is "+ vm_state)
        logging.debug("Task ID "+task_id.__str__()+" query Instance ID "+int_id.__str__()+" Status is "+ vm_state)
        if vm_state == 'active':
            result_list.append(int_id)
        if vm_state == 'error':
            rollback_flag = True

    if result_list.__len__() == osins_id_list.__len__():
        # TODO(thread exit): 执行成功调用UOP CallBack停止定时任务退出任务线程
        _dep_callback(deploy_id, True)
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
        _dep_callback(deploy_id, False)
        # 停止定时任务并退出
        TaskManager.task_exit(task_id)


def _image_transit_task(task_id = None, result_list = None, obj = None, deploy_id = None, ip = None, image_url = None):
    err_msg, image_uuid = image_transit(image_url)
    if err_msg is None:
        #Log.logger.debug(
        logging.debug(
            "Transit harbor docker image success. The result glance image UUID is " + image_uuid)
        if _check_image_status(image_uuid):
            obj._deploy_docker(ip, deploy_id, image_uuid)
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
    def post(self):
        code = 200
        msg = "ok"
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('mysql', type=dict)
            parser.add_argument('docker', type=list, location='json')
            parser.add_argument('deploy_id', type=str)
            parser.add_argument('mongodb', type=str)
            #parser.add_argument('file', type=werkz
            # eug.datastructures.FileStorage, location='files')
            args = parser.parse_args()
            logging.debug("AppDeploy receive post request. args is " + str(args))
            #Log.logger.debug("AppDeploy receive post request. args is " + str(args))
            deploy_id = args.deploy_id
            logging.debug("deploy_id is " + str(deploy_id))
            docker = args.docker
            mongodb = args.mongodb

            logging.debug("Thread exec start")
            t = threading.Thread(target=self.deploy_anything, args=(mongodb, args, docker, deploy_id))
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

    def deploy_anything(self, mongodb, args, docker, deploy_id):
        try:
            lock = threading.RLock()
            lock.acquire()
            code = 200
            msg = "ok"
            mongodb_res = True
            sql_ret = True
            if mongodb:
                mongodb_res = self._deploy_mongodb(mongodb)
            if args.mysql:
                sql_ret = self._deploy_mysql(args)
            logging.debug("Docker is " + str(docker))
            for i in docker:
                while True:
                    ips = i.get('ip')
                    length_ip = len(ips)
                    if length_ip > 0:
                        logging.debug('ip and url: ' + str(ips) + str(i.get('url')))
                        ip = ips[0]
                        # self._image_transit(deploy_id, docker.get("ip"), docker.get("image_url"))
                        self._image_transit(deploy_id, ip, i.get('url'))
                        ips.pop(0)
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

    def _deploy_mongodb(self, args):
        host_username = args.get('host_username', '')
        host_password = args.get('host_passwork', '')
        mongodb_username = args.get('mongodb_username', '')
        mongodb_password = args.get('mongodb_password', '')
        vip1 = args.get('vip1', '')
        vip2 = args.get('vip2', '')
        vip3 = args.get('vip3', '')
        port = args.get('port', '')
        database = args.get('database', '')
        path_filename = args.get("path_filename", '')
        if not path_filename:
            return True
        ips = [vip1, vip2, vip3]

        local_path = path_filename[0]
        remote_path = '/tmp/' + path_filename[1]
        sh_path = self.mongodb_command_file(mongodb_password, mongodb_username, port, database, local_path)

        for ip in ips:
            host_path = self.mongodb_hosts_file(ip)
            ansible_cmd = 'ansible -i ' + host_path + ip + ' --private-key=crp/res_set/playbook-0830/old_id_rsa -u root -m'
            ansible_sql_cmd = ansible_cmd + ' copy -a "src=' + local_path + ' dest=' + remote_path + '"'
            ansible_sh_cmd = ansible_cmd + ' script -a ' + sh_path
            if self._exec_ansible_cmd(ansible_sql_cmd):
                return self._exec_ansible_cmd(ansible_sh_cmd)
            else:
                return False

    def mongodb_command_file(self, username, password, port, db, script_file):
        sh_path = os.path.join(UPLOAD_FOLDER, 'mongodb.sh')
        with open(sh_path, 'wb+') as f:
            f.write("#!/bin/bash\n")
            f.write("'/opt/mongodb/bin/mongo 127.0.0.1:28010;use admin;db.auth('admin','123456')'")
            f.write("\"db.auth('admin','123456')\"\n")
            f.write("'rs.slaveOK()'\n")
            f.write('%s' % script_file)
            f.write("'exit'")
        return sh_path

    def mongodb_hosts_file(self, ip):
        # myhosts_path = os.path.join(UPLOAD_FOLDER, 'mongodb')
        # with open(myhosts_path, "wb+") as file_object:
        #     file_object.write(ip)
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

    def _deploy_mysql(self,args):
        host_password = args.mysql.get("host_password")
        host_user = args.mysql.get("host_user")
        mysql_password = args.mysql.get("mysql_password")
        mysql_user = args.mysql.get("mysql_user")
        ip = args.mysql.get("ip")
        port = args.mysql.get("port")
        database = args.mysql.get("database")

        # sql = args.mysql.get("sql_script").replace('\xc2\xa0', ' ')
        path_filename = args.mysql.get("path_filename")
        if not path_filename:
            return True
        # if sql:
        #     sql_srcipt_file_name = self._make_sql_script_file(workdir,sql)

        local_path = path_filename[0]
        remote_path = '/root/' + path_filename[1]
        sh_path = self._make_command_file(mysql_password, mysql_user, port, database, remote_path)

        host_path = self._make_hosts_file(ip)
        ansible_cmd = 'ansible -i ' + host_path + ' ip ' +  ' --private-key=crp/res_set/playbook-0830/old_id_rsa -u root -m'
        ansible_sql_cmd = ansible_cmd + ' copy -a "src=' + local_path + ' dest=' + remote_path + '"'
        ansible_sh_cmd =  ansible_cmd + ' script -a ' + sh_path
        if self._exec_ansible_cmd(ansible_sql_cmd):
            return self._exec_ansible_cmd(ansible_sh_cmd)
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

    def _make_command_file(self, password, user, port, database, path):
        sh_path = os.path.join(UPLOAD_FOLDER, 'mysql', 'sql.sh')
        with open(sh_path, "wb+") as file_object:
            file_object.write("#!/bin/bash\n")
            file_object.write("TMP_PWD=$MYSQL_PWD\n")
            file_object.write("export MYSQL_PWD=" + password + "\n")
            file_object.write("mysql -u" + user + " -P" + port + " -e \"\n")
            #file_object.write("use " + database + ";\n")
            file_object.write("source " + path + "\n")
            file_object.write("quit \"\n")
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

    def _deploy_docker(self, ip, deploy_id, image_uuid):
        server = OpenStack.find_vm_from_ipv4(ip = ip)
        newserver = OpenStack.nova_client.servers.rebuild(server=server, image=image_uuid)
        # newserver = OpenStack.nova_client.servers.rebuild(server=server, image='3027f868-8f87-45cd-b85b-8b0da3ecaa84')
        vm_id_list = []
        # Log.logger.debug("Add the id type is" + type(newserver.id))
        logging.debug("Add the id type is" + str(newserver.id))
        vm_id_list.append(newserver.id)
        result_list = []
        timeout = 10
        TaskManager.task_start(SLEEP_TIME, timeout, result_list, _query_instance_set_status, vm_id_list, deploy_id)

    def _image_transit(self,deploy_id, ip, image_url):
        result_list = []
        timeout = 10
        TaskManager.task_start(SLEEP_TIME, timeout, result_list, _image_transit_task, self, deploy_id, ip, image_url)


class Upload(Resource):
    def post(self):
        try:
            UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
            file_dic = {}
            for _type, file in request.files.items():
                file_path = os.path.join(UPLOAD_FOLDER, _type, file.filename)
                file.save(file_path)
                file_dic[_type] = (file_path, file.filename)

        except Exception as e:
            return {
                'code': 500,
                'msg': e.message
            }
        return {
            'code': 200,
            'msg': '上传成功！',
            'file_info': file_dic,
        }


app_deploy_api.add_resource(AppDeploy, '/deploys')
app_deploy_api.add_resource(Upload, '/upload')
