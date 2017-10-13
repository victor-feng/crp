# -*- coding: utf-8 -*-
import logging

from flask_restful import reqparse, Api, Resource

# TODO: import * is bad!!!
from crp.taskmgr import *

from crp.openstack_api import openstack_blueprint
from crp.openstack_api.errors import az_errors
from crp.openstack import OpenStack
from crp.log import Log
from config import configs, APP_ENV


# 配置可用域
AVAILABILITY_ZONE_AZ_UOP = configs[APP_ENV].AVAILABILITY_ZONE_AZ_UOP

openstack_api = Api(az_blueprint, errors=az_errors)


class NovaVMAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('os_inst_ids', type=str, location='args', action='append')
        args = parser.parse_args()
        os_inst_ids = args.os_inst_ids
        try:
            nova_cli = OpenStack.nova_client
            query =  {'vm': ''}
            statistics = nova_cli.services.list(**query)
        except Exception as e:
            #Log.logger.error('get hypervisors_statistics err: %s' % e.message)
            logging.error('get vm status err: %s' % e.message)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "请求成功",
                    "res": hypervisors_statistics
                }
            }
            return res, 200

az_api.add_resource(NovaVMAPI, '/uopStatistics')
