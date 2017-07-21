# -*- coding: utf-8 -*-
import os
import json
import subprocess
import time
from crp.taskmgr import *
from crp.res_set import resource_set_blueprint
from crp.res_set.errors import resource_set_errors
from crp.log import Log
from crp.openstack import OpenStack
from crp.utils.docker_tools import image_transit
from crp.dns.dns_api import DnsConfig
import requests
from transitions import Machine
from flask_restful import reqparse, Api, Resource



resource_set_api = Api(resource_set_blueprint, errors=resource_set_errors)

quantity = 0
TIMEOUT = 500
SLEEP_TIME = 3
GLOBAL_MONGO_CLUSTER_IP = ['172.28.36.230', '172.28.36.23', '172.28.36.231', '172.28.36.231']

images_dict = {
    'mysql': {
        'uuid': '54291935-a8af-4f56-bdfd-9f1758307f3e',
        'name': 'mysqlsas-80G-20170627',
    },
    'redis': {
        'uuid': '3da55e5b-814c-4935-abf0-1469ae606286',
        'name': 'redis-50G-20170428',
    },
    'mongodb': {
        'uuid': '95863650-6816-4588-846a-c0423b5baae0',
        'name': 'mongosas-50G-20170428',
    },
    'mycat': {
        'uuid': '59a5022b-3c46-47ec-8e97-b63edc4b7be0',
        'name': 'mycat-50G-20170628'
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
AVAILABILITY_ZONE_AZ_UOP = 'AZ_UOP'
DEV_NETWORK_ID = '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
OS_EXT_PHYSICAL_SERVER_ATTR = 'OS-EXT-SRV-ATTR:host'

# res_callback
RES_CALLBACK = 'http://uop-dev.syswin.com/api/res_callback/res'

# use localhost for ip is none
IP_NONE = "localhost"
# use localhost for physical_server is none
PHYSICAL_SERVER_NONE = "localhost"

RES_STATUS_OK = "ok"
RES_STATUS_FAIL = "fail"
RES_STATUS_DEFAULT = 'unreserved'

DEFAULT_USERNAME = "root"
DEFAULT_PASSWORD = "123456"


class ResourceProvider(object):
    # Define some states.
    states = ['init', 'success', 'fail', 'rollback', 'stop', 'create', 'query']

    # Define transitions.
    transitions = [
        {'trigger': 'success', 'source': 'query', 'dest': 'success', 'after': 'do_success'},
        {'trigger': 'fail', 'source': 'rollback', 'dest': 'fail', 'after': 'do_fail'},
        {'trigger': 'rollback', 'source': ['create', 'query'], 'dest': 'rollback', 'after': 'do_rollback'},
        {'trigger': 'stop', 'source': ['success', 'fail'], 'dest': 'stop', 'after': 'do_stop'},
        {'trigger': 'create', 'source': 'init', 'dest': 'create', 'after': 'do_create_instance'},
        {'trigger': 'query', 'source': ['create', 'query'], 'dest': 'query', 'after': 'do_query_resource_set_status'},
        {'trigger': 'app_push', 'source': ['success', 'fail'], 'dest': 'nginx_push', 'after':'do_push_nginx_config'}
    ]

    def __init__(self, resource_id, resource_list, compute_list, req_dict):
        # Initialize the variable
        self.task_id = None
        self.resource_id = resource_id
        self.resource_list = resource_list
        self.compute_list = compute_list
        self.req_dict = req_dict
        self.is_rollback = False
        self.result_inst_id_list = []
        self.uop_os_inst_id_list = []
        self.result_info_list = []
        self.ip_list = []

        # Initialize the state machine
        self.machine = Machine(model=self,
                               states=ResourceProvider.states,
                               transitions=ResourceProvider.transitions,
                               initial='init')

    def set_task_id(self, task_id):
        self.task_id = task_id

    def do_success(self):
        # 执行成功调用UOP CallBack，提交成功
        Log.logger.debug("Query Task ID " + self.task_id.__str__() + " all instance create success." +
                         " instance id set is " + self.result_inst_id_list[:].__str__() +
                         " instance info set is " + self.result_info_list[:].__str__())
        redis_master_slave = ['slave','master']
        mysql_master_slave = ['slave2', 'slave1', 'master']
        mysql_lvs = ['lvs2', 'lvs1']
        redis_ips = []
        mysql_cluster = False
        mysql_cluster_ip_info = []
        mysql_cluster_ip_lvs = []
        mongo_ips = []
        for info in self.result_info_list:
            uop_inst_id = info["uop_inst_id"]
            uop_inst_name = info["uop_inst_name"]
            os_inst_id = info["os_inst_id"]
            instance = {
                'ip': info["ip"],
                'server_name': uop_inst_name,
                'physical_server': info["physical_server"],
                'username': DEFAULT_USERNAME,
                'password': DEFAULT_PASSWORD,
            }
            if self.req_dict["mysql_cluster"].get('ins_id') and uop_inst_id == self.req_dict["mysql_cluster"]['ins_id']:
                instance['port'] = "3316"
                if uop_inst_name.endswith('_4') or uop_inst_name.endswith('_5'):
                    instance['dbtype'] =mysql_lvs.pop()
                    mysql_cluster = True
                    mysql_cluster_ip_lvs.append((uop_inst_name, info["ip"]))
                else:
                    instance['dbtype'] = mysql_master_slave.pop()
                    mysql_cluster_ip_info.append((uop_inst_name, info["ip"]))
                if not self.req_dict["mysql_cluster"].get('vip'):
                    _, vip1 = create_vip_port(uop_inst_id)
                    _, vip2 = create_vip_port(uop_inst_id)
                    self.req_dict["mysql_cluster"]['vip'] = [vip1, vip2]
                self.req_dict["mysql_cluster"]['instance'].append(instance)
            if self.req_dict["redis_cluster"].get('ins_id') and uop_inst_id == self.req_dict["redis_cluster"]['ins_id']:
                instance['port'] = '6379'
                instance['dbtype'] = redis_master_slave.pop()
                self.req_dict["redis_cluster"]['instance'].append(instance)
                redis_ips.append(info["ip"])
                if not self.req_dict["redis_cluster"].get('vip'):
                    _, vip = create_vip_port(uop_inst_id)
                    self.req_dict["redis_cluster"]['vip'] = vip
            if self.req_dict["mongodb_cluster"].get('ins_id') and uop_inst_id == self.req_dict["mongodb_cluster"]['ins_id']:
                instance['port'] = '27017'
                self.req_dict["mongodb_cluster"]['instance'].append(instance)
                mongo_ips.append(info['ip'])
        # 部署redis集群
        if len(redis_ips) >1:
            if query_vm_status(redis_ips):
                flag = create_redis_cluster(redis_ips[0], redis_ips[1], self.req_dict["redis_cluster"]['vip'])
                if not flag:
                    create_redis_cluster(redis_ips[0], redis_ips[1], self.req_dict["redis_cluster"]['vip'])
        # 部署mysql mha的集群
        if mysql_cluster:
            mysql_cluster_ip_info = mysql_cluster_ip_info + mysql_cluster_ip_lvs
            mysql_cluster_ip_info.extend(zip(['vip1', 'vip2'], self.req_dict["mysql_cluster"]['vip']))
            create_mysql_cluster(mysql_cluster_ip_info)
        request_res_callback(self.task_id, RES_STATUS_OK, self.req_dict, self.compute_list)
        Log.logger.debug("Query Task ID " + self.task_id.__str__() + " Call UOP CallBack Post Success Info.")
        # 部署mongo集群
        if len(mongo_ips) > 1:
            Log.logger.debug("Start deploy the mongo master.%s" % mongo_ips)
            ins = MongodbCluster(mongo_ips[0], mongo_ips[1], mongo_ips[2], mongo_ips[2])
            ins.exec_final_script()
            Log.logger.debug("Deploy the mongo master Done.")
        # 停止定时任务并退出
        self.stop()

    def do_fail(self):
        # 执行失败调用UOP CallBack，提交失败
        request_res_callback(self.task_id, RES_STATUS_FAIL, self.req_dict, self.compute_list)
        Log.logger.debug("Query Task ID " + self.task_id.__str__() + " Call UOP CallBack Post Fail Info.")
        # 停止定时任务并退出
        self.stop()

    def do_rollback(self):
        _rollback_all(self.task_id, self.resource_id, self.uop_os_inst_id_list, self.result_inst_id_list, self.req_dict['domain'])
        self.fail()

    def do_stop(self):
        # 停止定时任务退出任务线程
        Log.logger.debug("Query Task ID " + self.task_id.__str__() + " Stop.")
        # 停止定时任务并退出
        TaskManager.task_exit(self.task_id)

    def do_create_instance(self):
        self.is_rollback, self.uop_os_inst_id_list = _create_resource_set(self.task_id, self.resource_id,
                                                                          self.resource_list, self.compute_list)
        if self.is_rollback:
            self.rollback()
        else:
            self.query()

    def do_query_resource_set_status(self):
        is_finished, self.is_rollback = _query_resource_set_status(self.task_id, self.uop_os_inst_id_list,
                                                                   self.result_inst_id_list, self.result_info_list,
                                                                   self.compute_list)
        if is_finished:
            # l = self.compute_list['container']
            for compute in self.compute_list:
                real_ip = ''
                domain = compute.get('domain')
                instance = compute.get('instance')
                for ip in instance:
                    ip_str = str(ip.get('ip')) + ' '
                    real_ip += ip_str
                ports = str(compute.get('port'))
                nip = '172.28.20.98'
                # port = '8081 9999 1010'  # TODO 前端传值
                print 'domain&ip:', domain, real_ip
                Log.logger.debug('the receive domain and ip port is %s-%s-%s' % (domain, real_ip, ports))
                self.do_push_nginx_config({'nip': nip, 'domain': domain, 'ip': real_ip.strip(), 'port': ports.strip()})
                # self.do_push_nginx_config({'nip': nip, 'domain': 'tttttt', 'ip': 'nnnnnnnn'})
                #####
                dns_env = {'develop': '172.28.5.21', 'test': '172.28.18.212'}
                ip = dns_env[self.req_dict['env']]
                # domain = self.req_dict['domain']
                domain = compute.get('domain')
                dns_server = DnsConfig.singleton()
                dns_server.add(domain_name=domain, ip=ip)
                dns_server.reload()
                #####
            self.success()
        if self.is_rollback:
            self.rollback()

    def do_push_nginx_config(self, kwargs):
        """
        need the nip domain ip
        nip:这是nginx那台机器的ip
        need write the update file into vm
        :param kwargs:
        :return:
        """
        nip = kwargs.get('nip')
        with open('/etc/ansible/hosts', 'w') as f:
            f.write('%s\n' % nip)
        Log.logger.debug('----->start push', kwargs)
        run_cmd("ansible {nip} --private-key=/root/.ssh/id_rsa_98 -a 'yum install rsync -y'".format(nip=nip))
        run_cmd("ansible {nip} --private-key=/root/.ssh/id_rsa_98 -m synchronize -a 'src=/opt/uop-crp/crp/res_set/update.py dest=/shell/'".format(nip=nip))
        run_cmd("ansible {nip} --private-key=/root/.ssh/id_rsa_98 -m synchronize -a 'src=/opt/uop-crp/crp/res_set/template dest=/shell/'".format(nip=nip))
        Log.logger.debug('------>上传配置文件完成')
        run_cmd("ansible {nip} --private-key=/root/.ssh/id_rsa_98 -m shell -a 'chmod 777 /shell/update.py'".format(nip=nip))
        run_cmd("ansible {nip} --private-key=/root/.ssh/id_rsa_98 -m shell -a 'chmod 777 /shell/template'".format(nip=nip))
        run_cmd('ansible {nip} --private-key=/root/.ssh/id_rsa_98 -m shell -a '
                '"/shell/update.py {domain} {ip} {port}"'.format(nip=kwargs.get('nip'), domain=kwargs.get('domain'), ip=kwargs.get('ip'), port=kwargs.get('port')))
        Log.logger.debug('------>end push')


def run_cmd(cmd):
    msg = ''
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
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


# 向OpenStack申请资源
def _create_instance(task_id, name, image, flavor, availability_zone, network_id):
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
    Log.logger.debug("Task ID " + task_id.__str__() + " create instance:")
    Log.logger.debug(int)
    Log.logger.debug(int.id)

    return int.id


# 依据资源类型创建资源
def create_instance_by_type(task_id, ins_type, name):
    image = images_dict.get(ins_type)
    image_uuid = image.get('uuid')
    Log.logger.debug("Task ID " + task_id.__str__() +
                     " Select Image UUID: " + image_uuid + " by Instance Type " + ins_type)
    return _create_instance(task_id, name, image_uuid, FLAVOR_1C2G, AVAILABILITY_ZONE_AZ_UOP, DEV_NETWORK_ID)


# 依据镜像URL创建NovaDocker容器
def create_docker_by_url(task_id, name, image_url):
    err_msg, image_uuid = image_transit(image_url)
    if err_msg is None:
        Log.logger.debug("Task ID " + task_id.__str__() +
                         " Transit harbor docker image success. The result glance image UUID is " + image_uuid)
        return None, _create_instance(task_id, name, image_uuid, DOCKER_FLAVOR_2C4G, AVAILABILITY_ZONE_AZ_UOP,
                                      DEV_NETWORK_ID)
    else:
        return err_msg, None


def create_vip_port(instance_name):
    neutron_client = OpenStack.neutron_client
    network_id = DEV_NETWORK_ID

    body_value = {
                     "port": {
                             "admin_state_up": True,
                             "name": instance_name + '_port',
                             "network_id": network_id
                      }
                 }
    Log.logger.debug('Create port for cluster/instance ' + instance_name)
    response = neutron_client.create_port(body=body_value)
    ip = response.get('port').get('fixed_ips').pop().get('ip_address')
    Log.logger.debug('Port id: ' + response.get('port').get('id') +
                     'Port ip: ' + ip)
    return None, ip


# 申请资源定时任务
def _create_resource_set(task_id, resource_id=None, resource_list=None, compute_list=None):
    is_rollback = False
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
        global quantity
        for i in range(1, quantity+1, 1):
            # 为mysql创建2个mycat镜像的LVS
            if instance_type == 'mysql' and i == 4:
                instance_type = 'mycat'
            instance_name2 = instance_name + '_' + str(i)
            osint_id = create_instance_by_type(task_id, instance_type, instance_name2)
            uopinst_info = {
                               'uop_inst_id': instance_id,
                               'os_inst_id': osint_id,
                                'uop_inst_name': instance_name2,
                           }
            uop_os_inst_id_list.append(uopinst_info)

    for compute in compute_list:
        instance_name = compute.get('instance_name')
        instance_id = compute.get('instance_id')
        cpu = compute.get('cpu')
        mem = compute.get('mem')
        image_url = compute.get('image_url')
        quantity = compute.get('quantity')
        domain = compute.get('domain')

        compute['instance'] = []


        # er_msg, ip = create_vip_port(instance_name)

        for i in range(0, quantity, 1):
            err_msg, osint_id = create_docker_by_url(task_id, instance_name, image_url)
            if err_msg is None:
                uopinst_info = {
                       'uop_inst_id': instance_id,
                       'os_inst_id': osint_id
                   }
                uop_os_inst_id_list.append(uopinst_info)
                compute['instance'].append({'domain': domain, 'os_inst_id': osint_id})
            else:
                Log.logger.error("Task ID " + task_id.__str__() + " ERROR. Error Message is:")
                Log.logger.error(err_msg)
                # 删除全部
                is_rollback = True
                uop_os_inst_id_list = []

    return is_rollback, uop_os_inst_id_list


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
def _rollback_all(task_id, resource_id, uop_os_inst_id_list, result_uop_os_inst_id_list, domain):
    nova_client = OpenStack.nova_client
    # fail_list = list(set(uop_os_inst_id_list) - set(result_uop_os_inst_id_list))
    fail_list = _uop_os_list_sub(uop_os_inst_id_list, result_uop_os_inst_id_list)
    Log.logger.debug("Task ID " + task_id.__str__() +
                     " Resource ID " + resource_id.__str__() + " have one or more instance create failed." +
                     " Successful instance id set is " + result_uop_os_inst_id_list[:].__str__() +
                     " Failed instance id set is " + fail_list[:].__str__())
    # 删除全部，完成rollback
    for uop_os_inst_id in uop_os_inst_id_list:
        nova_client.servers.delete(uop_os_inst_id['os_inst_id'])
    Log.logger.debug("Task ID " + task_id.__str__() + " Resource ID " + resource_id.__str__() + " rollback done.")
    ####
    dns_server = DnsConfig.singleton()
    dns_server.delete(domain_name=domain)
    dns_server.reload()

# _uop_os_list_sub
def _uop_os_list_sub(uop_os_inst_id_list, result_uop_os_inst_id_list):
    uop_os_inst_id_wait_query = copy.deepcopy(uop_os_inst_id_list)
    for i in result_uop_os_inst_id_list:
        for j in uop_os_inst_id_wait_query:
            if j['os_inst_id'] == i['os_inst_id']:
                uop_os_inst_id_wait_query.remove(j)
    return uop_os_inst_id_wait_query


# 向OpenStack查询已申请资源的定时任务
def _query_resource_set_status(task_id=None, uop_os_inst_id_list=None, result_inst_id_list=None,
                               result_info_list=None, container_list=None):
    is_finish = False
    is_rollback = False
    # uop_os_inst_id_wait_query = list(set(uop_os_inst_id_list) - set(result_inst_id_list))
    uop_os_inst_id_wait_query = _uop_os_list_sub(uop_os_inst_id_list, result_inst_id_list)

    Log.logger.debug("Query Task ID " + task_id.__str__() + ", remain " + uop_os_inst_id_wait_query[:].__str__())
    Log.logger.debug("Query Task ID " + task_id.__str__() +
                     " Test Task Scheduler Class result_inst_id_list object id is " +
                     id(result_inst_id_list).__str__() +
                     ", Content is " + result_inst_id_list[:].__str__())
    nova_client = OpenStack.nova_client
    for uop_os_inst_id in uop_os_inst_id_wait_query:
        inst = nova_client.servers.get(uop_os_inst_id['os_inst_id'])
        Log.logger.debug("Query Task ID " + task_id.__str__() + " query Instance ID " +
                         uop_os_inst_id['os_inst_id'] + " Status is " + inst.status)
        if inst.status == 'ACTIVE':
            _ips = _get_ip_from_instance(inst)
            _ip = _ips.pop() if _ips.__len__() >= 1 else ''
            physical_server = getattr(inst, OS_EXT_PHYSICAL_SERVER_ATTR)
            _data = {
                        'uop_inst_id': uop_os_inst_id['uop_inst_id'],
                        'os_inst_id': uop_os_inst_id['os_inst_id'],
                        'uop_inst_name': uop_os_inst_id.get('uop_inst_name'),
                        'ip': _ip,
                        'physical_server': physical_server,
                    }
            for container in container_list:
                for instance in container.get('instance'):
                    if instance.get('os_inst_id') == uop_os_inst_id['os_inst_id']:
                        instance['ip'] = _ip
                        instance['physical_server'] = physical_server
            result_info_list.append(_data)
            _data = {}
            Log.logger.debug("Query Task ID " + task_id.__str__() + " Instance Info: " + _data.__str__())
            result_inst_id_list.append(uop_os_inst_id)
        if inst.status == 'ERROR':
            # 置回滚标志位
            Log.logger.debug("Query Task ID " + task_id.__str__() + " ERROR Instance Info: " + inst.to_dict().__str__())
            is_rollback = True

    if result_inst_id_list.__len__() == uop_os_inst_id_list.__len__():
        is_finish = True

    # 回滚全部资源和容器
    return is_finish, is_rollback


# request UOP res_callback
def request_res_callback(task_id, status, req_dict, container_list):
    # project_id, resource_name,under_name, resource_id, domain,
    # container_name, image_addr, stardand_ins,cpu, memory, ins_id,
    # mysql_username, mysql_password, mysql_port, mysql_ip,
    # redis_username, redis_password, redis_port, redis_ip,
    # mongodb_username, mongodb_password, mongodb_port, mongodb_ip
    """
    :param task_id: 任务ID
    :param status: 状态
    :param req_dict: req字段字典
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
    "status": "成功",
    "container": {
        "username": "root",
        "password": "123456",
        "ip": "容器IP",
        "container_name": "容器名称",
        "image_addr": "镜像地址",
        "cpu": "2",
        "memory": "4",
        "ins_id": "实例id",
        "physical_server": "所在物理机"
    },
    "db_info": {
        "mysql": {
            "ins_id": "mysql_inst_id",
            "username": "数据库名",
            "password": "密码",
            "port": "端口",
            "ip": "MySQLIP",
            "physical_server": "所在物理机"
        },
        "redis": {
            "ins_id": "redis_inst_id",
            "username": "数据库名",
            "password": "密码",
            "port": "端口",
            "ip": "RedisIP",
            "physical_server": "所在物理机"
        },
        "mongodb": {
            "ins_id": "mongodb_inst_id",
            "username": "数据库名",
            "password": "密码",
            "port": "端口",
            "ip": "MongodbIP",
            "physical_server": "所在物理机"
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
    data["cmdb_repo_id"] = req_dict["cmdb_repo_id"]
    data["status"] = status

    data["container"] = container_list

    db_info = {}
    db_info["mysql"] = req_dict['mysql_cluster']
    db_info["redis"] = req_dict['redis_cluster']
    db_info["mongodb"] = req_dict['mongodb_cluster']

    data["db_info"] = db_info

    data_str = json.dumps(data)
    Log.logger.debug('xxxxx')
    Log.logger.debug("Task ID " + task_id.__str__() + " UOP res_callback Request Body is: " + data_str)
    res = requests.post(RES_CALLBACK, data=data_str)
    Log.logger.debug(res.status_code)
    Log.logger.debug(res.content)
    ret = eval(res.content.decode('unicode_escape'))
    return ret


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
            parser.add_argument('cmdb_repo_id', type=str)
            parser.add_argument('resource_list', type=list, location='json')
            parser.add_argument('compute_list', type=list, location='json')
            args = parser.parse_args()

            req_dict = {}
            req_list = []
            com_dict = dict()

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
            req_dict["mysql_cluster"] = {}
            req_dict["redis_cluster"] = {}
            req_dict["mongodb_cluster"] = {}
            for resource in resource_list:
                instance_id = resource.get('instance_id')
                instance_type = resource.get('instance_type')
                if instance_type == 'mysql':
                    req_dict["mysql_cluster"]['username'] = DEFAULT_USERNAME
                    req_dict["mysql_cluster"]['password'] = DEFAULT_PASSWORD
                    req_dict["mysql_cluster"]['port'] = '3316'
                    req_dict["mysql_cluster"]['ins_id'] = instance_id
                    req_dict["mysql_cluster"]['instance'] = []
                if instance_type == 'redis':
                    req_dict["redis_cluster"]['username'] = DEFAULT_USERNAME
                    req_dict["redis_cluster"]['password'] = DEFAULT_PASSWORD
                    req_dict["redis_cluster"]['port'] = '6379'
                    req_dict["redis_cluster"]['ins_id'] = instance_id
                    req_dict["redis_cluster"]['instance'] = []
                if instance_type == 'mongo':
                    req_dict["mongodb_cluster"]['username'] = DEFAULT_USERNAME
                    req_dict["mongodb_cluster"]['password'] = DEFAULT_PASSWORD
                    req_dict["mongodb_cluster"]['port'] = '27017'
                    req_dict["mongodb_cluster"]['ins_id'] = instance_id
                    req_dict["mongodb_cluster"]['instance'] = []
                # req_list.append(req_dict)
                # req_dict = {}

            for compute in compute_list:
                instance_name = compute.get('instance_name', None)
                instance_id = compute.get('instance_id', None)
                cpu = compute.get('cpu', None)
                mem = compute.get('mem', None)
                image_url = compute.get('image_url', None)
                domain = compute.get('domain', None)
                quantity = compute.get('quantity', None)

                for i in range(quantity):
                    com_dict["container_name"] = instance_name + str(i)
                    com_dict["image_addr"] = image_url
                    com_dict["cpu"] = cpu
                    com_dict["memory"] = mem
                    com_dict["container_inst_id"] = instance_id + '_' + str(i)
                    com_dict["domain"] = domain
                    # com_dict['instances'] = []
                    req_list.append(com_dict)
                    com_dict = {}

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

            # init app cluster Map(List[])
            req_dict['app_cluster_list'] = req_list

            # init default data
            req_dict["container_username"] = DEFAULT_USERNAME
            req_dict["container_password"] = DEFAULT_PASSWORD
            req_dict["container_ip"] = IP_NONE
            req_dict["container_physical_server"] = PHYSICAL_SERVER_NONE

            result_list = []
            Log.logger.debug('req_dict\'s object id is :')
            Log.logger.debug(id(req_dict))
            Log.logger.debug('result_list\'s object id is :')
            Log.logger.debug(id(result_list))
            # 创建资源集合定时任务，成功或失败后调用UOP资源预留CallBack（目前仅允许全部成功或全部失败，不允许部分成功）
            res_provider = ResourceProvider(resource_id, resource_list, compute_list, req_dict)
            res_provider_list = [res_provider]
            TaskManager.task_start(SLEEP_TIME, TIMEOUT, res_provider_list, tick_announce)
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


def tick_announce(task_id, res_provider_list):
    if res_provider_list is not None and len(res_provider_list) >= 1:
        res_provider = res_provider_list[0]
        if res_provider.task_id is None:
            res_provider.set_task_id(task_id)
        Log.logger.debug(res_provider.state)
        if res_provider.state == 'init':
            res_provider.create()
        else:
            res_provider.query()


class MongodbCluster(object):
    """
    ip_slave1 = '172.28.36.143'
    ip_slave2 = '172.28.36.142'
    ip_master1 = '172.28.36.141'
    ip_master2 = '172.28.36.141'


    cmd1 = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/mongoclu_install/mongoslave1.sh sys95"'.format(vip=ip_slave1)
    cmd2 = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/mongoclu_install/mongoslave2.sh sys95"'.format(vip=ip_slave2)
    cmd3 = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/mongoclu_install/mongomaster1.sh"'.format(vip=ip_master1)
    cmd4 = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/mongoclu_install/mongomaster2.sh sys95"'.format(vip=ip_master2)

    """

    def __init__(self, ip_slave1, ip_slave2, ip_master1, ip_master2):
        """
        172.28.36.230
        172.28.36.23
        172.28.36.231
        :param cmd_list:
        """
        self.ip_slave1 = ip_slave1
        self.ip_slave2 = ip_slave2
        self.ip_master1 = ip_master1
        self.ip_master2 = ip_master2
        self.d = {
            self.ip_slave1: 'mongoslave1.sh',
            self.ip_slave2: 'mongoslave2.sh',
            self.ip_master1: 'mongomaster1.sh',
            }
        self.cmd = ['ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/'
                    'mongoclu_install/mongomaster2.sh sys95"'.format(vip=ip_master2)]
        self.ip = [ip_slave1, ip_slave2, ip_master1]
        self.new_host = '[new_host]'
        self.write_ip_to_server()
        self.flag = False
        self.telnet_ack()

    def write_ip_to_server(self):
        for ip in self.ip:
            with open('/etc/ansible/hosts', 'a') as f:
                f.write('%s\n' % ip)

    def telnet_ack(self):
        while not self.flag:
            for ip in self.ip:
                p = subprocess.Popen('nmap %s -p 22' % ip, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                try:
                    a = p.stdout.readlines()[5]
                    Log.logger.debug('nmap ack result:%s' % a)
                except IndexError as e:
                    print e
                    a = 'false'
                    Log.logger.debug('%s' % e)
                    break
                if 'open' in a:
                    self.mongodb_cluster_push(ip)
                    self.ip.remove(ip)
            if len(self.ip) == 0:
                self.flag = True

    def mongodb_cluster_push(self, ip):
        # vip_list = list(set(self.ip))
        # vip_list = [ip_master1, ip_slave1, ip_slave2]
        cmd_before = "ansible {vip} --private-key=/home/mongo/old_id_rsa -m synchronize -a 'src=/opt/uop-crp/crp/res_set/write_mongo_ip.py dest=/tmp/'".format(vip=ip)
        authority_cmd = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m shell -a "chmod 777 /tmp/write_mongo_ip.py"'.format(vip=ip)
        cmd1 = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m shell -a "python /tmp/write_mongo_ip.py {m_ip} {s1_ip} {s2_ip}"'.\
            format(vip=ip, m_ip=self.ip_master1, s1_ip=self.ip_slave1, s2_ip=self.ip_slave2)
        Log.logger.debug('开始上传脚本%s' % ip)
        p = subprocess.Popen(cmd_before, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line
            Log.logger.debug('mongodb cluster cmd before:%s' % line)
        Log.logger.debug('开始修改权限%s' % ip)
        p = subprocess.Popen(authority_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line
            Log.logger.debug('mongodb cluster authority:%s' % line)
        Log.logger.debug('脚本上传完成,开始执行脚本%s' % ip)
        p = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line
            Log.logger.debug('mongodb cluster exec write script:%s' % line)
        Log.logger.debug('脚本执行完毕 接下来会部署%s' % ip)
        # for ip in self.ip:
        with open('/home/mongo/hosts', 'w') as f:
            f.write('%s\n' % ip)
        print '-----', ip,type(ip)
        script = self.d.get(ip)
        if str(ip) != '172.28.36.105':
            cmd_s = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/mongoclu_install/{s} sys95"'.\
                format(vip=ip, s=script)
        else:
            cmd_s = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/mongoclu_install/{s}"'.\
                format(vip=ip, s=script)
        p = subprocess.Popen(cmd_s, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line,
            Log.logger.debug('mongodb cluster push result:%s, -----%s' % (line, ip))

    def exec_final_script(self):
        for i in self.cmd:
            p = subprocess.Popen(i, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                print line,
                Log.logger.debug('mongodb cluster push result:%s' % line)


CMDPATH = r'crp/res_set/playbook-0830/'
def create_redis_cluster(ip1, ip2, vip):
    cmd = 'python {0}script/redis_cluster.py {1} {2} {3}'.format(CMDPATH, ip1, ip2, vip)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    strout = ''
    for line in p.stdout.readlines():
        strout += line + os.linesep

    Log.logger.debug('redis cluster push result:%s' % strout)
    if 'FAILED!' in strout or 'UNREACHABLE!' in strout:
        return False
    else:
        return True



def create_mysql_cluster(ip_info):
    with open(os.path.join(CMDPATH, 'mysqlmha', 'mysql.txt'), 'wb') as f:
        for host_name, ip in ip_info:
            f.write(host_name + os.linesep)
            f.write(ip + os.linesep)

    path = CMDPATH + 'mysqlmha'
    cmd = '/bin/sh {0}/mlm.sh {0}'.format(path)
    strout = ''
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        strout += line + os.linesep
    Log.logger.debug('mysql cluster push result:%s' % strout)

def query_vm_status(ips):
    flag = False
    for ip in ips:
        p = subprocess.Popen('nmap %s -p 22' % ip, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            a = p.stdout.readlines()[5]
            Log.logger.debug('nmap ack result:%s' % a)
        except IndexError as e:
            print e
            a = 'false'
            Log.logger.debug('%s' % e)
            break
        if 'open' in a:
            ips.remove(ip)
    if len(ips) == 0:
        flag = True
    return flag


resource_set_api.add_resource(ResourceSet, '/sets')

if __name__ == "__main__":
    a = MongodbCluster()
