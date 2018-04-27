# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import os
import werkzeug

from flask import request
from flask_restful import reqparse, Api, Resource
from config import APP_ENV, configs
from crp import models
from crp.log import Log
from crp.disconf import disconf_blueprint
from crp.disconf.errors import disconf_errors
from crp.disconf.disconf_api import *

DISCONF_SERVER = configs[APP_ENV].DISCONF_SERVER

disconf_api = Api(disconf_blueprint, errors=disconf_errors)


class DisconfAPI(Resource):
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('filename', type=str, location='json')
        parser.add_argument('filecontent', type=str, location='json')
        parser.add_argument('res_id', type=str, location='json')
        parser.add_argument('ins_name', type=str, location='json')
        args = parser.parse_args()

        res_id = args.get("res_id")
        version = "1_0_0"
        fileName = args.get('filename')
        fileContent = args.get('filecontent')

        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
            app_name = resource.ins_name
            app_desc = '{res_name} config generated.'.format(res_name=app_name)
            disconf_api = DisconfServerApi(DISCONF_SERVER.get("host"))
            disconf_api.disconf_app(app_name, app_desc)
            app_id = disconf_api.disconf_app_id(app_name)
            env_id = disconf_api.disconf_env_id('rd')
            ret = disconf_api.disconf_filetext(app_id, env_id, version, fileContent, fileName)

            code = 200
            res = 'Disconf Success.'
            message = ret
        except ServerError as e:
            code = 500
            res = "Disconf Failed."
            message = e.args

        ret = {
            "code": code,
            "result": {
                "res": res,
                "msg": message
            }
        }
        return ret, code



    @classmethod
    def get(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('res_id', type=str, location='args')
        args = parser.parse_args()
        res_id = args.res_id
        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
            message = []
            for ins_info in resource.compute_list:
                if ins_info is not None:
                    result = {}
                    app_name = getattr(ins_info,'ins_name')
                    disconf_api = DisconfServerApi(DISCONF_SERVER.get("host"))
                    app_id = disconf_api.disconf_app_id(app_name=app_name)
                    env_id = disconf_api.disconf_env_id(env_name='rd')
                    version_id = disconf_api.disconf_version_list(app_id=app_id)
                    config_id_list = disconf_api.disconf_config_id_list(app_id=app_id, env_id=env_id, version=version_id)

                    configurations = []
                    for config_id in config_id_list:
                        config = disconf_api.disconf_config_show(config_id)
                        config_value = {}
                        if config is not None:
                            config_value['filename'] = config.get('key')
                            config_value['filecontent'] = config.get('value')
                            config_value['config_id'] = config.get('configId')
                            configurations.append(config_value)
                    result[app_name] = configurations
                    message.append(result)
            code = 200
            res = "Configurations Success."
        except ServerError as e:
            code = 500
            res = "Configurations Failed."
            message = e.args

        ret = {
            "code": code,
            "result": {
                "res": res,
                "msg": message,
            }
        }
        return ret, code


class DisconfItem(Resource):
    @classmethod
    def put(cls, res_id):
        parser = reqparse.RequestParser()
        parser.add_argument('filecontent', type=str, location='json')
        parser.add_argument('filename', type=str, location='json')
        args = parser.parse_args()
        filecontent = args.get('filecontent')
        filename = args.get('filename')
        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
        except Exception as e:
            code = 500
            res = "Failed to find the rsource. "
            ret = {
                "code": code,
                "result": {
                    "res": res + e.message,
                    "msg": ""
                }
            }
            return ret, code

        app_name = resource.resource_name
        disconf_api = DisconfServerApi(DISCONF_SERVER)
        ret, msg = disconf_api.disconf_session()
        if not ret:
            return msg, 200
        app_id, msg = disconf_api.disconf_app_id(app_name)
        if app_id is None:
            return msg, 200
        app_id = str(app_id)
        version_id, msg = disconf_api.disconf_version_list(app_id)
        if version_id is None:
            return msg, 200

        config_list, msg = disconf_api.disconf_config_list(app_id, '1', version_id)
        if config_list is None:
            return msg, 200

        find = False
        for conf in config_list:
            config, msg = disconf_api.disconf_config_show(str(conf.get('configId')))
            if config is not None:
                if filename == config.get('key'):
                    ret, msg = disconf_api.disconf_filetext_update(str(config.get('configId')), filecontent)
                    find = True
                else:
                    ret, msg = disconf_api.disconf_filetext_delete(str(config.get('configId')))
        if not find:
            ret, msg = disconf_api.disconf_filetext(app_id, '1', version_id, filecontent, filename)

        return msg, 200


class DisconfEnv(Resource):
    @classmethod
    def get(cls):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('disconf_server', type=str, location='args')
            args = parser.parse_args()
            disconf_server = args.disconf_server
            server_info = {'disconf_server_name': DISCONF_SERVER.get("host"),
                           'disconf_server_url': ":".join([DISCONF_SERVER.get("host"), DISCONF_SERVER.get("port")]),
                           'disconf_server_user': DISCONF_SERVER.get("user"),
                           'disconf_server_password': DISCONF_SERVER.get("password"),
                           }
            disconf_api = DisconfServerApi(server_info)
            env_list = disconf_api.disconf_env_list()
            code = 200
            flag = 'true'
            res = env_list
            message = 'disconf_env_list success.'
        except ServerError as e:
            code = 500
            flag = 'false'
            res = []
            message = e.args
        ret = {
            "code": code,
            "result": {
                "flag": flag,
                "data": res,
                "msg": message
            }
        }
        return ret, code



def delete_disconf(disconf_list):
    try:
        for disconf_info in disconf_list:
            disconf_server_name=disconf_info.get('disconf_server_name')
            disconf_server_url=disconf_info.get('disconf_server_url')
            disconf_server_user=disconf_info.get('disconf_server_user')
            disconf_server_password=disconf_info.get('disconf_server_password')
            app_name=disconf_info.get('ins_name')
            env_name=disconf_info.get('disconf_env')
            version=disconf_info.get('disconf_version')
            config_name=disconf_info.get('disconf_name')
            server_info={'disconf_server_name':disconf_server_name,
                         'disconf_server_url':disconf_server_url,
                         'disconf_server_user':disconf_server_user,
                         'disconf_server_password':disconf_server_password,
                        }
            if disconf_server_name and disconf_server_url and disconf_server_user and disconf_server_password:
                disconf_api = DisconfServerApi(server_info)
                app_id = disconf_api.disconf_app_id(app_name)
                env_id = disconf_api.disconf_env_id(env_name)
                config_id = disconf_api.disconf_config_id(app_id, env_id, config_name, version)
                if config_id:
                    res=disconf_api.disconf_filetext_delete(config_id)
                    status=res.get('success')
                    if status == 'true':
                        Log.logger.debug('disconf delete success app_name:%s env_name:%s version:%s config_name:%s' % (app_name,env_name,version,config_name) )

                else:
                    Log.logger.debug('disconf delete failed disconf is not exist')
            else:
                 Log.logger.debug('server_info error:disconf_server_name:%s disconf_server_url:%s  disconf_server_user:%s  disconf_server_password:%s' % ( disconf_server_name,disconf_server_url,disconf_server_user,disconf_server_password))
    except Exception as e:
        Log.logger.error(" delete disconf  error, Exception:%s" % e.args)




disconf_api.add_resource(DisconfAPI, '/')
disconf_api.add_resource(DisconfItem, '/<string:res_id>/')
disconf_api.add_resource(DisconfEnv, '/env_list/')
