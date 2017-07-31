# -*- coding: utf-8 -*-

import os

# APP_ENV = "default"
APP_ENV = "testing"


class BaseConfig:
    DEBUG = False


# NOTE: no used. remove it later.
#class DevelopmentConfig(BaseConfig):
#    DEBUG = True
#    MONGODB_SETTINGS = {
#        'db': 'crp',
#        'host': 'develop.mongodb.db',
#        'port': 27017,
#        'username': 'crp',
#        'password': 'crp'
#    }
#    UOP_URL = "http://develop.mongodb.db:5000/"
#    MPC_URL = "http://mpc-dev.syswin.com/"
#    OPENRC_PATH = "/root/openrc"
#    DK_SOCK_URL = 'unix://var/run/docker.sock'
#    DK_CLI_VERSION = '1.22'
#    DK_TAR_PATH = '/home/dk/'
#    GLANCE_RESERVATION_QUANTITY = 3
#    UPLOAD_FOLDER = '/tmp/'
#    AP_NETWORK_CONF = {
#        'AZ_UOP': '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
#    }
#

class DevelopmentConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    MONGODB_SETTINGS = {
        'db': 'crp',
        'host': 'test.mongodb.db',
        'port': 27017,
        'username': 'crp',
        'password': 'crp',
    }
    UOP_URL = "http://172.28.20.124:5000/"
    MPC_URL = "http://mpc-dev.syswin.com/"
    OPENRC_PATH = "/root/openrc"
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.22'
    DK_TAR_PATH = '/home/dk/'
    GLANCE_RESERVATION_QUANTITY = 3
    UPLOAD_FOLDER = '/tmp/'
    AP_NETWORK_CONF = {
        'AZ_UOP': '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
    }
    nginx_ip = '172.28.20.98'
    MONGODB_SCRIPT_PATH = 'uop-crp/crp/res_set/mongo_script/'

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    #MONGODB_SETTINGS = {
    #    'db': 'crp',
    #    'host': 'test.mongodb.db',
    #    'port': 27017,
    #    'username': 'crp',
    #    'password': 'crp',
    #}
    # TODO: test.mongodb.db??
    MONGODB_SETTINGS = [
             {
            'db': 'crp',
            'host': 'mongo-1',
            'port': 28010,
            'username': 'crp',
            'password': 'crp',
            },
             {
            'db': 'crp',
            'host': 'mongo-2',
            'port': 28010,
            'username': 'crp',
            'password': 'crp',
            },
            {
            'db': 'crp',
            'host': 'mongo-3',
            'port': 28010,
            'username': 'crp',
            'password': 'crp',
            }
    ]

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
    UPLOAD_FOLDER = '/tmp/'
    #NOTE: noused in uop
    #NOTE: config it !!!! TODO:
    #TODO:? hard code?
    AP_NETWORK_CONF = {
        'AZ_UOP': '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
    }
    nginx_ip = '172.28.20.98'
    MONGODB_SCRIPT_PATH = 'uop-crp/crp/res_set/mongo_script/'


configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

