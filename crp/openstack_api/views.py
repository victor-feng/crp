# -*- coding: utf-8 -*-
import requests
import os
from flask_restful import reqparse, Api, Resource
from crp.openstack_api import openstack_blueprint
from crp.openstack_api.errors import az_errors
from handler import OpenStack_Api,OpenStack2_Api
from crp.log import Log
from crp.k8s_api import K8sDeploymentApi,K8sLogApi,K8sNamespaceApi,K8sConfigMapApi
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
            name2id1s = OpenStack_Api.get_network_info()
            name2id2s = OpenStack2_Api.get_network_info()
            name2id = dict(name2id1s,**name2id2s)
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
        parser = reqparse.RequestParser()
        parser.add_argument("namespace", type=str)
        args = parser.parse_args()
        namespace = args.namespace if args.namespace else NAMESPACE
        vm_info_dict = {}
        try:
            K8sDeployment = K8sDeploymentApi()
            vm_info_dict1=OpenStack_Api.get_all_vm_status()
            vm_info_dict2=OpenStack2_Api.get_all_vm_status()
            k8s_info_dict=K8sDeployment.get_namespace_pod_list_info(namespace)[0]
            vm_info_dict= dict(vm_info_dict1,**vm_info_dict2)
            vm_info_dict = dict(vm_info_dict, **k8s_info_dict)
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
        parser.add_argument("namespace", type=str)
        args = parser.parse_args()
        osid = args.osid
        cloud = args.cloud
        resource_name = args.resource_name
        namespace = args.namespace if args.namespace else NAMESPACE
        try:
            if cloud == "2":
                K8sLog = K8sLogApi()
                deployment_name = resource_name
                #logs,code=K8sLog.get_deployment_log(deployment_name,namespace)
                pod_name = osid
                container = "app"
                logs, code = K8sLog.get_namespace_pod_log(pod_name,namespace,container)
            else:
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
        parser.add_argument("namespace", type=str)
        args = parser.parse_args()
        deployment_name = args.deployment_name
        namespace = args.namespace if args.namespace else NAMESPACE
        data={}
        res_list=[]
        K8sDeployment = K8sDeploymentApi()
        try:
            if deployment_name:
                #如果传deployment_name,获取单个deployment状态
                res_list=K8sDeployment.get_deployment_info(namespace,deployment_name)
            else:
                #获取namespace下所有deployment状态
                res_list = K8sDeployment.get_namespace_deployment_info(namespace)
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


class K8sNamespace(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('namespace_name', type=str, location="json")
        parser.add_argument('config_map_name', type=str, location="json")
        parser.add_argument('config_map_data', type=dict, location="json")
        args = parser.parse_args()
        namespace_name = args.namespace_name
        config_map_name = args.config_map_name
        config_map_data = args.config_map_data
        try:
            K8sNamespace = K8sNamespaceApi()
            K8sConfigMap = K8sConfigMapApi()
            if namespace_name:
                namespace = K8sNamespace.create_namespace_object(namespace_name)
                err_msg,code=K8sNamespace.create_namespace(namespace)
                if not err_msg and config_map_name:
                    config_map = K8sConfigMap.create_config_map_object(config_map_name,namespace_name,config_map_data)
                    err_msg,code = K8sConfigMap.create_config_map(config_map,namespace_name)
            if code == 200:
                data = "success"
                msg = "create namespace or config map success"
                code = code
            else:
                data = "Error"
                code = code
                msg = err_msg
        except Exception as e:
            code = 500
            data = "Error"
            msg = "create namespace or config map error {e}".format(e=str(e))
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

    def get(self):
        data = {}
        res_list=[]
        try:
            K8sNamespace = K8sNamespaceApi()
            K8sConfigMap = K8sConfigMapApi()
            namespace_list,err_msg,code= K8sNamespace.list_namespace()
            if code == 200:
                for namespace_name in namespace_list:
                    config_map_list,err_msg,code = K8sConfigMap.list_namespace_config_map(namespace_name)
                    if config_map_list:
                        for config_map_name in config_map_list:
                            namespace_config_dict = {}
                            namespace_config_dict["namespace_name"] = namespace_name
                            namespace_config_dict["config_map_name"] = config_map_name
                            res_list.append(namespace_config_dict)
                    else:
                        namespace_config_dict = {}
                        namespace_config_dict["namespace_name"] = namespace_name
                        namespace_config_dict["config_map_name"] = ""
                        res_list.append(namespace_config_dict)
            if code == 200:
                data["res_list"] = res_list
                code = code
                msg = "success"
            else:
                data = "Error"
                code = code
                msg = err_msg
        except Exception as e:
            code = 500
            data = "Error"
            msg = "create namespace or config map error {e}".format(e=str(e))
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

class K8sDeploymentPod(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("deployment_name", type=str)
        parser.add_argument("namespace", type=str)
        args = parser.parse_args()
        deployment_name = args.deployment_name
        namespace = args.namespace if args.namespace else NAMESPACE
        data={}
        res_list=[]
        K8sDeployment = K8sDeploymentApi()
        try:
            if deployment_name:
                res_list=K8sDeployment.get_deployment_pod_info(namespace, deployment_name)
            else:
                res_list,msg,code=K8sDeployment.list_namespace_all_pod_info(namespace)
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



openstack_api.add_resource(NovaVMAPIAll, '/nova/states')
openstack_api.add_resource(NovaVMAPI, '/nova/state')
openstack_api.add_resource(PortAPI, '/port/count')
openstack_api.add_resource(NetworkAPI, '/network/list')
openstack_api.add_resource(Dockerlogs, '/docker/logs/')
openstack_api.add_resource(K8sDeployment, '/k8s/deployment')
openstack_api.add_resource(K8sNetwork, '/k8s/network')
openstack_api.add_resource(K8sNamespace, '/k8s/namespace')
openstack_api.add_resource(K8sDeploymentPod, '/k8s/deploymentpod')