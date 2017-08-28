# -*- coding: utf-8 -*-
import os
import json
import time
import subprocess
import requests
from transitions import Machine
from flask_restful import reqparse, Api, Resource
from flask import request
from crp.taskmgr import *
from mysql_volume import create_volume
from crp.dns.dns_api import DnsApi,NamedManagerApi
from crp.res_set import resource_set_blueprint
from crp.res_set.errors import resource_set_errors
from crp.log import Log
from crp.openstack import OpenStack
from crp.utils.docker_tools import image_transit
from config import configs, APP_ENV

# TODO: refactor it later.
# nginx_ip = configs[APP_ENV].nginx_ip
# nginx_ip_slave = configs[APP_ENV].nginx_ip_slave
MONGODB_SCRIPT_PATH = configs[APP_ENV].MONGODB_SCRIPT_PATH

resource_set_api = Api(resource_set_blueprint, errors=resource_set_errors)

TIMEOUT = 500
SLEEP_TIME = 3
cluster_type_image_port_mappers = configs[APP_ENV].cluster_type_image_port_mappers
FLAVOR_1C2G = configs[APP_ENV].FLAVOR_1C2G
DOCKER_FLAVOR_2C4G = configs[APP_ENV].DOCKER_FLAVOR_2C4G
AVAILABILITY_ZONE_AZ_UOP = configs[APP_ENV].AVAILABILITY_ZONE_AZ_UOP
DEV_NETWORK_ID = configs[APP_ENV].DEV_NETWORK_ID
OS_EXT_PHYSICAL_SERVER_ATTR = configs[APP_ENV].OS_EXT_PHYSICAL_SERVER_ATTR
RES_CALLBACK = configs[APP_ENV].RES_CALLBACK
RES_STATUS_OK = configs[APP_ENV].RES_STATUS_OK
RES_STATUS_FAIL = configs[APP_ENV].RES_STATUS_FAIL
RES_STATUS_DEFAULT = configs[APP_ENV].RES_STATUS_DEFAULT
DEFAULT_USERNAME = configs[APP_ENV].DEFAULT_USERNAME
DEFAULT_PASSWORD = configs[APP_ENV].DEFAULT_PASSWORD
items_sequence_list_config = configs[APP_ENV].items_sequence_list_config
property_json_mapper_config = configs[APP_ENV].property_json_mapper_config
SCRIPTPATH = configs[APP_ENV].SCRIPTPATH
DNS_ENV = configs[APP_ENV].DNS_ENV

# Transition state Log debug decorator


def transition_state_logger(func):
    def wrapper(self, *args, **kwargs):
        Log.logger.debug("Transition state is turned in " + self.state)
        ret = func(self, *args, **kwargs)
        Log.logger.debug("Transition state is turned out " + self.state)
        return ret
    return wrapper


class ResourceProviderTransitions(object):
    # Define some states.
    states = [
        'init',
        'success',
        'fail',
        'rollback',
        'stop',
        'app_cluster',
        'resource_cluster',
        'query',
        'status',
        'app_push',
        'mysql_push',
        'mongodb_push',
        'redis_push',
        'dns_push']

    # Define transitions.
    transitions = [
        {'trigger': 'success', 'source': ['status', 'app_push', 'mysql_push', 'mongodb_push', 'redis_push', 'dns_push'], 'dest': 'success', 'after': 'do_success'},
        {'trigger': 'fail', 'source': 'rollback', 'dest': 'fail', 'after': 'do_fail'},
        {'trigger': 'rollback', 'source': '*', 'dest': 'rollback', 'after': 'do_rollback'},
        {'trigger': 'stop', 'source': ['success', 'fail'], 'dest': 'stop', 'after': 'do_stop'},
        {'trigger': 'app_cluster', 'source': ['init', 'app_cluster', 'resource_cluster'], 'dest': 'app_cluster', 'after': 'do_app_cluster'},
        {'trigger': 'resource_cluster', 'source': ['init', 'app_cluster', 'resource_cluster'], 'dest': 'resource_cluster', 'after': 'do_resource_cluster'},
        {'trigger': 'query', 'source': ['app_cluster', 'resource_cluster', 'query'], 'dest': 'query', 'after': 'do_query'},
        {'trigger': 'status', 'source': ['query', 'status'], 'dest': 'status', 'after': 'do_status'},
        {'trigger': 'app_push', 'source': ['status', 'app_push', 'dns_push', 'mysql_push', 'mongodb_push', 'redis_push'], 'dest': 'app_push', 'after': 'do_app_push'},
        {'trigger': 'dns_push', 'source': ['status', 'app_push', 'dns_push', 'mysql_push', 'mongodb_push', 'redis_push'], 'dest': 'dns_push', 'after': 'do_dns_push'},
        {'trigger': 'mysql_push', 'source': ['status', 'app_push', 'dns_push', 'mysql_push', 'mongodb_push', 'redis_push'], 'dest': 'mysql_push', 'after': 'do_mysql_push'},
        {'trigger': 'mongodb_push', 'source': ['status', 'app_push', 'dns_push', 'mysql_push', 'mongodb_push', 'redis_push'], 'dest': 'mongodb_push', 'after': 'do_mongodb_push'},
        {'trigger': 'redis_push', 'source': ['status', 'app_push', 'dns_push', 'mysql_push', 'mongodb_push', 'redis_push'], 'dest': 'redis_push', 'after': 'do_redis_push'},
    ]

    def __init__(self, resource_id, property_mappers_list, req_dict):
        # Initialize the variable
        self.is_running = False
        self.is_need_rollback = False
        self.phase_list = [
            'create',
            'query',
            'status',
            'push',
            'callback',
            'stop']
        self.phase = 'create'
        self.task_id = None
        self.resource_id = resource_id
        self.result_inst_id_list = []
        self.uop_os_inst_id_list = []
        self.property_mappers_list = copy.deepcopy(property_mappers_list)
        self.property_mappers_list.reverse()
        self.push_mappers_list = []
        # 结果集
        self.result_mappers_list = []
        # 刚刚处理过的节点，可能为存在引用关系的父节点
        self.pre_property_mapper = {}
        # 待处理的节点
        self.property_mapper = {}
        self.req_dict = req_dict

        # Initialize the state machine
        self.machine = Machine(
            model=self,
            states=ResourceProviderTransitions.states,
            transitions=ResourceProviderTransitions.transitions,
            initial='init')

        self.dir = os.path.dirname(
            os.path.abspath(__file__))

    def set_task_id(self, task_id):
        self.task_id = task_id

    def next_phase(self):
        index = self.phase_list.index(self.phase)
        self.phase = self.phase_list[index + 1]
        if self.phase == 'query':
            self.query()
        elif self.phase == 'status':
            self.status()

    def preload_property_mapper(self, property_mappers_list):
        if len(property_mappers_list) != 0:
            if len(self.pre_property_mapper) == 0:
                self.pre_property_mapper = self.property_mapper
            if len(self.pre_property_mapper) != 0 and len(self.property_mapper) != 0 and (
                    self.pre_property_mapper.keys()[0] != self.property_mapper.keys()[0]):
                self.pre_property_mapper = self.property_mapper
            self.property_mapper = property_mappers_list.pop()
        else:
            self.pre_property_mapper = {}
            self.property_mapper = {}

    def tick_announce(self):
        if self.is_need_rollback:
            self.rollback()
        if self.phase == 'query' or self.phase == 'status' or self.phase == 'stop':
            return
        if self.phase == 'create':
            self.preload_property_mapper(self.property_mappers_list)
        elif self.phase == 'push':
            self.preload_property_mapper(self.push_mappers_list)

        if len(self.property_mapper) != 0:
            item_id = self.property_mapper.keys()[0]
            if self.phase == 'create':
                func = getattr(self, item_id, None)
            elif self.phase == 'push':
                func = getattr(self, ('%s_push' % item_id), None)
            if not func:
                raise NotImplementedError("Unexpected item_id=%s" % item_id)
            Log.logger.debug('Trigger is %s', item_id)
            func()
            if self.phase == 'push':
                # 从self.property_mapper中获得的cluster_info为引用类型，因此更新self.push_mapper_list中的dict则self.result_mapper_list同步更新
                pass
        else:
            if self.phase == 'stop':
                self.stop()
            elif self.phase == 'callback':
                if self.is_need_rollback is not True:
                    self.success()
            self.next_phase()

    @staticmethod
    def _get_ip_from_instance(server):
        ips_address = []
        for _, ips in server.addresses.items():
            for ip in ips:
                if isinstance(ip, dict):
                    if 'addr' in ip:
                        ip_address = ip['addr']
                        ips_address.append(ip_address)
        return ips_address

    # _uop_os_list_sub
    @staticmethod
    def _uop_os_list_sub(uop_os_inst_id_list, result_uop_os_inst_id_list):
        uop_os_inst_id_wait_query = copy.deepcopy(uop_os_inst_id_list)
        for i in result_uop_os_inst_id_list:
            for j in uop_os_inst_id_wait_query:
                if j['os_inst_id'] == i['os_inst_id']:
                    uop_os_inst_id_wait_query.remove(j)
        return uop_os_inst_id_wait_query

    # 回滚删除全部资源和容器
    def _rollback_all(
            self,
            resource_id,
            uop_os_inst_id_list,
            result_uop_os_inst_id_list):
        nova_client = OpenStack.nova_client
        # fail_list = list(set(uop_os_inst_id_list) - set(result_uop_os_inst_id_list))
        fail_list = self._uop_os_list_sub(
            uop_os_inst_id_list, result_uop_os_inst_id_list)
        Log.logger.debug(
            "Task ID " +
            self.task_id.__str__() +
            " Resource ID " +
            resource_id.__str__() +
            " have one or more instance create failed." +
            " Successful instance id set is " +
            result_uop_os_inst_id_list[:].__str__() +
            " Failed instance id set is " +
            fail_list[:].__str__())
        # 删除全部，完成rollback
        for uop_os_inst_id in uop_os_inst_id_list:
            nova_client.servers.delete(uop_os_inst_id['os_inst_id'])
        Log.logger.debug(
            "Task ID " +
            self.task_id.__str__() +
            " Resource ID " +
            resource_id.__str__() +
            " rollback done.")

    # 向OpenStack申请资源
    def _create_instance(
            self,
            name,
            image,
            flavor,
            availability_zone,
            network_id):
        nova_client = OpenStack.nova_client
        """
        ints = nova_client.servers.list()
        Log.logger.debug(ints)
        def create(self, name, image, flavor, meta=None, files=None,
                   reservation_id=None, min_count=None,
                   max_count=None, security_groups=None, userdata=None,
                   key_name=None, availability_zone=None,
                   block_device_mapping=None, block_device_mapping_v2=None,
                   nics=None, scheduler_hints=None,
                   config_drive=None, disk_config=None, **kwargs):
        """
        nics_list = []
        nic_info = {'net-id': network_id}
        nics_list.append(nic_info)
        int = nova_client.servers.create(name, image, flavor,
                                         availability_zone=availability_zone,
                                         nics=nics_list)
        Log.logger.debug(
            "Task ID " +
            self.task_id.__str__() +
            " create instance:")
        Log.logger.debug(int)
        Log.logger.debug(int.id)

        return int.id

    # 依据镜像URL创建NovaDocker容器
    def _create_docker_by_url(self, name, image_url):
        err_msg, image_uuid = image_transit(image_url)
        if err_msg is None:
            Log.logger.debug(
                "Task ID " +
                self.task_id.__str__() +
                " Transit harbor docker image success. The result glance image UUID is " +
                image_uuid)
            return None, self._create_instance(
                name, image_uuid, DOCKER_FLAVOR_2C4G, AVAILABILITY_ZONE_AZ_UOP, DEV_NETWORK_ID)
        else:
            return err_msg, None

    # 依据资源类型创建资源
    def _create_instance_by_type(self, ins_type, name):
        image = cluster_type_image_port_mappers.get(ins_type)
        image_uuid = image.get('uuid')
        Log.logger.debug(
            "Task ID " +
            self.task_id.__str__() +
            " Select Image UUID: " +
            image_uuid +
            " by Instance Type " +
            ins_type)
        return self._create_instance(
            name,
            image_uuid,
            FLAVOR_1C2G,
            AVAILABILITY_ZONE_AZ_UOP,
            DEV_NETWORK_ID)

    # 申请应用集群docker资源
    def _create_app_cluster(self, property_mapper):
        is_rollback = False
        uop_os_inst_id_list = []

        propertys = property_mapper.get('app_cluster')
        cluster_name = propertys.get('cluster_name')
        cluster_id = propertys.get('cluster_id')
        domain = propertys.get('domain')
        port = propertys.get('port')
        image_url = propertys.get('image_url')
        cpu = propertys.get('cpu')
        mem = propertys.get('mem')
        quantity = propertys.get('quantity')

        if quantity >= 1:
            propertys['ins_id'] = cluster_id
            cluster_type = 'app_cluster'
            propertys['cluster_type'] = cluster_type
            propertys['username'] = DEFAULT_USERNAME
            propertys['password'] = DEFAULT_PASSWORD
            propertys['port'] = port
            propertys['instance'] = []

            for i in range(0, quantity, 1):
                instance_name = '%s_%s' % (cluster_name, i.__str__())
                err_msg, osint_id = self._create_docker_by_url(
                    instance_name, image_url)
                if err_msg is None:
                    uopinst_info = {
                        'uop_inst_id': cluster_id,
                        'os_inst_id': osint_id
                    }
                    uop_os_inst_id_list.append(uopinst_info)
                    propertys['instance'].append(
                        {
                            'instance_type': cluster_type,
                            'instance_name': instance_name,
                            'username': DEFAULT_USERNAME,
                            'password': DEFAULT_PASSWORD,
                            'domain': domain,
                            'port': port,
                            'os_inst_id': osint_id})
                else:
                    Log.logger.error(
                        "Task ID " +
                        self.task_id.__str__() +
                        " ERROR. Error Message is:")
                    Log.logger.error(err_msg)
                    # 删除全部
                    is_rollback = True
                    uop_os_inst_id_list = []

        return is_rollback, uop_os_inst_id_list

    # 申请资源集群kvm资源
    def _create_resource_cluster(self, property_mapper):
        is_rollback = False
        uop_os_inst_id_list = []

        propertys = property_mapper.get('resource_cluster')
        cluster_name = propertys.get('cluster_name')
        cluster_id = propertys.get('cluster_id')
        cluster_type = propertys.get('cluster_type')
        version = propertys.get('version')
        cpu = propertys.get('cpu')
        mem = propertys.get('mem')
        disk = propertys.get('disk')
        quantity = propertys.get('quantity')

        if quantity >= 1:
            cluster_type_image_port_mapper = cluster_type_image_port_mappers.get(
                cluster_type)
            if cluster_type_image_port_mapper is not None:
                port = cluster_type_image_port_mapper.get('port')
            propertys['ins_id'] = cluster_id
            propertys['cluster_type'] = cluster_type
            propertys['username'] = DEFAULT_USERNAME
            propertys['password'] = DEFAULT_PASSWORD
            propertys['port'] = port
            propertys['instance'] = []

            for i in range(0, quantity, 1):
                # 为mysql创建2个mycat镜像的LVS
                if cluster_type == 'mysql' and i == 3:
                    cluster_type = 'mycat'
                instance_name = '%s_%s' % (cluster_name, i.__str__())
                osint_id = self._create_instance_by_type(
                    cluster_type, instance_name)
                uopinst_info = {
                    'uop_inst_id': cluster_id,
                    'os_inst_id': osint_id
                }
                uop_os_inst_id_list.append(uopinst_info)
                propertys['instance'].append({'instance_type': cluster_type,
                                              'instance_name': instance_name,
                                              'username': DEFAULT_USERNAME,
                                              'password': DEFAULT_PASSWORD,
                                              'port': port,
                                              'os_inst_id': osint_id})

                if cluster_type == 'mysql':
                    pass
                    # TODO mysql volume
                    # vm = {
                    #     'vm_name': instance_name,
                    #     'os_inst_id': osint_id,
                    # }
                    # create_volume(vm)

        return is_rollback, uop_os_inst_id_list

    # 将第一阶段输出结果新增至第四阶段
    def _add_to_phase4(self, uop_os_inst_id_list):
        self.uop_os_inst_id_list.extend(uop_os_inst_id_list)
        temp_push_property_mapper = {}
        temp_result_property_mapper = {}
        key = self.property_mapper.keys()[0]
        if key == 'resource_cluster':
            cluster_type = self.property_mapper.get(
                'resource_cluster').get('cluster_type')
            cluster_type_key = '%s' % cluster_type
            cluster_info = self.property_mapper.get('resource_cluster')
            quantity = cluster_info.get('quantity')
            if quantity is not None:
                temp_result_property_mapper[cluster_type_key] = cluster_info
                if quantity > 0:
                    temp_push_property_mapper[cluster_type_key] = cluster_info
        else:
            cluster_info = self.property_mapper.get('app_cluster')
            quantity = cluster_info.get('quantity')
            if quantity is not None:
                temp_result_property_mapper['app'] = cluster_info
                if quantity > 0:
                    temp_push_property_mapper['app'] = cluster_info
        if len(temp_push_property_mapper) > 0:
            self.push_mappers_list.insert(0, temp_push_property_mapper)
        if len(temp_result_property_mapper) > 0:
            self.result_mappers_list.insert(0, temp_result_property_mapper)

    # 向OpenStack查询已申请资源的定时任务
    def _query_resource_set_status(
            self,
            uop_os_inst_id_list=None,
            result_inst_id_list=None,
            result_mappers_list=None):
        is_finish = False
        is_rollback = False
        # uop_os_inst_id_wait_query = list(set(uop_os_inst_id_list) - set(result_inst_id_list))
        uop_os_inst_id_wait_query = self._uop_os_list_sub(
            uop_os_inst_id_list, result_inst_id_list)

        Log.logger.debug(
            "Query Task ID " +
            self.task_id.__str__() +
            ", remain " +
            uop_os_inst_id_wait_query[:].__str__())
        Log.logger.debug(
            "Query Task ID " +
            self.task_id.__str__() +
            " Test Task Scheduler Class result_inst_id_list object id is " +
            id(result_inst_id_list).__str__() +
            ", Content is " +
            result_inst_id_list[:].__str__())
        nova_client = OpenStack.nova_client
        for uop_os_inst_id in uop_os_inst_id_wait_query:
            inst = nova_client.servers.get(uop_os_inst_id['os_inst_id'])
            Log.logger.debug(
                "Query Task ID " +
                self.task_id.__str__() +
                " query Instance ID " +
                uop_os_inst_id['os_inst_id'] +
                " Status is " +
                inst.status)
            if inst.status == 'ACTIVE':
                _ips = self._get_ip_from_instance(inst)
                _ip = _ips.pop() if _ips.__len__() >= 1 else ''
                physical_server = getattr(inst, OS_EXT_PHYSICAL_SERVER_ATTR)
                for mapper in result_mappers_list:
                    value = mapper.values()[0]
                    instances = value.get('instance')
                    if instances is not None:
                        for instance in value.get('instance'):
                            if instance.get(
                                    'os_inst_id') == uop_os_inst_id['os_inst_id']:
                                instance['ip'] = _ip
                                instance['physical_server'] = physical_server
                                Log.logger.debug(
                                    "Query Task ID " +
                                    self.task_id.__str__() +
                                    " Instance Info: " +
                                    mapper.__str__())
                result_inst_id_list.append(uop_os_inst_id)
            if inst.status == 'ERROR':
                # 置回滚标志位
                Log.logger.debug(
                    "Query Task ID " +
                    self.task_id.__str__() +
                    " ERROR Instance Info: " +
                    inst.to_dict().__str__())
                is_rollback = True

        if result_inst_id_list.__len__() == uop_os_inst_id_list.__len__():
            is_finish = True

        # 回滚全部资源和容器
        return is_finish, is_rollback

    def start(self):
        if self.is_running is not True:
            self.is_running = True
            self.run()

    def run(self):
        while self.phase != 'query' and self.phase != 'status' and self.phase != 'stop':
            self.tick_announce()
        self.is_running = False

    @transition_state_logger
    def do_init(self):
        # 状态机初始状态
        pass

    @transition_state_logger
    def do_success(self):
        # 执行成功调用UOP CallBack，提交成功
        Log.logger.debug(
            "Query Task ID " +
            self.task_id.__str__() +
            " all instance create success." +
            " instance id set is " +
            self.result_inst_id_list[:].__str__() +
            " instance info set is " +
            self.result_mappers_list[:].__str__())
        request_res_callback(
            self.task_id,
            RES_STATUS_OK,
            self.req_dict,
            self.result_mappers_list)
        Log.logger.debug(
            "Query Task ID " +
            self.task_id.__str__() +
            " Call UOP CallBack Post Success Info.")
        # 停止定时任务并退出
        self.stop()

    @transition_state_logger
    def do_fail(self):
        # 执行失败调用UOP CallBack，提交失败
        request_res_callback(
            self.task_id,
            RES_STATUS_FAIL,
            self.req_dict,
            self.result_mappers_list)
        Log.logger.debug(
            "Query Task ID " +
            self.task_id.__str__() +
            " Call UOP CallBack Post Fail Info.")
        # 停止定时任务并退出
        self.stop()

    @transition_state_logger
    def do_rollback(self):
        self._rollback_all(
            self.resource_id,
            self.uop_os_inst_id_list,
            self.result_inst_id_list)
        self.fail()

    @transition_state_logger
    def do_stop(self):
        # 停止定时任务退出任务线程
        Log.logger.debug("Query Task ID " + self.task_id.__str__() + " Stop.")
        self.is_running = False
        # 停止定时任务并退出
        TaskManager.task_exit(self.task_id)

    @transition_state_logger
    def do_app_cluster(self):
        self.is_need_rollback, uop_os_inst_id_list = self._create_app_cluster(
            self.property_mapper)
        self._add_to_phase4(uop_os_inst_id_list)

    @transition_state_logger
    def do_resource_cluster(self):
        self.is_need_rollback, uop_os_inst_id_list = self._create_resource_cluster(
            self.property_mapper)
        self._add_to_phase4(uop_os_inst_id_list)

    @transition_state_logger
    def do_query(self):
        is_finished, self.is_need_rollback = self._query_resource_set_status(
            self.uop_os_inst_id_list, self.result_inst_id_list, self.result_mappers_list)
        if self.is_need_rollback:
            self.rollback()
        if is_finished is True:
            self.next_phase()

    @transition_state_logger
    def do_status(self):
        # 查询KVM操作系统状态
        is_finished = True
        if is_finished is True:
            self.next_phase()

    @transition_state_logger
    def do_app_push(self):
        # TODO: do app push
        def do_push_nginx_config(kwargs):
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
            self.run_cmd(
                "ansible {nip} --private-key={dir}/playbook-0830/id_rsa_98 -a 'yum install rsync -y'".format(nip=nip,dir=self.dir))
            self.run_cmd(
                "ansible {nip} --private-key={dir}/playbook-0830/id_rsa_98 -m synchronize -a 'src={dir}/update.py dest=/shell/'".format(
                    nip=nip, dir=self.dir))
            self.run_cmd(
                "ansible {nip} --private-key={dir}/playbook-0830/id_rsa_98 -m synchronize -a 'src={dir}/template dest=/shell/'".format(
                    nip=nip, dir=self.dir))
            Log.logger.debug('------>上传配置文件完成')
            self.run_cmd("ansible {nip} --private-key={dir}/playbook-0830/id_rsa_98 -m shell -a 'chmod 777 /shell/update.py'".format(
                nip=nip, dir=self.dir))
            self.run_cmd("ansible {nip} --private-key={dir}/playbook-0830/id_rsa_98 -m shell -a 'chmod 777 /shell/template'".format(
                nip=nip, dir=self.dir))
            self.run_cmd(
                'ansible {nip} --private-key={dir}/playbook-0830/id_rsa_98 -m shell -a '
                '"/shell/update.py {domain} {ip} {port}"'.format(
                    nip=kwargs.get('nip'),
                    dir=self.dir,
                    domain=kwargs.get('domain'),
                    ip=kwargs.get('ip'),
                    port=kwargs.get('port')))
            Log.logger.debug('------>end push')

        real_ip = ''
        app = self.property_mapper.get('app', '')
        app_instance = app.get('instance')
        Log.logger.debug("####current compute instance is:{}".format(self.property_mapper))
        domain_ip = app.get('domain_ip', "")
        for ins in app_instance:
            domain = ins.get('domain', '')
            ip_str = str(ins.get('ip')) + ' '
            real_ip += ip_str
        ports = str(app.get('port'))
        Log.logger.debug(
            'the receive (domain, nginx, ip, port) is (%s, %s, %s, %s)' %
            (domain, domain_ip, real_ip, ports))
        do_push_nginx_config({'nip': domain_ip,
                              'domain': domain,
                              'ip': real_ip.strip(),
                              'port': ports.strip()})
        # do_push_nginx_config({'nip': nginx_ip_slave,
        #                       'domain': domain,
        #                       'ip': real_ip.strip(),
        #                       'port': ports.strip()})

        #添加dns操作#
        try:
            domain_ip = self.property_mapper.get('app',{}).get('domain_ip','10.0.0.1')
            if len(domain_ip.strip()) == 0:
                domain_ip = '10.0.0.1'
            Log.logger.debug("self.property_mapper: %s" % self.property_mapper)
            domain_name = self.property_mapper.get('app',{}).get('domain',{})
            Log.logger.debug('dns add -->ip:%s,domain:%s' %(domain_ip, domain_name))
            self.do_dns_push(domain_name=domain_name, domain_ip=domain_ip)
        except Exception as e:
            Log.logger.debug("dns error: %s" % e.message)

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

    @transition_state_logger
    def do_dns_push(self, domain_name, domain_ip):
        dns_api = NamedManagerApi()
        msg = dns_api.named_dns_domain_add(domain_name=domain_name, domain_ip=domain_ip)
        Log.logger.debug('The dns add result: %s' % msg)

    @transition_state_logger
    def do_mysql_push(self):
        mysql = self.property_mapper.get('mysql', {})
        instance = mysql.get('instance')
        if mysql.get('quantity') == 5:
            mysql_ip_info = []
            mycat_ip_info = []
            master_slave = ['slave2', 'slave1', 'master']
            lvs = ['lvs2', 'lvs1']
            for _instance in instance:
                tup = (_instance['instance_name'], _instance['ip'])
                if _instance['instance_type'] == 'mysql':
                    mysql_ip_info.append(tup)
                    _instance['dbtype'] = master_slave.pop()
                else:
                    mycat_ip_info.append(tup)
                    _instance['dbtype'] = lvs.pop()

            _, vip1 = create_vip_port(mysql_ip_info[0][0])
            _, vip2 = create_vip_port(mysql_ip_info[0][0])
            ip_info = mysql_ip_info + mycat_ip_info
            ip_info.append(('vip1', vip1))
            ip_info.append(('vip2', vip2))
            mysql['wvip'] = vip2
            mysql['rvip'] = vip1
            with open(os.path.join(SCRIPTPATH, 'mysqlmha', 'mysql.txt'), 'wb') as f:
                for host_name, ip in ip_info:
                    f.write(host_name + os.linesep)
                    f.write(ip + os.linesep)

            path = SCRIPTPATH + 'mysqlmha'
            cmd = '/bin/sh {0}/mlm.sh {0}'.format(path)
            strout = ''
            time.sleep(30)
            p = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                strout += line + os.linesep
            Log.logger.debug('mysql cluster push result:%s' % strout)
        else:
            # 当MYSQL为单例时  将实IP当虚IP使用
            mysql['wvip'] = instance[0]['ip']
            mysql['rvip'] = instance[0]['ip']
            instance[0]['dbtype'] = 'master'

    @transition_state_logger
    def do_mongodb_push(self):
        mongodb_ip_list = []
        mongodb = self.property_mapper.get('mongodb', {})
        if mongodb.get('quantity', {}) == 3:
            instance = mongodb.get('instance', '')
            for ins in instance:
                mongodb_ip_list.append(ins.get('ip', ''))
            try:
                mongodb['vip1'] = mongodb_ip_list[0]
                mongodb['vip2'] = mongodb_ip_list[1]
                mongodb['vip3'] = mongodb_ip_list[2]

                instance[0]['dbtype'] = 'slave1'
                instance[1]['dbtype'] = 'slave2'
                instance[2]['dbtype'] = 'master'
            except IndexError as e:
                Log.logger.debug('mongodb ips error {e}'.format(e=e))
            mongodb_ip_list.append(mongodb_ip_list[-1])
            mongodb_cluster = MongodbCluster(mongodb_ip_list)
            mongodb_cluster.exec_final_script()
        else:
            Log.logger.debug('mongodb single instance start')
            instance = mongodb.get('instance', '')
            mongodb['ip'] = instance[0].get('ip')
            Log.logger.debug(
                'mongodb single instance end {ip}'.format(
                    ip=mongodb['ip']))

    @transition_state_logger
    def do_redis_push(self):
        redis = self.property_mapper.get('redis', {})
        instance = redis.get('instance')
        ip1 = instance[0]['ip']
        instance[0]['dbtype'] = 'master'
        # 当redis为单例时  将实IP当虚IP使用
        redis['vip'] = ip1
        if redis.get('quantity') == 2:
            _, vip = create_vip_port(instance[0]['instance_name'])
            ip2 = instance[1]['ip']
            instance[1]['dbtype'] = 'slave'
            redis['vip'] = vip
            cmd = 'python {0}script/redis_cluster.py {1} {2} {3}'.format(
                SCRIPTPATH, ip1, ip2, vip)
            error_time = 0

            def _redis_push():
                out = ''
                p = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                for line in p.stdout.readlines():
                    out += line + os.linesep

                Log.logger.debug('redis cluster push result:%s' % out)
                return out

            strout = ''
            # 执行命令 如果失败 连续重复尝试3次
            while (not strout or 'FAILED!' in strout or 'UNREACHABLE!' in strout) and error_time < 3:
                strout = _redis_push()
                error_time += 1
                time.sleep(5)

            instance[0]['dbtype'] = 'master'
            instance[1]['dbtype'] = 'slave'
            if error_time == 3:
                Log.logger.debug('redis cluster 重试3次失败')


# Transit request_data from the JSON nest structure to the chain structure
# with items_sequence and porerty_json_mapper
def transit_request_data(items_sequence, porerty_json_mapper, request_data):
    if request_data is None:
        return
    if not (
            isinstance(
                items_sequence,
                list) or isinstance(
                items_sequence,
                dict) or isinstance(
                    items_sequence,
                    set)) or not (
                        isinstance(
                            request_data,
                            list) or isinstance(
                                request_data,
                                dict)) or not isinstance(
                                    porerty_json_mapper,
            dict):
        raise Exception(
            "Need input dict for porerty_json_mapper and request_data in transit_request_data.")
    request_items = []
    if isinstance(items_sequence, list) or isinstance(items_sequence, set):
        for one_item_sequence in items_sequence:
            if isinstance(one_item_sequence, dict):
                item_mapper_keys = one_item_sequence.keys()
            elif isinstance(one_item_sequence, basestring):
                item_mapper_keys = [one_item_sequence]
            else:
                raise Exception("Error items_sequence_list_config")
            for item_mapper_key in item_mapper_keys:
                if isinstance(one_item_sequence, basestring):
                    context = None
                else:
                    context = one_item_sequence.get(item_mapper_key)
                item_mapper_body = porerty_json_mapper.get(item_mapper_key)
                if item_mapper_body is not None:
                    if isinstance(
                            request_data,
                            list) or isinstance(
                            request_data,
                            set):
                        for one_req in request_data:
                            item = {}
                            sub_item = copy.deepcopy(one_req)
                            item[item_mapper_key] = sub_item
                            request_items.append(item)
                            if context is not None and sub_item is not None:
                                request_items.extend(transit_request_data(
                                    context, porerty_json_mapper, sub_item))
                    else:
                        item = {}
                        current_item = copy.deepcopy(request_data)
                        item[item_mapper_key] = current_item
                        request_items.append(item)
                        if context is not None:
                            if hasattr(current_item, item_mapper_key):
                                sub_item = current_item.get(item_mapper_key)
                                if sub_item is not None:
                                    request_items.extend(transit_request_data(
                                        context, porerty_json_mapper, sub_item))
                            else:
                                sub_item = current_item
                                if sub_item is not None:
                                    request_items.extend(transit_request_data(
                                        context, porerty_json_mapper, sub_item))
                else:
                    if request_data is not None:
                        sub_item = request_data.get(item_mapper_key)
                        if context is not None and sub_item is not None:
                            request_items.extend(transit_request_data(
                                context, porerty_json_mapper, sub_item))
    elif isinstance(items_sequence, dict):
        items_sequence_keys = items_sequence.keys()
        for items_sequence_key in items_sequence_keys:
            context = items_sequence.get(items_sequence_key)
            item_mapper_body = porerty_json_mapper.get(items_sequence_key)
            if item_mapper_body is not None:
                current_items = copy.deepcopy(request_data)
                if hasattr(item_mapper_body, items_sequence_key):
                    current_items_keys = current_items.keys()
                    for current_item_key in current_items_keys:
                        if current_item_key == items_sequence_key:
                            current_item_body = current_items.get(
                                current_item_key)
                            if current_item_body is not None and len(
                                    current_item_body) > 0:
                                item = current_items
                                request_items.append(item)
                else:
                    current_item_body = current_items
                    if current_item_body is not None and len(
                            current_item_body) > 0:
                        item = {}
                        item[items_sequence_key] = current_item_body
                        request_items.append(item)
                    if context is not None:
                        if hasattr(current_items, items_sequence_key):
                            sub_item = current_items.get(items_sequence_key)
                            if sub_item is not None:
                                request_items.extend(transit_request_data(
                                    context, porerty_json_mapper, sub_item))
                        else:
                            sub_item = current_items
                            if sub_item is not None:
                                request_items.extend(transit_request_data(
                                    context, porerty_json_mapper, sub_item))
            if context is not None and request_data is not None:
                sub_item = request_data.get(items_sequence_key)
                if sub_item is not None:
                    request_items.extend(
                        transit_request_data(
                            context, porerty_json_mapper, sub_item))

    return request_items


# Transit request_items from JSON property to item property with
# property_json_mapper
def transit_repo_items(property_json_mapper, request_items):
    if not isinstance(
            property_json_mapper,
            dict) and not isinstance(
            request_items,
            list):
        raise Exception(
            "Need input dict for property_json_mapper and list for request_items in transit_repo_items.")
    property_mappers_list = []
    for request_item in request_items:
        item_id = request_item.keys()[0]
        repo_property = {}
        item_property_mapper = property_json_mapper.get(item_id)
        item_property_keys = item_property_mapper.keys()
        for item_property_key in item_property_keys:
            value = request_item.get(item_id)
            if value is not None:
                repo_json_property = value.get(
                    item_property_mapper.get(item_property_key))
                if repo_json_property is not None:
                    repo_property[item_property_key] = repo_json_property
        if len(repo_property) >= 1:
            repo_item = {}
            repo_item[item_id] = repo_property
            property_mappers_list.append(repo_item)
    return property_mappers_list


def do_transit_repo_items(
        items_sequence_list,
        property_json_mapper,
        request_data):
    request_items = transit_request_data(
        items_sequence_list, property_json_mapper, request_data)
    property_mappers_list = transit_repo_items(
        property_json_mapper, request_items)
    return property_mappers_list


# request UOP res_callback
def request_res_callback(task_id, status, req_dict, result_mappers_list):
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

    container = []
    db_info = {}
    mysql = {}
    redis = {}
    mongodb = {}

    if status == RES_STATUS_OK:
        for result_mapper in result_mappers_list:
            if result_mapper.keys()[0] == 'app':
                app = result_mapper.get('app')
                if app is not None and app.get('quantity') > 0:
                    container.append(app)
            elif result_mapper.keys()[0] == 'mysql':
                mysql = result_mapper.get('mysql')
            elif result_mapper.keys()[0] == 'redis':
                redis = result_mapper.get('redis')
            elif result_mapper.keys()[0] == 'mongodb':
                mongodb = result_mapper.get('mongodb')

    data["container"] = container

    if mysql is not None and mysql.get('quantity') > 0:
        db_info["mysql"] = mysql
    if redis is not None and redis.get('quantity') > 0:
        db_info["redis"] = redis
    if mongodb is not None and mongodb.get('quantity') > 0:
        db_info["mongodb"] = mongodb

    data["db_info"] = db_info

    data_str = json.dumps(data)
    Log.logger.debug(
        "Task ID " +
        task_id.__str__() +
        " UOP res_callback Request Body is: " +
        data_str)
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
            request_data = json.loads(request.data)
            property_mappers_list = do_transit_repo_items(
                items_sequence_list_config, property_json_mapper_config, request_data)
            Log.logger.debug(
                "property_mappers_list: %s" %
                property_mappers_list)
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

            # init default data
            Log.logger.debug('req_dict\'s object id is :')
            Log.logger.debug(id(req_dict))
            # 创建资源集合定时任务，成功或失败后调用UOP资源预留CallBack（目前仅允许全部成功或全部失败，不允许部分成功）
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
        if res_provider.phase == 'query' and res_provider.state == 'query':
            res_provider.query()
        elif res_provider.phase == 'status' and res_provider.state == 'status':
            res_provider.status()
        else:
            if res_provider.is_running is not True:
                res_provider.start()


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
    #Log.logger.debug('Create port for cluster/instance ' + instance_name)
    response = neutron_client.create_port(body=body_value)
    ip = response.get('port').get('fixed_ips').pop().get('ip_address')
    # Log.logger.debug('Port id: ' + response.get('port').get('id') +
    Log.logger.debug('Port id: ' + response.get('port').get('id') +
                     'Port ip: ' + ip)
    return None, ip


class MongodbCluster(object):

    def __init__(self, ip_list):
        """
        172.28.36.230
        172.28.36.23
        172.28.36.231
        :param cmd_list:
        """
        self.dir = os.path.dirname(
            os.path.abspath(__file__)) + '/' + 'mongo_script'
        self.ip_slave1 = ip_list[0]
        self.ip_slave2 = ip_list[1]
        self.ip_master1 = ip_list[2]
        self.ip_master2 = ip_list[3]
        self.d = {
            self.ip_slave1: 'mongoslave1.sh',
            self.ip_slave2: 'mongoslave2.sh',
            self.ip_master1: 'mongomaster1.sh',
        }
        self.cmd = [
            'ansible {vip} -u root --private-key={rsa_dir}/old_id_rsa -m script -a '
            '"{dir}/mongomaster2.sh sys95"'.format(
                vip=self.ip_master2,
                rsa_dir=self.dir,
                dir=self.dir)]
        self.ip = [self.ip_slave1, self.ip_slave2, self.ip_master1]
        self.new_host = '[new_host]'
        self.write_ip_to_server()
        self.flag = False
        self.telnet_ack()

    def write_ip_to_server(self):
        for ip in self.ip:
            with open('/etc/ansible/hosts', 'a') as f:
                f.write('%s\n' % ip)

    def telnet_ack(self):
        start_time = time.time()
        while not self.flag:
            for ip in self.ip:
                p = subprocess.Popen(
                    'nmap %s -p 22' %
                    str(ip),
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
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
            end_time = time.time()
            if start_time - end_time > 180:
                break
            if len(self.ip) == 0:
                self.flag = True

    def mongodb_cluster_push(self, ip):
        # vip_list = list(set(self.ip))
        # vip_list = [ip_master1, ip_slave1, ip_slave2]
        script_name = [
            'mongoslave1.sh',
            'mongoslave2.sh',
            'mongomaster1.sh',
            'mongomaster2.sh',
            'old_id_rsa']
        for i in script_name:
            os.system('chmod 600 {dir}'.format(dir=self.dir + '/' + i))
        cmd_before = "ansible {vip} --private-key={dir}/old_id_rsa -m synchronize -a 'src=/opt/uop-crp/crp/res_set/" \
                     "write_mongo_ip.py dest=/tmp/'".format(vip=ip, dir=self.dir)
        authority_cmd = 'ansible {vip} -u root --private-key={dir}/old_id_rsa -m shell -a ' \
                        '"chmod 777 /tmp/write_mongo_ip.py"'.format(vip=ip, dir=self.dir)
        cmd1 = 'ansible {vip} -u root --private-key={dir}/old_id_rsa -m shell -a "python /tmp/write_mongo_ip.py' \
               ' {m_ip} {s1_ip} {s2_ip}"'.format(vip=ip, dir=self.dir, m_ip=self.ip_master1, s1_ip=self.ip_slave1, s2_ip=self.ip_slave2)
        Log.logger.debug('开始上传脚本%s' % ip)
        p = subprocess.Popen(
            cmd_before,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line
            Log.logger.debug('mongodb cluster cmd before:%s' % line)
        Log.logger.debug('开始修改权限%s' % ip)
        p = subprocess.Popen(
            authority_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line
            Log.logger.debug('mongodb cluster authority:%s' % line)
        Log.logger.debug('脚本上传完成,开始执行脚本%s' % ip)
        p = subprocess.Popen(
            cmd1,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line
            Log.logger.debug('mongodb cluster exec write script:%s' % line)
        Log.logger.debug('脚本执行完毕 接下来会部署%s' % ip)
        # for ip in self.ip:
        with open('/tmp/hosts', 'w') as f:
            f.write('%s\n' % ip)
        print '-----', ip, type(ip)
        script = self.d.get(ip)
        # if str(ip) != '172.28.36.105':
        cmd_s = 'ansible {vip} -u root --private-key={rsa_dir}/old_id_rsa -m script -a "{dir}/{s} sys95"'.\
                format(vip=ip, rsa_dir=self.dir, dir=self.dir, s=script)
        # else:
        #     cmd_s = 'ansible {vip} -u root --private-key=/home/mongo/old_id_rsa -m script -a "/home/mongo/
        # mongoclu_install/{s}"'.format(vip=ip, s=script)
        p = subprocess.Popen(
            cmd_s,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print line,
            Log.logger.debug(
                'mongodb cluster push result:%s, -----%s' %
                (line, ip))

    def exec_final_script(self):
        for i in self.cmd:
            p = subprocess.Popen(
                i,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                print line,
                Log.logger.debug('mongodb cluster push result:%s' % line)


resource_set_api.add_resource(ResourceSet, '/sets')
