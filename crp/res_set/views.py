# -*- coding: utf-8 -*-

import os
import re
import json
import uuid
from flask_restful import reqparse, Api, Resource
from flask import request
from crp.taskmgr import *
from crp.res_set import resource_set_blueprint
from crp.res_set.errors import resource_set_errors
from crp.log import Log
from config import configs, APP_ENV
from del_handler import delete_instance_and_query,QUERY_VOLUME,delete_vip
from handler import ResourceProviderTransitions
from del_handler2 import delete_instance_and_query2,QUERY_VOLUME as QUERY_VOLUME2,delete_vip2,QUERY_INGRESS
from handler2 import ResourceProviderTransitions2,tick_announce,deal_del_request_data,do_transit_repo_items
from put_handler2 import QUERY_VM as QUERY_VM2,modfiy_vm_config2
from put_handler import QUERY_VM,modfiy_vm_config


resource_set_api = Api(resource_set_blueprint, errors=resource_set_errors)

TIMEOUT = 5000
SLEEP_TIME = 3
RES_STATUS_DEFAULT = configs[APP_ENV].RES_STATUS_DEFAULT
items_sequence_list_config = configs[APP_ENV].items_sequence_list_config
property_json_mapper_config = configs[APP_ENV].property_json_mapper_config


# res_set REST API Controller
class ResourceSet(Resource):

    @classmethod
    def post(cls):
        """
        API JOSN:
{
    "unit_name": "部署单元名称",
    "unit_id": "部署单元编号",
    "unit_des": "部署单元描述",
    "user_id": "创建人工号",
    "username": "创建人姓名",
    "department": "创建人归属部门",
    "created_time": "部署单元创建时间",
    "resource_id": "资源id",
    "resource_name": "资源名",
    "env": "开发测试生产环境",
    "domain": "qitoon.syswin.com",
    "cmdb_repo_id": "CMDB仓库实例ID",
    "resource_list": [
        {
            "instance_name": "crp-mysql1",
            "instance_id": "实例id1",
            "instance_type": "mysql",
            "cpu": 1,
            "mem": 1,
            "disk": 50,
            "quantity": 1,
            "version": "mysql5.6"
        },
        {
            "instance_name": "crp-mongodb1",
            "instance_id": "实例id2",
            "instance_type": "mongo",
            "cpu": 1,
            "mem": 1,
            "disk": 50,
            "quantity": 1,
            "version": "mongo3.0"
        },
        {
            "instance_name": "crp-redis1",
            "instance_id": "实例id3",
            "instance_type": "redis",
            "cpu": 1,
            "mem": 1,
            "disk": 50,
            "quantity": 1,
            "version": "redis3.0"
        }
    ],
    "compute_list": [
        {
            "instance_name": "crp-tomcat1",
            "instance_id": "容器实例id",
            "cpu": 1,
            "mem": 1,
            "image_url": "arp.reg.innertoon.com/qitoon.checkin/qitoon.checkin:20170517101336"
        }
    ]
}
        """
        # success return http code 202 (Accepted)
        code = 202
        msg = 'Create Resource Set Accepted.'
        try:
            request_data = json.loads(request.data)
            property_mappers_list = do_transit_repo_items(
                items_sequence_list_config, property_json_mapper_config, request_data)
            Log.logger.debug(
                "property_mappers_list: %s" %
                property_mappers_list)
            Log.logger.debug("RES_SET request_data is:" + request_data.__str__())
            parser = reqparse.RequestParser()
            parser.add_argument('unit_name', type=str, location='json')
            parser.add_argument('unit_id', type=str, location='json')
            parser.add_argument('unit_des', type=str, location='json')
            parser.add_argument('user_id', type=str, location='json')
            parser.add_argument('username', type=str, location='json')
            parser.add_argument('department', type=str, location='json')
            parser.add_argument('created_time', type=str, location='json')
            parser.add_argument('project_id', type=str,location='json')
            parser.add_argument('module_id', type=str,location='json')
            parser.add_argument('resource_id', type=str, location='json')
            parser.add_argument('resource_name', type=str, location='json')
            parser.add_argument('env', type=str, location='json')
            parser.add_argument('domain', type=str, location='json')
            parser.add_argument('cmdb_repo_id', type=str, location='json')
            parser.add_argument('resource_list', type=list, location='json')
            parser.add_argument('compute_list', type=list, location='json')
            parser.add_argument('set_flag', type=str, location='json')
            parser.add_argument('cloud', type=str, location='json')
            parser.add_argument('resource_type', type=str, location='json')
            parser.add_argument('syswin_project', type=str, location='json')
            parser.add_argument('project', type=str, location='json')
            parser.add_argument('department_id', type=str, location='json')
            parser.add_argument('project_name', type=str, location='json')
            parser.add_argument('os_ins_ip_list', type=list, location='json')
            parser.add_argument('named_url_list', type=list, location='json')
            args = parser.parse_args()

            req_dict = {}

            unit_name = args.unit_name
            unit_id = args.unit_id
            unit_des = args.unit_des
            user_id = args.user_id
            username = args.username
            department = args.department
            created_time = args.created_time

            resource_id = args.resource_id
            resource_name = args.resource_name
            env = args.env
            domain = args.domain
            cmdb_repo_id = args.cmdb_repo_id
            resource_list = args.resource_list
            compute_list = args.compute_list
            set_flag = args.set_flag
            project_id = args.project_id
            cloud = args.cloud
            resource_type = args.resource_type
            syswin_project = args.syswin_project
            project = args.project
            department_id = args.department_id
            project_name = args.project_name
            module_id = args.module_id
            os_ins_ip_list = args.os_ins_ip_list
            named_url_list = args.named_url_list


            Log.logger.debug(resource_list)
            Log.logger.debug(compute_list)

            req_dict["unit_name"] = unit_name
            req_dict["unit_id"] = unit_id
            req_dict["unit_des"] = unit_des
            req_dict["user_id"] = user_id
            req_dict["username"] = username
            req_dict["department"] = department
            req_dict["created_time"] = created_time
            req_dict["resource_id"] = resource_id
            req_dict["resource_name"] = resource_name
            req_dict["env"] = env
            req_dict["domain"] = domain
            req_dict["cmdb_repo_id"] = cmdb_repo_id
            req_dict["status"] = RES_STATUS_DEFAULT
            req_dict["set_flag"] = set_flag
            req_dict["project_id"] = project_id
            req_dict["cloud"] = cloud
            req_dict["resource_type"] = resource_type
            req_dict["syswin_project"] = syswin_project
            req_dict["project"] = project
            req_dict["department_id"] = department_id
            req_dict["project_name"] = project_name
            req_dict["module_id"] = module_id
            req_dict["os_ins_ip_list"] = os_ins_ip_list
            req_dict["named_url_list"] = named_url_list

            # init default data
            Log.logger.debug('req_dict\'s object id is :')
            Log.logger.debug(id(req_dict))
            # 创建资源集合定时任务，成功或失败后调用UOP资源预留CallBack（目前仅允许全部成功或全部失败，不允许部分成功）
            if cloud == '2':
                res_provider = ResourceProviderTransitions2(
                    resource_id, property_mappers_list, req_dict)
            else:
                res_provider = ResourceProviderTransitions(
                    resource_id, property_mappers_list, req_dict)
            res_provider_list = [res_provider]
            TaskManager.task_start(
                SLEEP_TIME,
                TIMEOUT,
                res_provider_list,
                tick_announce)
        except Exception as e:
            # exception return http code 500 (Internal Server Error)
            code = 500
            msg = str(e)

        res = {
            'code': code,
            'result': {
                'res': 'success',
                'msg': msg,
                'res_id': resource_id,
                'res_name': resource_name
            }
        }

        return res, 202

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('set_flag', type=str, location='json')
        parser.add_argument('flavor', type=str, location='json')
        parser.add_argument('cloud', type=str, location='json')
        parser.add_argument('volume_size', type=int, location='json')
        parser.add_argument('volume_exp_size', type=int, location='json')
        parser.add_argument('syswin_project', type=str, location='json')
        parser.add_argument('resource_id', type=str, location='json')
        parser.add_argument('resource_type', type=str, location='json')
        parser.add_argument('os_ins_ip_list', type=list, location='json')
        args = parser.parse_args()
        Log.logger.debug("Put args {}".format(args))
        set_flag = args.set_flag
        flavor = args.flavor
        cloud = args.cloud
        os_ins_ip_list = args.os_ins_ip_list
        volume_size = args.volume_size
        volume_exp_size = args.volume_exp_size
        syswin_project = args.syswin_project
        resource_id = args.resource_id
        resource_type = args.resource_type
        resources = deal_del_request_data(resource_id, os_ins_ip_list)
        resources = resources.get('resources')
        Log.logger.debug("Put resource {}".format(resources))
        try:
            if cloud == "2":
                for resource in resources:
                    result = {
                        "current_status": QUERY_VM2,
                        "set_flag":set_flag,
                        "syswin_project": syswin_project,
                        "resource_id":resource_id,
                        "resource_type":resource_type,
                        "flavor":flavor,
                        "volume_exp_size":volume_exp_size,
                    }
                    TaskManager.task_start(
                        SLEEP_TIME, TIMEOUT,
                        result,
                        modfiy_vm_config2, resource)
            else:
                for resource in resources:
                    result = {
                        "volume_size": volume_size,
                        "current_status": QUERY_VM,
                        "set_flag":set_flag,
                        "syswin_project": syswin_project,
                        "resource_id":resource_id,
                        "resource_type":resource_type,
                        "flavor":flavor,
                        "volume_exp_size":volume_exp_size,
                    }
                    TaskManager.task_start(
                        SLEEP_TIME, TIMEOUT,
                        result,
                        modfiy_vm_config, resource)
        except Exception as e:
            err_msg = str(e)
            Log.logger.error(
                "[CRP] Resource put failed, Exception:%s" % err_msg)
            code = 400
            res = {
                "code": code,
                "result": {
                    "res": "failed",
                    "msg": err_msg
                }
            }
            return res, code
        else:
            code = 202
            res = {
                "code": code,
                "result": {
                    "msg": "提交成功"
                }
            }
            return res, code


        

class ResourceDelete(Resource):
    
    def delete(self):
        """
        删除资源的接口（虚机、卷、虚IP）
        :return:
        """
        try:
            request_data=json.loads(request.data)
            Log.logger.debug("Delete resource data is:" + request_data.__str__())
            resource_id=request_data.get('resource_id')
            resource_name = request_data.get('resource_name')
            resource_type = request_data.get('resource_type')
            del_os_ins_ip_list=request_data.get("os_ins_ip_list",[])
            vid_list = request_data.get("vid_list", [])
            set_flag = request_data.get('set_flag')
            cloud = request_data.get('cloud')
            syswin_project = request_data.get('syswin_project')
            namespace = request_data.get('namespace')
            resources = deal_del_request_data(resource_id,del_os_ins_ip_list)
            resources = resources.get('resources')
            unique_flag=str(uuid.uuid1())
            #删除虚机和卷
            if cloud == '2':
                #cloud2.0分为删除k8s上的应用和删除openstack上的虚机
                if resource_type == "app":
                    TaskManager.task_start(
                        SLEEP_TIME, TIMEOUT,
                        {'current_status': QUERY_INGRESS,
                         "unique_flag": unique_flag,
                         "del_os_ins_ip_list": del_os_ins_ip_list,
                         "set_flag": set_flag,
                         "resource_name": resource_name,
                         "resource_type": resource_type,
                         'syswin_project':syswin_project,
                         'namespace':namespace,
                         'resource_id':resource_id,
                         "dep_check_times": 0,
                         "igs_check_times": 0,
                         "vm_check_times":0,
                         },
                        delete_instance_and_query2, {})
                else:
                    for resource in resources:
                        TaskManager.task_start(
                            SLEEP_TIME, TIMEOUT,
                            {'current_status': QUERY_VOLUME2,
                             "unique_flag":unique_flag,
                             "del_os_ins_ip_list":del_os_ins_ip_list,
                             "set_flag":set_flag,
                             'syswin_project': syswin_project,
                             "vm_check_times": 0,
                             },
                             delete_instance_and_query2, resource)
                # 删除虚IP
                for port_id in vid_list:
                    delete_vip2(port_id)
            else:
                for resource in resources:
                    TaskManager.task_start(
                        SLEEP_TIME, TIMEOUT,
                        {'current_status': QUERY_VOLUME,
                         "unique_flag":unique_flag,
                         "del_os_ins_ip_list":del_os_ins_ip_list,
                         "set_flag":set_flag,
                         'syswin_project': syswin_project,
                         "vm_check_times": 0,
                         },
                         delete_instance_and_query, resource)
                #删除虚IP
                for port_id in vid_list:
                    delete_vip(port_id)
            # 删除构建日志
            delete_resource_log(resource_name)
        except Exception as e:
            err_msg=str(e)
            Log.logger.error(
                "[CRP] Resource delete failed, Exception:%s" % err_msg)
            code=400
            res = {
                "code": code,
                "result": {
                    "res": "failed",
                    "msg": err_msg
                }
            }
            return res, code
        else:
            code=202
            res = {
                "code": code,
                "result": {
                    "msg": "提交成功"
                }
            }
            return res, code


def delete_resource_log(resource_name):
    project_name = resource_name.split('_')[0]

    base_path = "{u}build_log/{p}/".format(
        u=configs[APP_ENV].UPLOAD_FOLDER, p=project_name)
    if not os.path.exists(base_path):
        return

    match_resource = "{r}_.".format(r=resource_name)
    for fl in os.listdir(base_path): 
        match = re.match(match_resource, fl)
        if match:
            os.remove(os.path.join(base_path, match.group()))

    if not os.listdir(base_path):
        os.rmdir(base_path)
    return


resource_set_api.add_resource(ResourceSet, '/sets')
resource_set_api.add_resource(ResourceDelete, '/deletes')
