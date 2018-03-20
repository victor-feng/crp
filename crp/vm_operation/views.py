# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource
from flask import request
from crp.vm_operation import vm_operation_blueprint
from crp.vm_operation.errors import vm_operation_errors
from crp.log import Log
from crp.openstack import OpenStack
from crp.openstack2 import OpenStack as OpenStack2
from crp.k8s_api import K8sDeploymentApi,K8S
from config import configs, APP_ENV


vm_operation_api = Api(vm_operation_blueprint, errors=vm_operation_errors)
NAMESPACE = configs[APP_ENV].NAMESPACE

OpenStack_info={
    "1":OpenStack,
    "2":OpenStack2
}

class VMOperation(Resource):
    def post(self):
        code = 200
        parser = reqparse.RequestParser()
        parser.add_argument('vm_uuid', type=str)
        parser.add_argument('operation', type=str)
        parser.add_argument('reboot_type', type=str)
        parser.add_argument('cloud', type=str)
        parser.add_argument('resource_name', type=str)
        parser.add_argument('resource_type', type=str)
        parser.add_argument('namespace', type=str)
        args = parser.parse_args()
        Log.logger.debug("vm operation receive restart request. args is " + str(args))
        if args.cloud == "2":
            cloud = "2"
        else:
            cloud = "1"
        if  not args.operation:
            code = 500
            ret = {
                "code": code,
                "result": {
                    "msg": "vm operation receive invalid request",
                }
            }
            return ret, code
        try:
            if cloud == "2" and args.resource_type == "app":
                #k8s目前只支持应用重启功能
                namespace = args.namespace if args.namespace else NAMESPACE
                K8sDeployment = K8sDeploymentApi()
                if args.operation == "restart":
                    deployment_name = args.resource_name
                    restart_deployment = K8sDeployment.restart_deployment_pod_object(deployment_name)
                    msg,code = K8sDeployment.restart_deployment_pod(
                        restart_deployment, deployment_name, namespace)
                    if msg is not None:
                        ret = {
                            "code": code,
                            "result": {
                                "msg": msg,
                            }
                        }
                        return ret, code
            else:
                nova_client = OpenStack_info[cloud].nova_client
                if args.operation == "restart":
                    reboot_type = args.reboot_type if args.reboot_type else "SOFT"
                    inst = nova_client.servers.reboot(args.vm_uuid,reboot_type=reboot_type)
                elif args.operation == "stop":
                    inst = nova_client.servers.stop(args.vm_uuid)
                elif args.operation == "start":
                    inst = nova_client.servers.start(args.vm_uuid)
                else:
                    code = 500
                    ret = {
                        "code": code,
                        "result": {
                            "msg": "vm operation receive invalid operation",
                        }
                    }
                    return ret, code
        except Exception as e:
            code = 500
            msg=str(e)
            ret = {
                "code": code,
                "result": {
                    "msg": msg,
                }
            }
            return ret,code
        ret = {
            "code": code,
            "result": {
                "msg": "ok",
            }
        }
        return ret,code



class VMStartOrStop(VMOperation):
    def post(self):
        res = super(VMStartOrStop, self).post()
        appinfo = request.json.get('appinfo')
        ip = request.json.get('ip')
        operation = request.json.get('operation')

        # if operation == 'start':
        #     method = open_nginx_conf
        # else:
        #     method = closed_nginx_conf
        #
        # if res[0].get('code') == 200:
        #     result = method(appinfo, ip)
        #     if  result[0] == -1:
        #         res[0]['code'] = 500
        #         res[0]['result']['msg'] = result[1]

        return res




vm_operation_api.add_resource(VMOperation, '/operations')
vm_operation_api.add_resource(VMStartOrStop, '/startorstop')
