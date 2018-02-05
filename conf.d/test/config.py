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
    DK_CLI_VERSION = '1.19'

    #NOTE: noused in mpc
    DK_TAR_PATH = '/home/dk/'
    GLANCE_RESERVATION_QUANTITY = 100
    UPLOAD_FOLDER = '/data/'
    #NOTE: noused in uop
    #NOTE: config it !!!! TODO:
    #TODO:? hard code?
    AP_NETWORK_CONF = {
        'AZ_UOP': '7aca50a9-cf4b-4cc7-b078-be055dd7c6af',
        'hyperv_test': 'c12740e6-33c8-49e9-b17d-6255bb10cd0c'
    }

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

    # KVM_FLAVOR = {
    #     '2': 'uop-2C4G80G',
    #     '4': 'uop-4C8G80G',
    #     "mycat": "242c5ee6-d9b5-4456-88db-7603e765f075",  # pret-nginx-4C4G50G
    # }
    # DOCKER_FLAVOR = {
    #     "2": "uop-docker-2C4G50G",
    #     "4": "uop-docker-4C8G50G"
    # }
    KVM_FLAVOR = {
        '24': '0471bc46-4ced-4e35-a2e7-7c56aa71ff52', # tst-pc-2C4G50G
        'mysql':'20f28b8b-7adb-48c4-a7d0-d562007123b6', #mysql_2C4G80G
        # '4': 'uop-4C8G80G',
        '48': '00d92209-b17e-45cb-991c-d79600e68969',  # xiaojian_sas_4C8G50G
        # "8": 'xiaojian_sas_4C8G50G',
        "mycat": "135154ad-a637-4d29-ac2d-b4f63a2183b5",  # tst-dns-2C2G50G
        "816": '105deffb-dff9-4a16-8757-92a9d44e9b91',  # K8S-8C16G50G
        "832": '8257eac4-c9cb-48f0-b5d4-183e3e08137f',  # pret-mysql-8C32G80G
        # 'uop-4C16G180G': 'uop-4C16G180G',
        # 'uop-8C8180G': 'uop-8C8G180G',
        # 'uop-8C32G180G': 'uop-8C32G180G',
    }
    DOCKER_FLAVOR = {
        "22": "83c52038-3cc1-4865-958a-a85cfde96bc0",
        # "24": "uop-docker-4C4G30G"
    }
    # AVAILABILITY_ZONE
    #AVAILABILITY_ZONE_AZ_UOP = 'AZ_UOP'
    AVAILABILITY_ZONE = {
        "dev": 'AZ_UOP',
        "test": 'AZ_UOP',
        "prep": 'AZ-UOP',
        "prod": 'AZ-UOP',
    }
    DEV_NETWORK_ID = '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
    OS_EXT_PHYSICAL_SERVER_ATTR = 'OS-EXT-SRV-ATTR:host'

    # res_callback
    RES_CALLBACK = {
        "uop":'http://uop-test.syswin.com/api/res_callback/res',
        "cloud2-backend":'http://172.28.50.18:5001/api/res_callback/callback'
    }
    RES_DELETE_CALL_BACK={
        "uop":"http://uop-test.syswin.com/api/res_callback/delete",
        "cloud2-backend":"http://172.28.50.18:5001/api/res_callback/callback"
    }
    RES_STATUS_CALLBACK = 'http://uop-test.syswin.com/api/res_callback/status'
    DEP_STATUS_CALLBACK = 'http://uop-test.syswin.com/api/dep_result/status'
    RES_STATUS_OK = "ok"
    RES_STATUS_FAIL = "fail"
    RES_STATUS_DEFAULT = 'unreserved'

    DEFAULT_USERNAME = "root"
    DEFAULT_PASSWORD = "123456"

    HEALTH_CHECK_PORT = "8000"
    HEALTH_CHECK_PATH = "admin/health"
    OS_DOCKER_LOGS = "/os_docker_logs"

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
            'network_id':'network_id',
            'networkName':'networkName',
            'tenantName':'tenantName',
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
    #NAMEDMANAGER_URL = 'http://172.28.50.141/namedmanager/dnsapi.php'
    NAMEDMANAGER_URL = {
        "dev": "http://172.28.50.141/namedmanager/dnsapi.php",
        "test": "http://172.28.50.141/namedmanager/dnsapi.php",
        "prep": "http://10.253.68.85/api/dnsapi.php",
        "prod": "http://10.253.68.85/api/dnsapi.php",
    }
    IS_OPEN_AFFINITY_SCHEDULING = False

    #####################cloud2.0相关####################
    OPENRC2_PATH = "/root/openrc2"
    K8S_CONF_PATH="/root/k8s.config"
    #可用域
    AVAILABILITY_ZONE2 = {
        "dev": 'AZ_GENERAL',
        "test": 'AZ_GENERAL',
        "prep": 'AZ_GENERAL',
        "prod": 'AZ_GENERAL',
    }
    cluster_type_image_port_mappers2 = {
        'mysql': {
            'uuid': 'd67a2e33-cbb7-43f6-85da-8e3ca2873b2a',
            'name': 'mysqluop-80G-20170426',
            'port': '3316'
        },
        'redis': {
            'uuid': 'd67a2e33-cbb7-43f6-85da-8e3ca2873b2a',
            'name': 'redis-50G-20170428',
            'port': '6379'
        },
        'mongodb': {
            'uuid': 'd67a2e33-cbb7-43f6-85da-8e3ca2873b2a',
            'name': 'mongosas-50G-20170428',
            'port': '27017'
        },
        'mycat': {
            'uuid': 'd67a2e33-cbb7-43f6-85da-8e3ca2873b2a',
            'name': 'mycat-50G-20170628',
            'port': '3316'
        },
        'kvm': {
            'uuid': 'd67a2e33-cbb7-43f6-85da-8e3ca2873b2a',
            'name': 'kvm-50G-20170628',
            'port': '8081'
        }
    }
    KVM_FLAVOR = {
        '24': '905e3a5f-6b27-46ab-8cb2-2bb26ffbea58',  # tst-pc-2C4G50G
        'mysql': '905e3a5f-6b27-46ab-8cb2-2bb26ffbea58',  # mysql_2C4G80G
        'kvm': '905e3a5f-6b27-46ab-8cb2-2bb26ffbea58',  # mysql_2C4G80G
        # '4': 'uop-4C8G80G',
        '48': '00d92209-b17e-45cb-991c-d79600e68969',  # xiaojian_sas_4C8G50G
        # "8": 'xiaojian_sas_4C8G50G',
        "mycat": "135154ad-a637-4d29-ac2d-b4f63a2183b5",  # tst-dns-2C2G50G
        "816": '105deffb-dff9-4a16-8757-92a9d44e9b91',  # K8S-8C16G50G
        "832": '8257eac4-c9cb-48f0-b5d4-183e3e08137f',  # pret-mysql-8C32G80G
        # 'uop-4C16G180G': 'uop-4C16G180G',
        # 'uop-8C8180G': 'uop-8C8G180G',
        # 'uop-8C32G180G': 'uop-8C32G180G',
    }
    #k8s配置相关
    NAMESPACE="test-uop"
    FILEBEAT_NAME="filebeat"
    FILEBEAT_IMAGE_URL="dkreg-wj.syswin.com/base/filebeat:5.4.0"
    FILEBEAT_REQUESTS={
        "05002":{"cpu": 0.5, "memory": "20Mi"}
    }
    FILEBEAT_LIMITS={
        "101": {"cpu": 1, "memory": "100Mi"}

    }
    APP_REQUESTS={
        "11":{"cpu": 1, "memory": "1Gi"}
    }
    APP_LIMITS={
        "22":{"cpu": 2, "memory": "2Gi"}
    }
    HOSTNAMES=["uop-k8s.syswin.com"]
    IP="127.0.0.1"
    NETWORKNAME="contiv-vlan651"
    TENANTNAME="tenant-vlan651"

    K8S_NETWORK_URL={
        "dev":"http://172.28.13.254:19999/api/v1/networks/",
        "test": "http://172.28.13.254:19999/api/v1/networks/",
        "prep": "http://172.28.13.254:19999/api/v1/networks/",
        "prod": "http://172.28.13.254:19999/api/v1/networks/",
    }




configs = {
    'testing': TestingConfig,
}
