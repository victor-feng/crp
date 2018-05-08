# -*- coding: utf-8 -*-

import os

APP_ENV = "development"

class BaseConfig:
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    TESTING = True
    DEBUG = True

    UOP_URL = "http://uop-dev.syswin.com/"
    MPC_URL = "http://mpc-dev.syswin.com/"
    OPENRC_PATH = "/root/openrc"
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.19'
    DK_TAR_PATH = '/home/dk/'
    GLANCE_RESERVATION_QUANTITY = 100
    UPLOAD_FOLDER = '/data/'
    AP_NETWORK_CONF = {
        'AZ_UOP': '7aca50a9-cf4b-4cc7-b078-be055dd7c6af',
        'hyperv_test': 'c12740e6-33c8-49e9-b17d-6255bb10cd0c'
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
            'uuid': '817d3140-0b82-4722-9816-3cee734f22b6',
            'name': 'mysqluop-80G-20170426',
            'port': '3316'
        },
        'redis': {
            'uuid': '12f260fd-1196-4b68-8d37-d9f1d322c842',
            'name': 'redis-50G-20170428',
            'port': '6379'
        },
        'mongodb': {
            'uuid': 'ccc48185-961a-405e-95b5-136c4ed77c69',
            'name': 'mongosas-50G-20170428',
            'port': '27017'
        },
        'mycat': {
            'uuid': 'daf34739-7dc3-4d4f-abb1-3a222b796944',
            'name': 'mycat-50G-20180105',
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

    KVM_FLAVOR = {
        '22':'9ff4c08d-ad94-4417-b90a-bf4382cae768', #uop_2C2G30G
        '24': '0471bc46-4ced-4e35-a2e7-7c56aa71ff52', # tst-pc-2C4G50G
        '44':'280d8672-fdb4-4a87-9280-deca23263de5', #uop_4C4G30G
        'mysql': '20f28b8b-7adb-48c4-a7d0-d562007123b6',  # mysql_2C4G80G
        '48': '00d92209-b17e-45cb-991c-d79600e68969',  # xiaojian_sas_4C8G50G
        "mycat": "135154ad-a637-4d29-ac2d-b4f63a2183b5",  # tst-dns-2C2G50G
        "816": '105deffb-dff9-4a16-8757-92a9d44e9b91',  # K8S-8C16G50G
        "832": '8257eac4-c9cb-48f0-b5d4-183e3e08137f',  # pret-mysql-8C32G80G
    }
    DOCKER_FLAVOR = {
        "22": "83c52038-3cc1-4865-958a-a85cfde96bc0",
    }

    AVAILABILITY_ZONE = {
        "dev": 'AZ_UOP',
        "test": 'AZ_UOP',
        "prod": 'AZ_UOP',
    }
    DEV_NETWORK_ID = '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
    OS_EXT_PHYSICAL_SERVER_ATTR = 'OS-EXT-SRV-ATTR:host'

    # res_callback
    RES_CALLBACK = {
        "uop": "".join([UOP_URL, 'api/res_callback/res']),
        "cloud": 'http://172.28.50.18:5001/api/res_callback/callback'
    }
    RES_DELETE_CALL_BACK = {
        "uop": "".join([UOP_URL, "api/res_callback/delete"]),
        "cloud": "http://172.28.50.18:5001/api/res_callback/callback"
    }

    RES_STATUS_CALLBACK = "".join([UOP_URL, 'api/res_callback/status'])
    DEP_STATUS_CALLBACK = "".join([UOP_URL, 'api/dep_result/status'])

    RES_STATUS_OK = "ok"
    RES_STATUS_FAIL = "fail"
    RES_STATUS_DEFAULT = 'unreserved'

    DEFAULT_USERNAME = "root"
    DEFAULT_PASSWORD = "123456"

    HEALTH_CHECK_PORT = "8000"
    HEALTH_CHECK_PATH = "admin/health"
    OS_DOCKER_LOGS= "/data/os_docker_logs"

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
            'meta': 'meta',
            'quantity': 'quantity',
            'network_id': 'network_id',
            'networkName': 'networkName',
            'tenantName': 'tenantName',
            'availability_zone':'availability_zone',
            'flavor': 'flavor',
            'host_env':'host_env',
            'image_id': 'image_id',
            'language_env':'language_env',
            'deploy_source':'deploy_source',
            'database_config':'database_config',
            'lb_methods':'lb_methods',
            'namespace':'namespace',
            'ready_probe_path':'ready_probe_path',
            'domain_path':'domain_path',
            'host_mapping':'host_mapping',
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
            'availability_zone':'availability_zone',
            'flavor': 'flavor',
            'volume_exp_size':'volume_exp_size',
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
    NAMEDMANAGER_URL = {
        "dev": "http://172.28.39.94/namedmanager/api/dnsapi.php",
        "test": "http://172.28.39.94/namedmanager/api/dnsapi.php",
        "prep": "http://10.253.68.85/namedmanager/api/dnsapi.php",
        "prod": "http://10.253.68.85/namedmanager/api/dnsapi.php",
    }

    DISCONF_SERVER = {
        "host": "172.28.11.111",
        "port": "8081",
        "user": "admin",
        "password": "admin"
    }
    IS_OPEN_AFFINITY_SCHEDULING = False

    MYSQL_NETWORK = "172.%" #mysql数据库可以访问的网段

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
        '22': 'ec2b05b1-dd4e-4198-b8ce-738f62c14952', #2C2G30G
        '24': '4faa9926-462c-456f-bb71-3e6cecdec252',  # tst-pc-2C4G50G
        '44': '00da3f51-a8ce-4a0a-b30d-994b4bab94ff', #4C4G30G
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
    HOST_MAPPING =[
            {
            "ip":"127.0.0.1",
            "hostnames":["uop-k8s.syswin.com"],
             },
        ]
    NETWORKNAME = "contiv-vlan651"
    TENANTNAME = "tenant-vlan651"
    K8S_NETWORK_URL = {
        "dev": "http://172.28.13.254:19999/api/v1/networks/",
        "test": "http://172.28.13.254:19999/api/v1/networks/",
        "prep": "http://172.28.13.254:19999/api/v1/networks/",
        "prod": "http://172.28.13.254:19999/api/v1/networks/",
    }

    BASE_IMAGE_URL = "reg1.syswin.com/base/os69-tomcat7:v0.1"
    CHECK_TIMEOUT = 200

configs = {
    'development': DevelopmentConfig,
}

