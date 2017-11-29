# -*- coding: utf-8 -*-
import logging
import os
from flask_restful import reqparse, Api, Resource
from crp.openstack_api import openstack_blueprint
from crp.openstack_api.errors import az_errors
from crp.openstack import OpenStack
from crp.log import Log
from config import configs, APP_ENV


# 配置可用域
AVAILABILITY_ZONE_AZ_UOP = configs[APP_ENV].AVAILABILITY_ZONE_AZ_UOP
OS_DOCKER_LOGS = configs[APP_ENV].OS_DOCKER_LOGS

openstack_api = Api(openstack_blueprint, errors=az_errors)


class NetworkAPI(Resource):

    def get(self):
        name2id = {}
        try:
            subnet_info={}
            net_cli = OpenStack.neutron_client
            networks = net_cli.list_networks()
            networks = networks.get('networks', '')
            subnets=net_cli.list_subnets()["subnets"]
            for subnet in subnets:
                network_id = subnet["network_id"]
                sub_vlan=subnet["cidr"]
                if network_id in subnet_info.keys():
                    subnet_info[network_id].append(sub_vlan)
                else:
                    subnet_info[network_id] = [sub_vlan]
            for network in networks:
                name = network.get('name')
                id_ = network.get('id')
                status = network.get('status')
                for network_id in subnet_info.keys():
                    if network_id == id_:
                        sub_vlans=subnet_info[network_id]
                        name2id[name] = [id_,sub_vlans]
        except Exception as e:
            logging.error('get networks err: %s' % e.args)
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
                    "res": name2id
                }
            }
            return res, 200

class PortAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('network_id', type=str)
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
            logging.error('get port err: %s' % e.message)
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
        parser.add_argument('os_inst_id', type=str)
        args = parser.parse_args()
        os_inst_id = args.os_inst_id
        try:
            nova_cli = OpenStack.nova_client
            vm = nova_cli.servers.get(os_inst_id)
            logging.info("#####vm:{}".format(vm))
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


class NovaVMAPIs(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('os_inst_ids', type=list, location='json')
        args = parser.parse_args()
        os_inst_ids = args.os_inst_ids
        os_inst_status_dic = {}
        try:
            nova_cli = OpenStack.nova_client
            for os_inst_id in os_inst_ids:
                try:
                    vm = nova_cli.servers.get(os_inst_id)
                    vm_state = getattr(vm, 'OS-EXT-STS:vm_state')
                except Exception as e:
                    vm_state = "failed"
                os_inst_status_dic[os_inst_id] = vm_state
        except Exception as e:
            logging.error('get vm status err: %s' % e.args)
            res = {
                "code": 400,
                "result": {
                    "os_inst_status": {},
                    "msg": e.args,
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "success",
                    "os_inst_status_dic": os_inst_status_dic,
                }
            }
            return res, 200

class NovaVMAPIAll(Resource):

    def get(self):
        try:
            vm_info_dict={}
            nova_cli = OpenStack.nova_client
            vms = nova_cli.servers.list()
            for vm in vms:
                os_inst_id=vm.id
                ips = vm.networks
                if ips:
                    ip = vm.networks.values()[0][0]
                else:
                    ip = "127.0.0.1"
                status=vm.status.lower()
                vm_info_dict[os_inst_id]=[ip,status]
            print len(vm_info_dict)
        except Exception as e:
            logging.error('get vm status err: %s' % e.args)
            res = {
                "code": 400,
                "result": {
                    "msg": e.args,
                    "vm_info_dict":{}
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "msg": "success",
                    "vm_info_dict":vm_info_dict
                }
            }
            return res, 200

class Dockerlogs(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("osid", type=str, location='json')
        args = parser.parse_args()
        osid = args.osid
        try:
            #nova_cli = OpenStack.nova_client
            logging.info("#####osid:{}".format(osid))
            #vm = nova_cli.servers.get(osid)
            #logging.info("#####vm:{}".format(vm))
            os_log_dir = os.path.join(OS_DOCKER_LOGS, osid)
            os_log_file = os.path.join(os_log_dir, "docker_start.log")
            if os.path.exists(os_log_file):
                with open(os_log_file,'r') as f:
                    logs = f.read().strip()
            else:
                logs=''
        except Exception as e:
            logging.error('get vm logs err: %s' % e.message)
            res = {
                "code": 400 if "not be found" in e.message else 504,
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
                    "logs": logs
                }
            }
            return res, 200


openstack_api.add_resource(NovaVMAPIAll, '/nova/states')
openstack_api.add_resource(NovaVMAPI, '/nova/state')
openstack_api.add_resource(PortAPI, '/port/count')
openstack_api.add_resource(NetworkAPI, '/network/list')
openstack_api.add_resource(Dockerlogs, '/docker/logs/')