# -*- coding: utf-8 -*-
import requests
import os
from flask_restful import reqparse, Api, Resource
from crp.openstack_api import openstack_blueprint
from crp.openstack_api.errors import az_errors
from handler import OpenStack_Api,OpenStack2_Api
from crp.log import Log
from crp.k8s_api import K8sDeploymentApi,K8S,K8sLogApi
from config import configs, APP_ENV
from crp.utils.aio import response_data


# 配置可用域
AVAILABILITY_ZONE = configs[APP_ENV].AVAILABILITY_ZONE
OS_DOCKER_LOGS = configs[APP_ENV].OS_DOCKER_LOGS
NAMESPACE = configs[APP_ENV].NAMESPACE
K8S_NETWORK_URL=configs[APP_ENV].K8S_NETWORK_URL

openstack_api = Api(openstack_blueprint, errors=az_errors)


class NetworkAPI(Resource):

    def get(self):
        name2id = {}
        try:
            subnet_info={}
            network1s,subnet1s=OpenStack_Api.get_network_info()
            network2s, subnet2s = OpenStack2_Api.get_network_info()
            subnets=subnet1s + subnet2s
            networks=network1s + network2s
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
                for network_id in subnet_info.keys():
                    if network_id == id_:
                        sub_vlans=subnet_info[network_id]
                        name2id[name] = [id_,sub_vlans]
        except Exception as e:
            err_msg=str(e)
            Log.logger.error('get networks err: %s' % err_msg)
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": err_msg
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
        count = 0
        try:
            if network_id:
                port1s=OpenStack_Api.get_ports(network_id)
                port2s =OpenStack2_Api.get_ports(network_id)
                ports=port1s + port2s
                count = len(ports)
        except Exception as e:
            Log.logger.error('get port err: %s' % e.args)
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
        vm_state=None
        try:
            vm_state1 = OpenStack_Api.get_vm_status(os_inst_id)
            vm_state2 = OpenStack2_Api.get_vm_status(os_inst_id)
            if vm_state1:
                vm_state = vm_state1
            if vm_state2:
                vm_state = vm_state2
        except Exception as e:
            Log.logger.error('get vm status err: %s' % e.args)
            res = {
                "code": 400,
                "result": {
                    "vm_state": "failed",
                    "msg": e.args
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



class NovaVMAPIAll(Resource):

    def get(self):
        vm_info_dict = {}
        try:
            vm_info_dict1=OpenStack_Api.get_all_vm_status()
            vm_info_dict2=OpenStack2_Api.get_all_vm_status()
            vm_info_dict= dict(vm_info_dict1,**vm_info_dict2)
        except Exception as e:
            Log.logger.error('get vm status err: %s' % str(e.args))
            res = {
                "code": 400,
                "result": {
                    "msg": str(e.args),
                    "vm_info_dict":vm_info_dict
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
        parser.add_argument("cloud", type=str, location='json')
        parser.add_argument("resource_name", type=str, location='json')
        args = parser.parse_args()
        osid = args.osid
        cloud = args.cloud
        resource_name = args.resource_name
        try:
            if cloud == "2":
                K8sLog = K8sLogApi()
                deployment_name = resource_name
                logs,code=K8sLog.get_deployment_log(deployment_name,NAMESPACE)
                #logs,code=K8sLogApi.get_namespace_pod_log(osid,NAMESPACE,"app")
            else:
                #nova_cli = OpenStack.nova_client
                Log.logger.info("#####osid:{}".format(osid))
                #vm = nova_cli.servers.get(osid)
                #Log.logger.info("#####vm:{}".format(vm))
                os_log_dir = os.path.join(OS_DOCKER_LOGS, osid)
                os_log_file = os.path.join(os_log_dir, "docker_start.log")
                if os.path.exists(os_log_file):
                    with open(os_log_file,'r') as f:
                        logs = f.read().strip()
                else:
                    logs=''
        except Exception as e:
            Log.logger.error('get vm logs err: %s' % e.args)
            res = {
                "code": 400 if "not be found" in e.message else 504,
                "result": {
                    "vm_state": "failed",
                    "msg": e.args
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

class K8sDeployment(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("deployment_name", type=str)
        args = parser.parse_args()
        deployment_name = args.deployment_name
        data={}
        res_list=[]
        K8sDeployment = K8sDeploymentApi()
        try:
            if deployment_name:
                #如果传deployment_name,获取单个deployment状态
                res_list=K8sDeployment.get_deployment_info(NAMESPACE,deployment_name)
            else:
                #获取namespace下所有deployment状态
                res_list = K8sDeployment.get_namespace_deployment_info(NAMESPACE)
            data["res_list"] = res_list
            code = 200
            msg = "Get deployment info success"
        except Exception as e:
            code=500
            data = "Error"
            msg= "Get deployment info error %s" % str(e)
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code


class K8sNetwork(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("env", type=str)
        args = parser.parse_args()
        env = args.env
        data = {}
        res_list = []
        try:
            url=K8S_NETWORK_URL[env]
            res=requests.get(url)
            res_list=res.json()
            data["res_list"] = res_list
            code = 200
            msg = "Get k8s network info success"
        except Exception as e:
            code = 500
            data = "Error"
            msg = "Get k8s network info error %s" % str(e)
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code







openstack_api.add_resource(NovaVMAPIAll, '/nova/states')
openstack_api.add_resource(NovaVMAPI, '/nova/state')
openstack_api.add_resource(PortAPI, '/port/count')
openstack_api.add_resource(NetworkAPI, '/network/list')
openstack_api.add_resource(Dockerlogs, '/docker/logs/')
openstack_api.add_resource(K8sDeployment, '/k8s/deployment')
openstack_api.add_resource(K8sNetwork, '/k8s/network')