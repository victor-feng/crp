# -*- coding: utf-8 -*-
from flask_restful import reqparse, Api, Resource
from crp.vm_operation import vm_operation_blueprint
from crp.vm_operation.errors import vm_operation_errors
from crp.log import Log
from crp.openstack import OpenStack
vm_operation_api = Api(vm_operation_blueprint, errors=vm_operation_errors)

class VMOperation(Resource):
    def post(self):
        code = 200
        msg = "ok"
        parser = reqparse.RequestParser()
        parser.add_argument('vm_uuid', type=str)
        parser.add_argument('operation', type=str)
        parser.add_argument('reboot_type', type=str)
        args = parser.parse_args()
        Log.logger.debug("vm operation receive restart request. args is " + str(args))
        if not args.get("vm_uuid") or not args.get("operation"):
            return self._response_msg(500, "vm operation receive invalid request"), 500
        inst = None
        try:
            nova_client = OpenStack.nova_client
            if args.get("operation") == "restart":
                reboot_type = args.get("reboot_type") if args.get("reboot_type") else "SOFT"
                inst = nova_client.servers.reboot(args.get("vm_uuid"),reboot_type=reboot_type)
            elif args.get("operation") == "stop":
                inst = nova_client.servers.stop(args.get("vm_uuid"))
            elif args.get("operation") == "delete":
                inst = nova_client.servers.delete(args.get("vm_uuid"))
            elif args.get("operation") == "start":
                inst = nova_client.servers.start(args.get("vm_uuid"))
            else:
                return self._response_msg(500, "vm operation receive invalid operation: " + str(args.get("operation"))), 500
        except Exception as e:
            code = 500
            msg = e.message
            Log.logger.error("vm operation receive exception. message is " + msg + " vm_uuid: " + args.get("vm_uuid"))

        return self._response_msg(code,msg), code

    def _response_msg(self, code, msg=None):
        res = {
            "code": code,
            "result": {
                "msg": str(msg)
            }
        }
        return res
vm_operation_api.add_resource(VMOperation, '/operations')
