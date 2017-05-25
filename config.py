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
    OPENRC_PATH = "/root/openrc"
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.22'


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
    OPENRC_PATH = "/root/openrc"
    DK_SOCK_URL = 'unix://var/run/docker.sock'
    DK_CLI_VERSION = '1.22'


configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
