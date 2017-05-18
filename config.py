# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


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


class TestingConfig(BaseConfig):
    TESTING = True
    MONGODB_SETTINGS = {
        'db': 'crp',
        'host': 'test.mongodb.db',
        'port': 27017,
        'username': 'crp',
        'password': 'crp',
    }


configs = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
