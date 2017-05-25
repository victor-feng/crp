# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource

from crp.taskmgr import *
from crp.res_set import resource_set_blueprint
from crp.res_set.errors import resource_set_errors
from crp.log import Log
from crp.openstack import OpenStack
from crp.utils.docker_tools import image_transit
import json


resource_set_api = Api(resource_set_blueprint, errors=resource_set_errors)


TIMEOUT = 500
SLEEP_TIME = 3


images_dict = {
    'mysql': {
        'uuid': '9d9c2029-cd1e-41d3-ab2e-9b1ab6eca7df',
        'name': 'mysqlsas-50G-20170428',
    },
    'redis': {
        'uuid': '3da55e5b-814c-4935-abf0-1469ae606286',
        'name': 'redis-50G-20170428',
    },
    'mongo': {
        'uuid': '95863650-6816-4588-846a-c0423b5baae0',
        'name': 'mongosas-50G-20170428',
    },
}


# cirros-0.3.3
IMAGE_MINI = 'c63884fb-399b-400c-a5fd-810cefb50dc0'
# mini
FLAVOR_MINI = 'aadb6488-a64f-4868-82dd-7b832cd047ac'
# scm2-dev--1C2G80G
FLAVOR_1C2G = 'scm2-dev--1C2G80G'
# docker-2C4G25G
DOCKER_FLAVOR_2C4G = 'e90d8d25-c5c7-46d7-ba4e-2465a5b1d266'
# AVAILABILITY_ZONE = 'AZ_GENERAL'
AVAILABILITY_ZONE = 'AZ-SELF-SERVICE'
DEV_NETWORK_ID = 'c12740e6-33c8-49e9-b17d-6255bb10cd0c'

# res_callback
RES_CALLBACK = 'http://uop-test.syswin.com/api/res_callback/res'


# 向OpenStack申请资源
def _create_instance(name, image, flavor, availability_zone, network_id):
    nova_client = OpenStack.nova_client
    # ints = nova_client.servers.list()
    # Log.logger.debug(ints)
    # def create(self, name, image, flavor, meta=None, files=None,
    #            reservation_id=None, min_count=None,
    #            max_count=None, security_groups=None, userdata=None,
    #            key_name=None, availability_zone=None,
    #            block_device_mapping=None, block_device_mapping_v2=None,
    #            nics=None, scheduler_hints=None,
    #            config_drive=None, disk_config=None, **kwargs):

    nics_list = []
    nic_info = {'net-id': network_id}
    nics_list.append(nic_info)
    int = nova_client.servers.create(name, image, flavor,
                                     availability_zone=availability_zone,
                                     nics=nics_list)
    Log.logger.debug(int)
    Log.logger.debug(int.id)

    return int.id


# 依据资源类型创建资源
def create_instance_by_type(ins_type, name):
    image = images_dict.get(ins_type)
    image_uuid = image.get('uuid')
    Log.logger.debug("Select Image UUID: "+image_uuid+" by Instance Type "+ins_type)
    return _create_instance(name, image_uuid, FLAVOR_1C2G, AVAILABILITY_ZONE, DEV_NETWORK_ID)


# 依据镜像URL创建NovaDocker容器
def create_docker_by_url(name, image_url):
    err_msg, image_uuid = image_transit(image_url)
    if err_msg is None:
        Log.logger.debug("Transit harbor docker image success. The result glance image UUID is " + image_uuid)
        return None, _create_instance(name, image_uuid, DOCKER_FLAVOR_2C4G, AVAILABILITY_ZONE, DEV_NETWORK_ID)
    else:
        return err_msg, None


# 申请资源定时任务
def _create_resource_set(task_id=None, resource_list=None, compute_list=None):
    osins_id_list = []
    for resource in resource_list:
        ins_name = resource.get('res_name')
        ins_id = resource.get('res_id')
        # ins_id = str(uuid.uuid1())
        ins_type = resource.get('res_type')
        cpu = resource.get('cpu')
        mem = resource.get('mem')
        disk = resource.get('disk')
        quantity = resource.get('quantity')
        version = resource.get('version')

        osint_id = create_instance_by_type(ins_type, ins_name)
        osins_id_list.append(osint_id)

    for compute in compute_list:
        ins_name = compute.get('ins_name')
        ins_id = compute.get('ins_id')
        # ins_id = str(uuid.uuid1())
        cpu = compute.get('cpu')
        mem = compute.get('mem')
        url = compute.get('url')

        err_msg, osint_id = create_docker_by_url(ins_name, url)
        if err_msg is None:
            osins_id_list.append(osint_id)
        else:
            Log.logger.debug(err_msg)
            result_inst_id_list = []
            # 删除全部
            _rollback_all(task_id, osins_id_list, result_inst_id_list)
            osins_id_list = []

    return osins_id_list


def _get_ip_from_instance(server):
    ips_address = []
    for _, ips in server.addresses.items():
        for ip in ips:
            if isinstance(ip, dict):
                if ip.has_key('addr'):
                    ip_address = ip['addr']
                    ips_address.append(ip_address)
    return ips_address


# 回滚删除全部资源和容器
def _rollback_all(task_id, osins_id_list, result_inst_id_list):
    nova_client = OpenStack.nova_client
    fail_list = list(set(osins_id_list) - set(result_inst_id_list))
    Log.logger.debug("Task ID " + task_id.__str__() + " have one or more instance create failed." +
                     " Successful instance id set is " + result_inst_id_list[:].__str__() +
                     " Failed instance id set is " + fail_list[:].__str__())
    # 删除全部，完成rollback
    for inst_id in osins_id_list:
        nova_client.servers.delete(inst_id)
    Log.logger.debug("Task ID " + task_id.__str__() + " rollback done.")


# 向OpenStack查询已申请资源的定时任务
def _query_resource_set_status(task_id=None, result_list=None, osins_id_list=None, req_dict=None):
    if result_list.__len__() == 0:
        result_inst_id_list = []
        result_info_list = []
        result_inst_id_dict = {
                                  'type': 'id',
                                  'list': result_inst_id_list
                              }
        result_info_dict = {
                               'type': 'info',
                               'list': result_info_list
                           }
        result_list.append(result_inst_id_dict)
        result_list.append(result_info_dict)
    else:
        for res_dict in result_list:
            if res_dict['type'] == 'id':
                result_inst_id_list = res_dict['list']
            elif res_dict['type'] == 'info':
                result_info_list = res_dict['list']

    rollback_flag = False
    os_inst_id_wait_query = list(set(osins_id_list) - set(result_inst_id_list))
    Log.logger.debug("Query Task ID "+task_id.__str__()+", remain "+os_inst_id_wait_query[:].__str__())
    Log.logger.debug("Test Task Scheduler Class result_inst_id_list object id is " + id(result_inst_id_list).__str__() +
                     ", Content is " + result_inst_id_list[:].__str__())
    nova_client = OpenStack.nova_client
    for os_inst_id in os_inst_id_wait_query:
        inst = nova_client.servers.get(os_inst_id)
        Log.logger.debug("Task ID "+task_id.__str__()+" query Instance ID "+os_inst_id+" Status is "+inst.status)
        if inst.status == 'ACTIVE':
            _ips = _get_ip_from_instance(inst)
            _data = {
                        'uop_ins_id': req_dict["ins_id"],
                        'os_inst_id': os_inst_id,
                        'ip': _ips.pop() if _ips.__len__() >= 1 else '',
                    }
            result_info_list.append(_data)
            Log.logger.debug("Instance Info: " + _data.__str__())
            result_inst_id_list.append(os_inst_id)
        if inst.status == 'ERROR':
            # 置回滚标志位
            Log.logger.debug("ERROR Instance Info: " + inst.to_dict().__str__())
            rollback_flag = True

    if result_inst_id_list.__len__() == osins_id_list.__len__():
        # TODO(thread exit): 执行成功调用UOP CallBack停止定时任务退出任务线程
        Log.logger.debug("Task ID " + task_id.__str__() + " all instance create success." +
                         " instance id set is " + result_inst_id_list[:].__str__() +
                         " instance info set is "+result_info_list[:].__str__())
        for info in result_info_list:
            if info["uop_ins_id"] == req_dict["container_ins_id"]:
                req_dict["container_ip"] = info["ip"]
            if info["uop_ins_id"] == req_dict["mysql_ins_id"]:
                req_dict["mysql_ip"] = info["ip"]
            if info["uop_ins_id"] == req_dict["redis_ins_id"]:
                req_dict["redis_ip"] = info["ip"]
            if info["uop_ins_id"] == req_dict["mongodb_ins_id"]:
                req_dict["mongodb_ip"] = info["ip"]
        request_res_callback(req_dict)
        Log.logger.debug("Call UOP CallBack Post Success Info.")
        TaskManager.task_exit(task_id)

    # 回滚全部资源和容器
    if rollback_flag:
        # 删除全部
        _rollback_all(task_id, osins_id_list, result_inst_id_list)

        # TODO(thread exit): 执行失败调用UOP CallBack停止定时任务退出任务线程
        Log.logger.debug("Call UOP CallBack Post Fail Info.")

        # 停止定时任务并退出
        TaskManager.task_exit(task_id)


# request UOP res_callback
def request_res_callback(req_dict):
    # project_id, resource_name,under_name, resource_id, domain,
    # container_name, image_addr, stardand_ins,cpu, memory, ins_id,
    # mysql_username, mysql_password, mysql_port, mysql_ip,
    # redis_username, redis_password, redis_port, redis_ip,
    # mongodb_username, mongodb_password, mongodb_port, mongodb_ip
    """
    :param req_dict: req字段字典
    API JOSN:
    {
        "project_id": "项目id",
        "project_name": [
            {
                "resource_name": "资源名称",
                "under_name": "所属项目",
                "resource_id": "资源id",
                "domain": "域名",
                "container": {
                    "container_name": "容器名称",
                    "image_addr": "镜像地址",
                    "stardand_ins": "实例规格",
                    "cpu": "2",
                    "memory": "4",
                    "ins_id": "实例id"
                },
                "db_info": {
                    "mysql": {
                        "username": "数据库名",
                        "password": "密码",
                        "port": "端口",
                        "ip": ""
                    },
                    "redis": {
                        "username": "数据库名",
                        "password": "密码",
                        "port": "端口",
                        "ip": ""
                    },
                    "mongodb": {
                        "username": "数据库名",
                        "password": "密码",
                        "port": "端口",
                        "ip": ""
                    }
                }
            }
        ]
    }
    """
    data = {}
    data["project_id"] = req_dict["project_id"]

    project_name_list = []
    project_name = {}
    project_name["resource_name"] = req_dict["resource_name"]
    project_name["under_name"] = req_dict["under_name"]
    project_name["resource_id"] = req_dict["resource_id"]
    project_name["domain"] = req_dict["domain"]

    container = {}
    container["container_name"] = req_dict["container_name"]
    container["image_addr"] = req_dict["image_addr"]
    container["stardand_ins"] = req_dict["stardand_ins"]
    container["cpu"] = req_dict["cpu"]
    container["memory"] = req_dict["memory"]
    container["ins_id"] = req_dict["ins_id"]
    project_name["container"] = container

    db_info = {}
    mysql = {}
    mysql["username"] = req_dict["mysql_username"]
    mysql["password"] = req_dict["mysql_password"]
    mysql["port"] = req_dict["mysql_port"]
    mysql["ip"] = req_dict["mysql_ip"]

    redis = {}
    redis["username"] = req_dict["redis_username"]
    redis["password"] = req_dict["redis_password"]
    redis["port"] = req_dict["redis_port"]
    redis["ip"] = req_dict["redis_ip"]

    mongodb = {}
    mongodb["username"] = req_dict["mongodb_username"]
    mongodb["password"] = req_dict["mongodb_password"]
    mongodb["port"] = req_dict["mongodb_port"]
    mongodb["ip"] = req_dict["mongodb_ip"]

    db_info["mysql"] = mysql
    db_info["redis"] = redis
    db_info["mongodb"] = mongodb
    project_name["db_info"] = db_info

    project_name_list.append(project_name)

    data["project_name_list"] = project_name_list

    data_str = json.dumps(data)
    res = requests.post(RES_CALLBACK, data=data_str)
    ret = eval(res.content.decode('unicode_escape'))
    Log.logger.debug(res.status_code)
    Log.logger.debug(res.content)


# res_set REST API Controller
class ResourceSet(Resource):
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('resource_name', type=str)
        parser.add_argument('project', type=str)
        parser.add_argument('project_id', type=str)
        parser.add_argument('department', type=str)
        # parser.add_argument('department_id', type=str)
        parser.add_argument('res_id', type=str)
        parser.add_argument('user_name', type=str)
        parser.add_argument('user_id', type=str)
        parser.add_argument('domain', type=str)
        parser.add_argument('env', type=str)
        parser.add_argument('application_status', type=str)
        # parser.add_argument('approval_status', type=str)
        parser.add_argument('resource_list', type=list, location='json')
        parser.add_argument('compute_list', type=list, location='json')
        args = parser.parse_args()

        req_dict = {}

        resource_name = args.resource_name
        project = args.project
        project_id = args.project_id
        department = args.department
        department_id = '1'
        res_id = args.res_id
        # res_id = str(uuid.uuid1())
        user_name = args.user_name
        user_id = args.user_id
        domain = args.domain
        env = args.env
        application_status = args.application_status
        # approval_status = args.approval_status
        resource_list = args.resource_list
        compute_list = args.compute_list

        for resource in resource_list:
            ins_name = resource.get('res_name')
            ins_id = resource.get('res_id')
            # ins_id = str(uuid.uuid1())
            ins_type = resource.get('res_type')
            cpu = resource.get('cpu')
            mem = resource.get('mem')
            disk = resource.get('disk')
            quantity = resource.get('quantity')
            version = resource.get('version')

        for compute in compute_list:
            ins_name = compute.get('ins_name')
            ins_id = compute.get('ins_id')
            # ins_id = str(uuid.uuid1())
            cpu = compute.get('cpu')
            mem = compute.get('mem')
            url = compute.get('url')

        Log.logger.debug(resource_list)
        Log.logger.debug(compute_list)

        req_dict["project_id"] = project_id
        req_dict["resource_name"] = resource_name
        req_dict["under_name"] = project
        req_dict["resource_id"] = res_id
        req_dict["domain"] = domain
        req_dict["container_name"] = ins_name
        req_dict["image_addr"] = url
        req_dict["stardand_ins"] = "2C4G"
        req_dict["cpu"] = cpu
        req_dict["memory"] = mem
        req_dict["ins_id"] = ins_id
        req_dict["mysql_username"] = "root"
        req_dict["mysql_password"] = "123456"
        req_dict["mysql_port"] = "3306"
        req_dict["mysql_ip"] = "localhost"
        req_dict["redis_username"] = "root"
        req_dict["redis_password"] = "123456"
        req_dict["redis_port"] = "6379"
        req_dict["redis_ip"] = "localhost"
        req_dict["mongodb_username"] = "root"
        req_dict["mongodb_password"] = "123456"
        req_dict["mongodb_port"] = "27017"
        req_dict["mongodb_ip"] = "localhost"

        osins_id_list = _create_resource_set(res_id, resource_list, compute_list)
        if osins_id_list.__len__() == 0:
            # TODO(callback): 执行失败调用UOP CallBack
            pass
        else:
            # TODO(TaskManager.task_start()): 定时任务示例代码
            result_list = []
            Log.logger.debug("Test API handler result_list object id is " + id(result_list).__str__() +
                             ", Content is " + result_list[:].__str__())
            TaskManager.task_start(SLEEP_TIME, TIMEOUT, result_list, _query_resource_set_status, osins_id_list, req_dict)

        # return http code 202 (Accepted)
        res_id = 'testid'
        res = {
            'code': 202,
            'result': {
                'res': 'success',
                'msg': 'Create Resource Set Accepted.',
                'res_id': res_id,
                'res_name': resource_name
            }
        }

        return res, 202


resource_set_api.add_resource(ResourceSet, '/sets')
