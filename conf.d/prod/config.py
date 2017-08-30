# -*- coding: utf-8 -*-

import os

APP_ENV = "prod"


class BaseConfig:
    DEBUG = False

class ProdConfig(BaseConfig):
    TESTING = True
    DEBUG = True

    # NOTE: noused in mpc
    UOP_URL = "http://uop.syswin.com/" #域名自己定义好后想运维申请，我自己先定了prod
    # UOP_URL = "http://172.28.20.124:5000/"
    MPC_URL = "http://mpc.syswin.com/"
    OPENRC_PATH = "/root/openrc"

    # NOTE: noused in mpc
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.22'

    # NOTE: noused in mpc
    DK_TAR_PATH = '/home/dk/'
    GLANCE_RESERVATION_QUANTITY = 3
    UPLOAD_FOLDER = '/data/'

    # TODO:
    AP_NETWORK_CONF = {
        'AZ_UOP': 'AZ-UOP-HYPERUOP-LXC-SAS-76' #待确认
    }	

    MONGODB_SCRIPT_PATH = 'uop-crp/crp/res_set/mongo_script/'
    MONGODB_PATH = '/opt/mongodb/bin/mongo 127.0.0.1:28010'
    #镜像信息找王刚已经确认
    cluster_type_image_port_mappers = {
        'mysql': {
            'uuid': '4b6abfae-edd9-486f-8552-694504e9cd58',
            'name': 'mysqlssd-80G-20170627',
            'port': '3316'
        },
        'redis': {
            'uuid': 'adb4d545-fadc-485b-b7ed-2f8c709d3218',
            'name': 'redis-50G-20170428',
            'port': '6379'
        },
        'mongodb': {
            'uuid': 'd4803ad1-21df-4ea7-a6b6-aef98c56344c',
            'name': 'mongossd-50G-20170428',
            'port': '27017'
        },
        'mycat': {
            'uuid': 'aa80be12-b88d-477c-a2d8-443d09b81887',
            'name': 'mycat-50G-20170628',
            'port': '3316'
        }
    }

    # scm2-dev--1C2G80G
    FLAVOR_1C2G = 'scm2-dev--1C2G80G'   #写死的信息,可能还需要修改
    # docker-2C4G25G
    DOCKER_FLAVOR_2C4G = 'e90d8d25-c5c7-46d7-ba4e-2465a5b1d266' # 写死的信息,可能还需要修改

    # AVAILABILITY_ZONE
    AVAILABILITY_ZONE_AZ_UOP = 'AZ-UOP-HYPERUOP-KVM-SAS-31/32'
    DEV_NETWORK_ID = 'AZ-UOP-HYPERUOP-KVM-SAS-31/32'
    OS_EXT_PHYSICAL_SERVER_ATTR = 'OS-EXT-SRV-ATTR:host'

    # res_callback
    RES_CALLBACK = 'http://uop.syswin.com/api/res_callback/res'

    RES_STATUS_OK = "ok"
    RES_STATUS_FAIL = "fail"
    RES_STATUS_DEFAULT = 'unreserved'

    DEFAULT_USERNAME = "root"
    DEFAULT_PASSWORD = "123456"

    # Define Request JSON Format
    items_sequence_list_config = [
        {
            'compute_list':
                [
                    'app_cluster'
                ],
            'resource_list':
                [
                    'resource_cluster'
                ]
        }]

    # Define Item Property to JSON Property Mapper
    property_json_mapper_config = {
        'app_cluster': {
            'cluster_name': 'instance_name',
            'cluster_id': 'instance_id',
            'domain': 'domain',
            'image_url': 'image_url',
            'cpu': 'cpu',
            'domain_ip': 'domain_ip',
            'mem': 'mem',
            'port': 'port',
            'quantity': 'quantity'
        },
        'resource_cluster': {
            'cluster_name': 'instance_name',
            'cluster_id': 'instance_id',
            'cluster_type': 'instance_type',
            'version': 'version',
            'cpu': 'cpu',
            'mem': 'mem',
            'disk': 'disk',
            'quantity': 'quantity'
        }
    }
    SCRIPTPATH = r'crp/res_set/playbook-0830/'
    #DNS配置
    DNS_CONDIG = {
    'host': '172.28.50.141',
    'port': 22,
    'username': 'root',
    'password': '123456'
    }
    NAMEDMANAGER_URL = 'http://itop.syswin.com/dnsapi.php'   #已经找吴兆远确认 namedmanager 信息
    IS_OPEN_AFFINITY_SCHEDULING = False


configs = {
    'prod': ProdConfig,
}

