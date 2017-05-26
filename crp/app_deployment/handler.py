# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource
from crp.app_deployment import app_deploy_blueprint
from crp.app_deployment.errors import user_errors
from crp.utils.docker_tools import image_transit
from crp.openstack import OpenStack
from crp.taskmgr import *
from crp.log import Log
import requests
import json
import commands
import os

app_deploy_api = Api(app_deploy_blueprint, errors=user_errors)

#url = "http://172.28.11.111:8001/cmdb/api/"
#url = "http://uop-test.syswin.com/api/dep_result/"
url = "http://172.28.11.111:5001/api/dep_result/"

def _dep_callback(deploy_id, success):
    data = dict()
    if success:
        data["result"] = "success"
    else:
        data["result"] = "fail"
    data_str = json.dumps(data)

    headers = {'Content-Type': 'application/json'}
    res = requests.put(url + deploy_id + "/", data=data_str, headers=headers)
    return res


def _query_instance_set_status(task_id=None, result_list=None, osins_id_list=None, deploy_id=None):
    rollback_flag = False
    osint_id_wait_query = list(set(osins_id_list) - set(result_list))
    Log.logger.debug("Query Task ID "+task_id.__str__()+", remain "+osint_id_wait_query[:].__str__())
    Log.logger.debug("Test Task Scheduler Class result_list object id is " + id(result_list).__str__() +
                     ", Content is " + result_list[:].__str__())
    nova_client = OpenStack.nova_client
    for int_id in osint_id_wait_query:
        vm = nova_client.servers.get(int_id)
        vm_state = getattr(vm, 'OS-EXT-STS:vm_state')
        #Log.logger.debug("Task ID "+task_id.__str__()+" query Instance ID "+int_id.__str__()+" Status is "+ vm_state)
        if vm_state == 'active':
            result_list.append(int_id)
        if vm_state == 'error':
            rollback_flag = True

    if result_list.__len__() == osins_id_list.__len__():
        # TODO(thread exit): 执行成功调用UOP CallBack停止定时任务退出任务线程
        _dep_callback(deploy_id, True)
        Log.logger.debug("Task ID "+task_id.__str__()+" all instance create success." +
                         " instance id set is "+result_list[:].__str__())
        TaskManager.task_exit(task_id)

    if rollback_flag:
        fail_list = list(set(osins_id_list) - set(result_list))
        Log.logger.debug("Task ID "+task_id.__str__()+" have one or more instance create failed." +
                         " Successful instance id set is "+result_list[:].__str__() +
                         " Failed instance id set is "+fail_list[:].__str__())
        # 删除全部，完成rollback
        for int_id in osins_id_list:
            nova_client.servers.delete(int_id)

        # TODO(thread exit): 执行失败调用UOP CallBack停止定时任务退出任务线程
        _dep_callback(deploy_id, False)
        # 停止定时任务并退出
        TaskManager.task_exit(task_id)

class AppDeploy(Resource):
    def post(self):
        code = 200
        msg = "success"

        try:
            parser = reqparse.RequestParser()
            parser.add_argument('deploy_id', type=str)
            parser.add_argument('mysql', type=dict)
            parser.add_argument('docker', type=dict)
            args = parser.parse_args()

            deploy_id = args.deploy_id
            docker = args.docker
            sql_ret = self._deploy_mysql(args)
            if sql_ret:
                err_msg, image_uuid = image_transit(docker.get("image_url"))
                if err_msg is None:
                    Log.logger.debug(
                        "Transit harbor docker image success. The result glance image UUID is " + image_uuid)
                    self._deploy_docker(docker.get("ip"), deploy_id, image_uuid)
                else:
                    Log.logger.error(
                        "Transit harbor docker image failed. image_url is " + docker.get("image_url"))
                    return err_msg, None

            else:
                res = _dep_callback(deploy_id,False)
                if res.status_code == 500:
                    code = 500
                    msg = "uop server error"
        except Exception as e:
            code = 500
            msg = "internal server error"

        res = {
            "code": code,
            "result": {
                "res": "",
                "msg": msg
            }
        }
        return res, code

    def _deploy_mysql(self,args):
        workdir = os.getcwd()
        host_password = args.mysql.get("host_password")
        host_user = args.mysql.get("host_user")
        mysql_password = args.mysql.get("mysql_password")
        mysql_user = args.mysql.get("mysql_user")
        ip = args.mysql.get("ip")
        port = args.mysql.get("port")
        database = args.mysql.get("database")

        sql = args.mysql.get("sql_script")
        if not sql:
            return True

        self._make_sql_file(workdir, mysql_password, mysql_user, port, database, sql)
        self._make_hosts_file(workdir, ip, host_user, host_password)

        (status, output) = commands.getstatusoutput(
            'ansible -i ' + workdir + '/myhosts ' + ip + ' -u root -m script -a ' + workdir + '/sql.sh')
        ret = output.find("ERROR")
        return True if ret == -1 else False

    def _make_sql_file(self,workdir,password,user,port,database,sql):
        with open(workdir + '/sql.sh', "wb+") as file_object:
            file_object.write("#!/bin/bash\n")
            file_object.write("TMP_PWD=$MYSQL_PWD\n")
            file_object.write("export MYSQL_PWD=" + password + "\n")
            file_object.write("mysql -u" + user + " -P" + port + " -e \"\n")
            file_object.write("use " + database + ";\n")
            file_object.write(sql + "\n")
            file_object.write("quit \"\n")
            file_object.write("export MYSQL_PWD=$TMP_PWD\n")
            file_object.write("exit;")

    def _make_hosts_file(self,workdir,ip,user,password):
        with open(workdir + '/myhosts', "wb+") as file_object:
            file_object.write(ip + " ansible_ssh_pass=" + password + " ansible_ssh_user=" + user)

    def _deploy_docker(self, ip, deploy_id, image_uuid):
        server = OpenStack.find_vm_from_ipv4(ip=ip)
        newserver = OpenStack.nova_client.servers.rebuild(server=server, image=image_uuid)
        # newserver = OpenStack.nova_client.servers.rebuild(server=server, image='3027f868-8f87-45cd-b85b-8b0da3ecaa84')
        vm_id_list = []
        # Log.logger.debug("Add the id type is" + type(newserver.id))
        vm_id_list.append(newserver.id)
        result_list = []
        timeout = 10
        TaskManager.task_start(SLEEP_TIME, timeout, result_list, _query_instance_set_status, vm_id_list, deploy_id)

app_deploy_api.add_resource(AppDeploy, '/deploys')
