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
        'uuid': '817d3140-0b82-4722-9816-3cee734f22b6',
        'name': 'mysqluop-80G-20170426',
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
# AVAILABILITY_ZONE
AVAILABILITY_ZONE_GENERAL = 'AZ_GENERAL'
AVAILABILITY_ZONE_SELF_SERVICE = 'AZ-SELF-SERVICE'
DEV_NETWORK_ID = 'c12740e6-33c8-49e9-b17d-6255bb10cd0c'

# res_callback
RES_CALLBACK = 'http://uop-test.syswin.com/api/res_callback/res'

# use localhost for ip is none
IP_NONE = "localhost"

RES_STATUS_OK = "ok"
RES_STATUS_FAIL = "fail"
RES_STATUS_DEFAULT = 'unreserved'

DEFAULT_USERNAME = "root"
DEFAULT_PASSWORD = "123456"


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
    return _create_instance(name, image_uuid, FLAVOR_1C2G, AVAILABILITY_ZONE_SELF_SERVICE, DEV_NETWORK_ID)
    # return _create_instance(name, image_uuid, FLAVOR_1C2G, AVAILABILITY_ZONE_GENERAL, DEV_NETWORK_ID)


# 依据镜像URL创建NovaDocker容器
def create_docker_by_url(name, image_url):
    err_msg, image_uuid = image_transit(image_url)
    if err_msg is None:
        Log.logger.debug("Transit harbor docker image success. The result glance image UUID is " + image_uuid)
        return None, _create_instance(name, image_uuid, DOCKER_FLAVOR_2C4G, AVAILABILITY_ZONE_GENERAL, DEV_NETWORK_ID)
    else:
        return err_msg, None


# 申请资源定时任务
def _create_resource_set(resource_id=None, resource_list=None, compute_list=None):
    uop_os_inst_id_list = []
    for resource in resource_list:
        instance_name = resource.get('instance_name')
        instance_id = resource.get('instance_id')
        instance_type = resource.get('instance_type')
        cpu = resource.get('cpu')
        mem = resource.get('mem')
        disk = resource.get('disk')
        quantity = resource.get('quantity')
        version = resource.get('version')

        for i in range(1, quantity+1, 1):
            osint_id = create_instance_by_type(instance_type, instance_name)
            uopinst_info = {
                               'uop_inst_id': instance_id,
                               'os_inst_id': osint_id
                           }
            uop_os_inst_id_list.append(uopinst_info)

    for compute in compute_list:
        instance_name = compute.get('instance_name')
        instance_id = compute.get('instance_id')
        cpu = compute.get('cpu')
        mem = compute.get('mem')
        image_url = compute.get('image_url')

        err_msg, osint_id = create_docker_by_url(instance_name, image_url)
        if err_msg is None:
            uopinst_info = {
                   'uop_inst_id': instance_id,
                   'os_inst_id': osint_id
               }
            uop_os_inst_id_list.append(uopinst_info)
        else:
            Log.logger.debug(err_msg)
            result_inst_id_list = []
            # 删除全部
            _rollback_all(resource_id, uop_os_inst_id_list, result_inst_id_list)
            uop_os_inst_id_list = []

    return uop_os_inst_id_list


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
def _rollback_all(resource_id, uop_os_inst_id_list, result_uop_os_inst_id_list):
    nova_client = OpenStack.nova_client
    # fail_list = list(set(uop_os_inst_id_list) - set(result_uop_os_inst_id_list))
    fail_list = _uop_os_list_sub(uop_os_inst_id_list, result_uop_os_inst_id_list)
    Log.logger.debug("Resource ID " + resource_id.__str__() + " have one or more instance create failed." +
                     " Successful instance id set is " + result_uop_os_inst_id_list[:].__str__() +
                     " Failed instance id set is " + fail_list[:].__str__())
    # 删除全部，完成rollback
    for uop_os_inst_id in uop_os_inst_id_list:
        nova_client.servers.delete(uop_os_inst_id['os_inst_id'])
    Log.logger.debug("Resource ID " + resource_id.__str__() + " rollback done.")


# _uop_os_list_sub
def _uop_os_list_sub(uop_os_inst_id_list, result_uop_os_inst_id_list):
    uop_os_inst_id_wait_query = copy.deepcopy(uop_os_inst_id_list)
    for i in result_uop_os_inst_id_list:
        for j in uop_os_inst_id_wait_query:
            if j['os_inst_id'] == i['os_inst_id']:
                uop_os_inst_id_wait_query.remove(j)
    return uop_os_inst_id_wait_query


# 向OpenStack查询已申请资源的定时任务
def _query_resource_set_status(task_id=None, result_list=None, uop_os_inst_id_list=None, req_dict=None):
    if result_list.__len__() == 0:
        result_uop_os_inst_id_list = []
        result_info_list = []
        result_inst_id_dict = {
                                  'type': 'id',
                                  'list': result_uop_os_inst_id_list
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
                result_uop_os_inst_id_list = res_dict['list']
            elif res_dict['type'] == 'info':
                result_info_list = res_dict['list']

    rollback_flag = False
    # uop_os_inst_id_wait_query = list(set(uop_os_inst_id_list) - set(result_uop_os_inst_id_list))
    uop_os_inst_id_wait_query = _uop_os_list_sub(uop_os_inst_id_list, result_uop_os_inst_id_list)

    Log.logger.debug("Query Task ID "+task_id.__str__()+", remain "+uop_os_inst_id_wait_query[:].__str__())
    Log.logger.debug("Test Task Scheduler Class result_uop_os_inst_id_list object id is " +
                     id(result_uop_os_inst_id_list).__str__() +
                     ", Content is " + result_uop_os_inst_id_list[:].__str__())
    nova_client = OpenStack.nova_client
    for uop_os_inst_id in uop_os_inst_id_wait_query:
        inst = nova_client.servers.get(uop_os_inst_id['os_inst_id'])
        Log.logger.debug("Task ID "+task_id.__str__()+" query Instance ID "+uop_os_inst_id['os_inst_id']+" Status is "+inst.status)
        if inst.status == 'ACTIVE':
            _ips = _get_ip_from_instance(inst)
            _data = {
                        'uop_inst_id': uop_os_inst_id['uop_inst_id'],
                        'os_inst_id': uop_os_inst_id['os_inst_id'],
                        'ip': _ips.pop() if _ips.__len__() >= 1 else '',
                    }
            result_info_list.append(_data)
            Log.logger.debug("Instance Info: " + _data.__str__())
            result_uop_os_inst_id_list.append(uop_os_inst_id)
        if inst.status == 'ERROR':
            # 置回滚标志位
            Log.logger.debug("ERROR Instance Info: " + inst.to_dict().__str__())
            rollback_flag = True

    if result_uop_os_inst_id_list.__len__() == uop_os_inst_id_list.__len__():
        # TODO(thread exit): 执行成功调用UOP CallBack停止定时任务退出任务线程
        Log.logger.debug("Task ID " + task_id.__str__() + " all instance create success." +
                         " instance id set is " + result_uop_os_inst_id_list[:].__str__() +
                         " instance info set is "+result_info_list[:].__str__())
        for info in result_info_list:
            if info["uop_inst_id"] == req_dict["container_inst_id"]:
                req_dict["container_ip"] = info["ip"]
            if info["uop_inst_id"] == req_dict["mysql_inst_id"]:
                req_dict["mysql_ip"] = info["ip"]
            if info["uop_inst_id"] == req_dict["redis_inst_id"]:
                req_dict["redis_ip"] = info["ip"]
            if info["uop_inst_id"] == req_dict["mongodb_inst_id"]:
                req_dict["mongodb_ip"] = info["ip"]
        request_res_callback(RES_STATUS_OK, req_dict)
        Log.logger.debug("Call UOP CallBack Post Success Info.")
        # 停止定时任务并退出
        TaskManager.task_exit(task_id)

    # 回滚全部资源和容器
    if rollback_flag:
        # 删除全部
        _rollback_all(task_id, uop_os_inst_id_list, result_uop_os_inst_id_list)

        # TODO(thread exit): 执行失败调用UOP CallBack停止定时任务退出任务线程
        request_res_callback(RES_STATUS_FAIL, req_dict)
        Log.logger.debug("Call UOP CallBack Post Fail Info.")
        # 停止定时任务并退出
        TaskManager.task_exit(task_id)


# request UOP res_callback
def request_res_callback(status, req_dict):
    # project_id, resource_name,under_name, resource_id, domain,
    # container_name, image_addr, stardand_ins,cpu, memory, ins_id,
    # mysql_username, mysql_password, mysql_port, mysql_ip,
    # redis_username, redis_password, redis_port, redis_ip,
    # mongodb_username, mongodb_password, mongodb_port, mongodb_ip
    """
    :param req_dict: req字段字典
    API JOSN:
{
    "unit_name":"部署单元名称",
    "unit_id":"部署单元编号",
    "unit_des":"部署单元描述",
    "user_id":"创建人工号",
    "username":"创建人姓名",
    "department":"创建人归属部门",
    "created_time":"部署单元创建时间",
    "resource_id": "资源id",
    "resource_name": "资源名",
    "env": "开发测试生产环境",
    "domain": "qitoon.syswin.com",
    "status": "成功",
    "container": {
        "username": "root",
        "password": "123456",
        "ip": "容器IP",
        "container_name": "容器名称",
        "image_addr": "镜像地址",
        "cpu": "2",
        "memory": "4",
        "ins_id": "实例id"
    },
    "db_info": {
        "mysql": {
            "ins_id": "mysql_inst_id",
            "username": "数据库名",
            "password": "密码",
            "port": "端口",
            "ip": "MySQLIP"
        },
        "redis": {
            "ins_id": "redis_inst_id",
            "username": "数据库名",
            "password": "密码",
            "port": "端口",
            "ip": "RedisIP"
        },
        "mongodb": {
            "ins_id": "mongodb_inst_id",
            "username": "数据库名",
            "password": "密码",
            "port": "端口",
            "ip": "MongodbIP"
        }
    }
}
    """
    data = {}
    data["unit_name"] = req_dict["unit_name"]
    data["unit_id"] = req_dict["unit_id"]
    data["unit_des"] = req_dict["unit_des"]
    data["user_id"] = req_dict["user_id"]
    data["username"] = req_dict["username"]
    data["department"] = req_dict["department"]
    data["created_time"] = req_dict["created_time"]
    data["resource_id"] = req_dict["resource_id"]
    data["resource_name"] = req_dict["resource_name"]
    data["env"] = req_dict["env"]
    data["domain"] = req_dict["domain"]
    data["status"] = status

    container = {}
    if req_dict["container_ip"] is not IP_NONE:
        container["username"] = req_dict["container_username"]
        container["password"] = req_dict["container_password"]
        container["ip"] = req_dict["container_ip"]
        container["container_name"] = req_dict["container_name"]
        container["image_addr"] = req_dict["image_addr"]
        container["cpu"] = req_dict["cpu"]
        container["memory"] = req_dict["memory"]
        container["ins_id"] = req_dict["container_inst_id"]
    data["container"] = container

    db_info = {}
    mysql = {}
    mysql["ins_id"] = req_dict["mysql_inst_id"]
    mysql["username"] = req_dict["mysql_username"]
    mysql["password"] = req_dict["mysql_password"]
    mysql["port"] = req_dict["mysql_port"]
    mysql["ip"] = req_dict["mysql_ip"]

    redis = {}
    redis["ins_id"] = req_dict["redis_inst_id"]
    redis["username"] = req_dict["redis_username"]
    redis["password"] = req_dict["redis_password"]
    redis["port"] = req_dict["redis_port"]
    redis["ip"] = req_dict["redis_ip"]

    mongodb = {}
    mongodb["ins_id"] = req_dict["mongodb_inst_id"]
    mongodb["username"] = req_dict["mongodb_username"]
    mongodb["password"] = req_dict["mongodb_password"]
    mongodb["port"] = req_dict["mongodb_port"]
    mongodb["ip"] = req_dict["mongodb_ip"]

    if mysql["ip"] is not IP_NONE:
        db_info["mysql"] = mysql
    if redis["ip"] is not IP_NONE:
        db_info["redis"] = redis
    if mongodb["ip"] is not IP_NONE:
        db_info["mongodb"] = mongodb
    data["db_info"] = db_info

    data_str = json.dumps(data)
    Log.logger.debug("UOP res_callback Request Body is: "+data_str)
    res = requests.post(RES_CALLBACK, data=data_str)
    Log.logger.debug(res.status_code)
    Log.logger.debug(res.content)
    ret = eval(res.content.decode('unicode_escape'))


# 创建资源集合定时任务，成功或失败后调用UOP资源预留CallBack（目前仅允许全部成功或全部失败，不允许部分成功）
def _create_resource_set_and_query(task_id, result_list, resource_id, resource_list, compute_list, req_dict):
    try:
        if result_list.__len__() == 0:
            result_sub_is_create_resource_done_dict = {'is_create_done': False}
            result_sub_result_list = []
            uop_os_inst_id_list = []
            result_is_create_resource_done_dict = {
                                      'type': 'is_create_done',
                                      'nested': result_sub_is_create_resource_done_dict
                                  }
            result_sub_result_dict = {
                                   'type': 'sub_result',
                                   'nested': result_sub_result_list
                               }
            result_sub_uop_os_inst_id_dict = {
                                   'type': 'sub_uop_os_inst_id',
                                   'nested': uop_os_inst_id_list
                               }
            result_list.append(result_is_create_resource_done_dict)
            result_list.append(result_sub_result_dict)
            result_list.append(result_sub_uop_os_inst_id_dict)
            Log.logger.debug('uop_os_inst_id_list\'s object id is :')
            Log.logger.debug(id(uop_os_inst_id_list))
        else:
            for res_dict in result_list:
                if res_dict['type'] == 'is_create_done':
                    result_sub_is_create_resource_done_dict = res_dict['nested']
                elif res_dict['type'] == 'sub_result':
                    result_sub_result_list = res_dict['nested']
                elif res_dict['type'] == 'sub_uop_os_inst_id':
                    uop_os_inst_id_list = res_dict['nested']
                    Log.logger.debug('uop_os_inst_id_list\'s object id is :')
                    Log.logger.debug(id(uop_os_inst_id_list))

        if result_sub_is_create_resource_done_dict['is_create_done'] is not True:
            temp_uop_os_inst_id_list = _create_resource_set(resource_id, resource_list, compute_list)
            for temp in temp_uop_os_inst_id_list:
                uop_os_inst_id_list.append(temp)
                Log.logger.debug('uop_os_inst_id_list\'s object id is :')
                Log.logger.debug(id(uop_os_inst_id_list))

            result_sub_is_create_resource_done_dict['is_create_done'] = True
            if uop_os_inst_id_list.__len__() == 0:
                # TODO(thread exit): 执行失败调用UOP CallBack停止定时任务退出任务线程
                request_res_callback(RES_STATUS_FAIL, req_dict)
                Log.logger.debug("Call UOP CallBack Post Fail Info.")
                # 停止定时任务并退出
                TaskManager.task_exit(task_id)
        else:
            if uop_os_inst_id_list.__len__() == 0:
                # TODO(thread exit): 执行失败调用UOP CallBack停止定时任务退出任务线程
                request_res_callback(RES_STATUS_FAIL, req_dict)
                Log.logger.debug("Call UOP CallBack Post Fail Info.")
                # 停止定时任务并退出
                TaskManager.task_exit(task_id)
            else:
                Log.logger.debug("Test API handler result_list object id is " + id(result_sub_result_list).__str__() +
                                 ", Content is " + result_sub_result_list[:].__str__())
                _query_resource_set_status(task_id, result_sub_result_list, uop_os_inst_id_list, req_dict)
    except Exception as e:
        Log.logger.Error(e.message)


# res_set REST API Controller
class ResourceSet(Resource):
    @classmethod
    def post(cls):
        """
        API JOSN:
{
    "unit_name" : "部署单元名称",
    "unit_id" : "部署单元编号",
    "unit_des" : "部署单元描述",
    "user_id" : "创建人工号",
    "username" : "创建人姓名",
    "department" : "创建人归属部门",
    "created_time" : "部署单元创建时间",
    "resource_id": "资源id",
    "resource_name": "资源名",
    "env": "开发测试生产环境",
    "domain": "qitoon.syswin.com",
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
            parser = reqparse.RequestParser()
            parser.add_argument('unit_name', type=str)
            parser.add_argument('unit_id', type=str)
            parser.add_argument('unit_des', type=str)
            parser.add_argument('user_id', type=str)
            parser.add_argument('username', type=str)
            parser.add_argument('department', type=str)
            parser.add_argument('created_time', type=str)

            parser.add_argument('resource_id', type=str)
            parser.add_argument('resource_name', type=str)
            parser.add_argument('env', type=str)
            parser.add_argument('domain', type=str)
            parser.add_argument('resource_list', type=list, location='json')
            parser.add_argument('compute_list', type=list, location='json')
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
            resource_list = args.resource_list
            compute_list = args.compute_list

            for resource in resource_list:
                instance_name = resource.get('instance_name')
                instance_id = resource.get('instance_id')
                instance_type = resource.get('instance_type')
                cpu = resource.get('cpu')
                mem = resource.get('mem')
                disk = resource.get('disk')
                quantity = resource.get('quantity')
                version = resource.get('version')

                if instance_type == 'mysql':
                    req_dict["mysql_inst_id"] = instance_id
                if instance_type == 'redis':
                    req_dict["redis_inst_id"] = instance_id
                if instance_type == 'mongo':
                    req_dict["mongodb_inst_id"] = instance_id

            for compute in compute_list:
                instance_name = compute.get('instance_name')
                instance_id = compute.get('instance_id')
                cpu = compute.get('cpu')
                mem = compute.get('mem')
                image_url = compute.get('image_url')

                req_dict["container_name"] = instance_name
                req_dict["image_addr"] = image_url
                req_dict["cpu"] = cpu
                req_dict["memory"] = mem
                req_dict["container_inst_id"] = instance_id

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
            req_dict["status"] = RES_STATUS_DEFAULT

            # init default data
            req_dict["container_username"] = DEFAULT_USERNAME
            req_dict["container_password"] = DEFAULT_PASSWORD
            req_dict["container_ip"] = IP_NONE
            req_dict["mysql_username"] = DEFAULT_USERNAME
            req_dict["mysql_password"] = DEFAULT_PASSWORD
            req_dict["mysql_port"] = "3316"
            req_dict["mysql_ip"] = IP_NONE
            req_dict["redis_username"] = DEFAULT_USERNAME
            req_dict["redis_password"] = DEFAULT_PASSWORD
            req_dict["redis_port"] = "6379"
            req_dict["redis_ip"] = IP_NONE
            req_dict["mongodb_username"] = DEFAULT_USERNAME
            req_dict["mongodb_password"] = DEFAULT_PASSWORD
            req_dict["mongodb_port"] = "27017"
            req_dict["mongodb_ip"] = IP_NONE

            result_list = []
            Log.logger.debug('req_dict\'s object id is :')
            Log.logger.debug(id(req_dict))
            Log.logger.debug('result_list\'s object id is :')
            Log.logger.debug(id(result_list))
            # TODO(TaskManager.task_start()): 定时任务示例代码
            TaskManager.task_start(SLEEP_TIME, TIMEOUT, result_list,
                                   _create_resource_set_and_query, resource_id, resource_list, compute_list, req_dict)
        except Exception as e:
            # exception return http code 500 (Internal Server Error)
            code = 500
            msg = e.message

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


resource_set_api.add_resource(ResourceSet, '/sets')
