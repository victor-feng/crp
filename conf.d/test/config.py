# -*- coding: utf-8 -*-

import os

APP_ENV = "testing"


class BaseConfig:
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True

    #NOTE: noused in mpc
    UOP_URL = "http://uop-test.syswin.com/"
    #UOP_URL = "http://172.28.20.124:5000/"
    MPC_URL = "http://mpc-test.syswin.com/"
    OPENRC_PATH = "/root/openrc"
    
    #NOTE: noused in mpc
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.22'

    #NOTE: noused in mpc
    DK_TAR_PATH = '/home/dk/'
    GLANCE_RESERVATION_QUANTITY = 3
    UPLOAD_FOLDER = '/data/'
    #NOTE: noused in uop
    #NOTE: config it !!!! TODO:
    #TODO:? hard code?
    AP_NETWORK_CONF = {
        'AZ_UOP': '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
    }
    #nginx_ip = '172.28.20.98'
    #nginx_ip_slave = '172.28.11.111'
    MONGODB_SCRIPT_PATH = 'uop-crp/crp/res_set/mongo_script/'
    MONGODB_PATH = '/opt/mongodb/bin/mongo 127.0.0.1:28010'

    cluster_type_image_port_mappers = {
        'mysql': {
            'uuid': '817d3140-0b82-4722-9816-3cee734f22b6',
            'name': 'mysqluop-80G-20170426',
            'port': '3316'
        },
        'redis': {
            'uuid': '3da55e5b-814c-4935-abf0-1469ae606286',
            'name': 'redis-50G-20170428',
            'port': '6379'
        },
        'mongodb': {
            'uuid': '95863650-6816-4588-846a-c0423b5baae0',
            'name': 'mongosas-50G-20170428',
            'port': '27017'
        },
        'mycat': {
            'uuid': '59a5022b-3c46-47ec-8e97-b63edc4b7be0',
            'name': 'mycat-50G-20170628',
            'port': '3316'
        }
    }

    # scm2-dev--1C2G80G
    FLAVOR_1C2G = 'scm2-dev--1C2G80G'
    # docker-2C4G25G
    DOCKER_FLAVOR_2C4G = 'e90d8d25-c5c7-46d7-ba4e-2465a5b1d266'
    # AVAILABILITY_ZONE
    AVAILABILITY_ZONE_AZ_UOP = 'AZ_UOP'
    DEV_NETWORK_ID = '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
    OS_EXT_PHYSICAL_SERVER_ATTR = 'OS-EXT-SRV-ATTR:host'

    # res_callback
    RES_CALLBACK = 'http://uop-test.syswin.com/api/res_callback/res'

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
            'mem': 'mem',
            'domain_ip': 'domain_ip',
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
    DNS_ENV = {'develop': '172.28.5.21', 'test': '172.28.20.98'}
    #DNS配置
    DNS_CONDIG = {
        'host': '172.28.50.141',
        'port': 22,
        'username': 'root',
        'password': '123456'
        }
    #NAMEDMANAGER_URL = 'http://itop.syswin.com/dnsapi.php'
    NAMEDMANAGER_URL = 'http://172.28.50.141/namedmanager/dnsapi.php'
    IS_OPEN_AFFINITY_SCHEDULING = False

configs = {
    'testing': TestingConfig,
}
