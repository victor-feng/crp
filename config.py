# -*- coding: utf-8 -*-
import os

APP_ENV = "default"
# APP_ENV = "testing"


class BaseConfig:
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    MONGODB_SETTINGS = {
        'db': 'crp',
        'host': 'develop.mongodb.db',
        'port': 27017,
        'username': 'crp',
        'password': 'crp'
    }
    UOP_URL = "http://develop.mongodb.db:5000/"
    MPC_URL = "http://mpc-test.syswin.com/"
    OPENRC_PATH = "/root/openrc"
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.22'
    DK_TAR_PATH = '/home/dk/'
    GLANCE_RESERVATION_QUANTITY = 3
    UPLOAD_FOLDER = '/tmp/'
    AP_NETWORK_CONF = {
        'AZ_UOP': '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
    }


class TestingConfig(BaseConfig):
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
    MPC_URL = "http://mpc-test.syswin.com/"
    OPENRC_PATH = "/root/openrc"
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.22'
    DK_TAR_PATH = '/home/dk/'
    GLANCE_RESERVATION_QUANTITY = 3
    UPLOAD_FOLDER = '/tmp/'
    AP_NETWORK_CONF = {
        'AZ_UOP': '7aca50a9-cf4b-4cc7-b078-be055dd7c6af'
    }


configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
