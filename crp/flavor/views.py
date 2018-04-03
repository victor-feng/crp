# -*- coding: utf-8 -*-
import logging

from flask_restful import reqparse, Api, Resource

# TODO: import * is bad!!!
from crp.taskmgr import *
from crp.flavor import flavor_blueprint
from crp.flavor.errors import flavor_errors
from crp.openstack import OpenStack
from crp.openstack2 import OpenStack as OpenStack2
from crp.log import Log

flavor_api = Api(flavor_blueprint, errors=flavor_errors)


class FlavorAPI(Resource):

    def get(self):

        res_flavors = []
        try:
            nova_cli = OpenStack.nova_client
            flavors = nova_cli.flavors.list()
            for item in flavors:
                res_flavors.append({
                    "flavor_id": item.id,
                    "flavor_name": item.name,
                    "cpu": item.vcpus,
                    "memory": item.ram,
                    "cloud": "1"
                })
            nova_cli_2 = OpenStack2.nova_client
            flavors_2 = nova_cli_2.flavors.list()
            for item in flavors_2:
                res_flavors.append({
                    "flavor_id": item.id,
                    "flavor_name": item.name,
                    "cpu": item.vcpus,
                    "memory": item.ram,
                    "cloud": "2"
                })
        except Exception as e:
            err_msg = e.message
            #Log.logger.error('list flavor err: %s' % err_msg)
            Log.logger.error('list flavor err: %s' % err_msg)
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
                    "res": res_flavors
                }
            }
            return res, 200


flavor_api.add_resource(FlavorAPI, '/flavors')
