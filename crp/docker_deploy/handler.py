# -*- coding: utf-8 -*-

import json
import logging

from flask_restful import reqparse, Api, Resource

from crp.docker_deploy import docker_deploy_blueprint
from crp.app_deployment.errors import user_errors
from crp.openstack import OpenStack
from crp.taskmgr import *
from crp.log import Log

docker_deploy_api = Api(docker_deploy_blueprint, errors=user_errors)
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
    #Log.logger.debug("Query Task ID "+task_id.__str__()+", remain "+osint_id_wait_query[:].__str__())
    #Log.logger.debug("Test Task Scheduler Class result_list object id is " + id(result_list).__str__() +
    Log.logger.debug("Test Task Scheduler Class result_list object id is " + id(result_list).__str__() +
                     ", Content is " + result_list[:].__str__())
    nova_client = OpenStack.nova_client
    for int_id in osint_id_wait_query:
        vm = nova_client.servers.get(int_id)
        vm_state = getattr(vm, 'OS-EXT-STS:vm_state')
        #Log.logger.debug("Task ID "+task_id.__str__()+" query Instance ID "+int_id.__str__()+" Status is "+ vm_state)
        logger.debug("Task ID "+task_id.__str__()+" query Instance ID "+int_id.__str__()+" Status is "+ vm_state)
        if vm_state == 'active':
            result_list.append(int_id)
        if vm_state == 'error':
            rollback_flag = True

    if result_list.__len__() == osins_id_list.__len__():
        # TODO(thread exit): 执行成功调用UOP CallBack停止定时任务退出任务线程
        _dep_callback(deploy_id, True)
        #Log.logger.debug("Task ID "+task_id.__str__()+" all instance create success." +
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



class DockerDeploy(Resource):

    def post(self, deploy_id):
        code = 0
        res = ""
        msg = {}
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('ip', type=str)
            args = parser.parse_args()
            ip = args.ip

            server = OpenStack.find_vm_from_ipv4(ip=ip)
            newserver = OpenStack.nova_client.servers.rebuild(server=server, image='0bedca16-2b3d-438d-a3a6-c01301392a16')
            #newserver = OpenStack.nova_client.servers.rebuild(server=server, image='3027f868-8f87-45cd-b85b-8b0da3ecaa84')
            vm_id_list = []
            # Log.logger.debug("Add the id type is" + type(newserver.id))
            Log.logger.debug("Add the id type is" + type(newserver.id))
            vm_id_list.append(newserver.id)


            result_list = []
            timeout = 10
            TaskManager.task_start(SLEEP_TIME, timeout, result_list, _query_instance_set_status, vm_id_list, deploy_id)
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


docker_deploy_api.add_resource(DockerDeploy, '/<string:deploy_id>')
