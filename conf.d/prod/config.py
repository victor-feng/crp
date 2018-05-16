# -*- coding: utf-8 -*-

import os

APP_ENV = "prod"


class BaseConfig:
    DEBUG = False

class ProdConfig(BaseConfig):
    TESTING = False
    DEBUG = False

    # NOTE: noused in mpc
    UOP_URL = "http://uop.syswin.com/" #域名自己定义好后想运维申请，我自己先定了prod
    # UOP_URL = "http://172.28.20.124:5000/"

    #mpc url, ignore if not use mpc 
    MPC_URL = "http://mpc.syswin.com/" 

    #Cloud1.0 openstack openrc,ignore if use Cloud2.0
    OPENRC_PATH = "/root/openrc" 

    # NOTE: noused in mpc
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.19'

    # NOTE: noused in mpc
    DK_TAR_PATH = '/home/dk/'
    GLANCE_RESERVATION_QUANTITY = 100
    UPLOAD_FOLDER = '/data/'

    # disconf server config
    DISCONF_SERVER = {
        "host": "172.28.11.111",
        "port": "8081",
        "user": "admin",
        "password": "admin"
    }

    # Cloud1.0 openstack zone and network mapping, ignore if use Cloud2.0
    AP_NETWORK_CONF = {
        'AZ_UOP': 'AZ-UOP-HYPERUOP-LXC-SAS-76' 
    }	

    MONGODB_PATH = '/opt/mongodb/bin/mongo 127.0.0.1:28010'
    MONGODB_AUTH_PATH = '/opt/mongodb/bin/mongo 127.0.0.1:28010 --authenticationDatabase admin -u admin -p 123456'

    HARBOR_URL = "reg1.syswin.com"
    HARBOR_USERNAME = "crm_test1"
    HARBOR_PASSWORD = "syswin#"

    ADD_LOG = {
        "WAR_DICT":
            [
                "war_to_image_running",
                "war_to_image_success"
            ],
        "BUILD_IMAGE":
            [
                "build_image_running",
                "build_image_success"
            ],
        "PUSH_IMAGE":
            [
                "push_image_running",
                "push_image_success"
            ]

    }

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
        },
        'kvm': {
            'uuid': '75fadfb9-2e17-46ec-a3b7-da3b50a27735',
            'name': 'basic-50G-20170428',
            'port': '22'
        },
        'java': {
            'uuid': 'abdc1770-ee4a-43a0-a83e-e5107a37012a',
            'name': 'tomcat-30G-20180308',
            'port': '8081'
        }
    }

    #KVM_FLAVOR = {
    #    # '2': 'uop-2C4G80G',
    #    # '4': 'uop-4C8G80G',
    #    '48': '2a01b654-3b84-45e5-ac7a-5bf5f2730c74', #prod-redis-4C8G50G
    #    # "8": 'xiaojian_sas_4C8G50G',
    #    "mycat": "363f6916-f699-46d1-960b-06ed2b17c232", # prod - nginx - 4C4G50G
    #    "816": '11e80fa5-3076-4dbc-a6bb-49de2e304694', # prod-8C16G50G-sas
    #    "832": '762d5741-6b98-4ba1-b853-1807fd8a7506', # prodsas-mysql-8C32G80G
    #}

    #Cloud1.0 kvm flavor
    KVM_FLAVOR = {
        '22': '9ff4c08d-ad94-4417-b90a-bf4382cae768',  # uop_2C2G30G
        '24': '0471bc46-4ced-4e35-a2e7-7c56aa71ff52',  # tst-pc-2C4G50G
        '44': '280d8672-fdb4-4a87-9280-deca23263de5',  # uop_4C4G30G
        'mysql': '20f28b8b-7adb-48c4-a7d0-d562007123b6',  # mysql_2C4G80G
        '48': '00d92209-b17e-45cb-991c-d79600e68969',  # xiaojian_sas_4C8G50G
        "mycat": "135154ad-a637-4d29-ac2d-b4f63a2183b5",  # tst-dns-2C2G50G
        "816": '105deffb-dff9-4a16-8757-92a9d44e9b91',  # K8S-8C16G50G
        "832": '8257eac4-c9cb-48f0-b5d4-183e3e08137f',  # pret-mysql-8C32G80G
    }

    #DOCKER_FLAVOR = {
    #    # "22": "uop-docker-2C4G50G",
    #    "24": "96f98a7f-ab4e-4e1c-a597-ccac02306df9" #prod-docker-tomcat-4C4G30G
    #}

    # Cloud1.0 tomcat flavor docker-tomcat-2C2G25G, ignore if use Cloud2.0
    DOCKER_FLAVOR = {
        "2": "83c52038-3cc1-4865-958a-a85cfde96bc0",
    }


    # AVAILABILITY_ZONE, uop env and zone mapping
    AVAILABILITY_ZONE = {
        "dev": 'AZ_UOP',
        "test": 'AZ_UOP',
        "prep": 'AZ-UOP',
        "prod": 'AZ-UOP',
    }

    OS_EXT_PHYSICAL_SERVER_ATTR = 'OS-EXT-SRV-ATTR:host'

    # res_callback
    #RES_CALLBACK = "".join([UOP_URL, 'api/res_callback/res'])
    RES_CALLBACK = {
        "uop": UOP_URL + 'api/res_callback/res',
        "cloud": 'http://172.28.50.18:5001/api/res_callback/callback'
    }
    RES_DELETE_CALL_BACK = {
        "uop": UOP_URL + "api/res_callback/delete",
        "cloud": "http://172.28.50.18:5001/api/res_callback/callback"
    }
    RES_STATUS_CALLBACK = "".join([UOP_URL, 'api/res_callback/status'])
    DEP_STATUS_CALLBACK = "".join([UOP_URL, 'api/dep_result/status'])
    RES_STATUS_OK = "ok"
    RES_STATUS_FAIL = "fail"
    RES_STATUS_DEFAULT = 'unreserved'

    #openstack kvm default username
    DEFAULT_USERNAME = "root"
    #openstack kvm default password
    DEFAULT_PASSWORD = "123456"

    #micro server health check port
    HEALTH_CHECK_PORT = "8000"
    #micro server health check path
    HEALTH_CHECK_PATH = "admin/health"
    #Cloud1.0 docker logs, at CRP node,ignore if use Cloud2.0
    OS_DOCKER_LOGS = "/data/os_docker_logs"

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
            'meta': 'meta',
            'quantity': 'quantity',
            'network_id': 'network_id',
            'networkName': 'networkName',
            'tenantName': 'tenantName',
            'availability_zone': 'availability_zone',
            'flavor': 'flavor',
            'host_env': 'host_env',
            'image_id': 'image_id',
            'language_env': 'language_env',
            'deploy_source': 'deploy_source',
            'database_config': 'database_config',
            'lb_methods': 'lb_methods',
            'namespace': 'namespace',
            'ready_probe_path': 'ready_probe_path',
            'domain_path': 'domain_path',
            'host_mapping': 'host_mapping',
        },
        'resource_cluster': {
            'cluster_name': 'instance_name',
            'cluster_id': 'instance_id',
            'cluster_type': 'instance_type',
            'version': 'version',
            'cpu': 'cpu',
            'mem': 'mem',
            'disk': 'disk',
            'quantity': 'quantity',
            'volume_size': 'volume_size',
            'network_id': 'network_id',
            'image_id': 'image_id',
            'availability_zone': 'availability_zone',
            'flavor': 'flavor',
            'flavor2': 'flavor2',
            'volume_exp_size':'volume_exp_size',
            "port":"port",
        }
    }

    #playbook path
    SCRIPTPATH = r'crp/res_set/playbook-0830/'
    #DNS配置
    DNS_CONDIG = {
        'host': '172.28.50.141',
        'port': 22,
        'username': 'root',
        'password': '123456'
    }
    #NAMEDMANAGER_URL = 'http://10.253.68.85/api/dnsapi.php'   #已经找吴兆远确认 namedmanager 信息
    NAMEDMANAGER_URL = {
        "dev": "http://172.28.4.228/api/dnsapi.php",
        "test": "http://172.28.18.82/api/dnsapi.php",
        "prep": "http://10.253.68.85/api/dnsapi.php",
        "prod": "http://10.253.68.85/api/dnsapi.php",
    }

    # openstack affinity config
    IS_OPEN_AFFINITY_SCHEDULING = False
    MYSQL_NETWORK = "10.%"  # mysql数据库可以访问的网段

    #####################cloud2.0相关####################

    OPENRC2_PATH = "/root/openrc2"
    K8S_CONF_PATH = "/root/k8s.config"
    # 可用域
    AVAILABILITY_ZONE2 = {
        "dev": 'AZ_GENERAL',
        "test": 'AZ_GENERAL',
        "prep": 'AZ_GENERAL',
        "prod": 'AZ_GENERAL',
    }
    cluster_type_image_port_mappers2 = {
        'mysql': {
            'uuid': '914cacfd-bedf-4da7-83a3-c7ffea75f239',
            'name': 'mysql_sas_80G_20180130',
            'port': '3316'
        },
        'redis': {
            'uuid': '9c565dab-91a9-4084-b9b0-5e3b3dfd989f',
            'name': 'redis-50G-20170428',
            'port': '6379'
        },
        'mongodb': {
            'uuid': 'ccc48185-961a-405e-95b5-136c4ed77c69',
            'name': 'mongosas-50G-20170428',
            'port': '27017'
        },
        'mycat': {
            'uuid': 'b722a8e1-b21d-4a29-b8ed-93358950f1c4',
            'name': 'mycat-50G-20180105',
            'port': '3316'
        },
        'kvm': {
            'uuid': 'd67a2e33-cbb7-43f6-85da-8e3ca2873b2a',
            'name': 'basic',
            'port': '22'
        },
         'java': {
            'uuid': '60847610-0849-42c2-8300-484e04847338',
            'name': 'tomcat2C2G30G-20180507',
            'port': '8081'
        }
    }
    KVM_FLAVOR2 = {
        '22': 'ec2b05b1-dd4e-4198-b8ce-738f62c14952',  # 2C2G30G
        '24': '4faa9926-462c-456f-bb71-3e6cecdec252',  # tst-pc-2C4G50G
        '44': '00da3f51-a8ce-4a0a-b30d-994b4bab94ff',  # 4C4G30G
        'mysql': '6ef6287c-f4d4-4d08-9b33-901f47542a69',  # mysql_2C4G80G
        '48': '00d92209-b17e-45cb-991c-d79600e68969',  # xiaojian_sas_4C8G50G
        "mycat": "905e3a5f-6b27-46ab-8cb2-2bb26ffbea58",  # mycat-20180105
        "816": '105deffb-dff9-4a16-8757-92a9d44e9b91',  # K8S-8C16G50G
        "832": '8257eac4-c9cb-48f0-b5d4-183e3e08137f',  # pret-mysql-8C32G80G
    }
    # k8s配置相关
    NAMESPACE = "test-uop"
    FILEBEAT_NAME = "filebeat"
    FILEBEAT_IMAGE_URL = "dkreg-wj.syswin.com/base/filebeat:5.4.0"
    FILEBEAT_REQUESTS = {
        "05002": {"cpu": 0.1, "memory": "20Mi"}
    }
    FILEBEAT_LIMITS = {
        "101": {"cpu": 0.5, "memory": "100Mi"}

    }
    APP_REQUESTS = {
        "22": {"cpu": 0.225, "memory": "2Gi"},
        "44": {"cpu": 0.445, "memory": "4Gi"}
    }
    APP_LIMITS = {
        "22": {"cpu": 2, "memory": "2Gi"},
        "44": {"cpu": 4, "memory": "4Gi"}
    }
    HOST_MAPPING = [
        {
            "ip": "127.0.0.1",
            "hostnames": ["uop-k8s.syswin.com"],
        },
    ]
    NETWORKNAME = "contiv-vlan651"
    TENANTNAME = "tenant-vlan651"
    K8S_NETWORK_URL = {
        "dev": "http://172.28.11.252:19999/api/v1/networks/",
        "test": "http://172.28.11.252:19999/api/v1/networks/",
        "prep": "http://172.28.11.252:19999/api/v1/networks/",
        "prod": "http://172.28.11.252:19999/api/v1/networks/",
    }

    BASE_IMAGE_URL = "reg1.syswin.com/base/os69-tomcat7:v0.1"
    CHECK_TIMEOUT = 200

configs = {
    'prod': ProdConfig,
}

