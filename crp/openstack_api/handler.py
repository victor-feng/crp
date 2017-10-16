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

openstack_api = Api(openstack_blueprint, errors=az_errors)

class PortAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('network_id', type=str, location='args')
        args = parser.parse_args()
        network_id = args.network_id
        os_inst_id2state = {}
        count = 0
        try:
            net_cli = OpenStack.neutron_client
            if network_id:
                ports = net_cli.list_ports(**{'network_id':network_id})
                ports = ports.get('ports')
                count = len(ports)
        except Exception as e:
            #Log.logger.error('get hypervisors_statistics err: %s' % e.message)
            logging.error('get networks err: %s' % e.message)
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
                    "res": count
                }
            }
            return res, 200


class NovaVMAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('os_inst_id', type=str, location='json')
        args = parser.parse_args()
        os_inst_id = args.os_inst_id
        try:
            nova_cli = OpenStack.nova_client
            vm = nova_cli.servers.get(os_inst_id)
            vm_state = getattr(vm, 'OS-EXT-STS:vm_state')
        except Exception as e:
            logging.error('get vm status err: %s' % e.message)
            res = {
                "code": 400,
                "result": {
                    "vm_state": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "success",
                    "vm_state": vm_state
                }
            }
            return res, 200

openstack_api.add_resource(NovaVMAPI, '/nova/state')
openstack_api.add_resource(PortAPI, '/port/count')
