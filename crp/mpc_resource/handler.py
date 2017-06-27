# -*- coding: utf-8 -*-
import json

from flask_restful import reqparse, Api, Resource

from crp.taskmgr import *
from crp.mpc_resource import mpc_resource_blueprint
from crp.mpc_resource.errors import mpc_resource_errors
from crp.log import Log
from crp.openstack import OpenStack

from config import APP_ENV, configs

AP_NETWORK_CONF = configs[APP_ENV].AP_NETWORK_CONF
MPC_URL = configs[APP_ENV].MPC_URL

mpc_resource_api = Api(mpc_resource_blueprint, errors=mpc_resource_errors)


TIMEOUT = 600
SLEEP_TIME = 3

CREATE_VM = 0
QUERY_VM = 1
CREATE_VOLUME = 2
QUERY_VOLUME = 3
ATTACH_VOLUME = 4


# res_callback
MPC_RES_CALLBACK_URL = MPC_URL+'/api/mpc_resource/mpc_resources_callback'


# 向OpenStack申请资源
def _create_instance(task_id, name, image, flavor, availability_zone, network_id):
    nova_client = OpenStack.nova_client

    nics_list = []
    nic_info = {'net-id': network_id}
    nics_list.append(nic_info)
    int = nova_client.servers.create(name, image, flavor,
                                     availability_zone=availability_zone,
                                     nics=nics_list)
    Log.logger.debug("Task ID " + str(task_id) + " create instance:")
    Log.logger.debug(int)
    Log.logger.debug(int.id)

    return int.id


# 查询AZ，并创建
def _create_instance_by_az(task_id, result, resource):
    mpc_inst_id = resource.get('mpc_inst_id', '')
    vm_name = resource.get('vm_name', '')
    az = resource.get('az', '')
    image = resource.get('image', '')
    flavor = resource.get('flavor', '')
    # volume = resource.get('volume', 0)
    network_id = AP_NETWORK_CONF.get(az, None)

    result['current_status'] = QUERY_VM
    result['vm'] = {
        'mpc_inst_id': mpc_inst_id,
    }

    if not network_id:
        err_msg = 'not found network_id by AZ %s' % az
        Log.logger.error(
            "Task ID %s, %s"
            % (task_id, err_msg))
        result['vm']['status'] = 'error'
        result['vm']['err_msg'] = err_msg
        request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)
    else:
        os_inst_id = _create_instance(task_id, vm_name, image, flavor, az, network_id)
        result['vm']['os_inst_id'] = os_inst_id


def _get_ip_from_instance(server):
    ips_address = []
    for _, ips in server.addresses.items():
        for ip in ips:
            if isinstance(ip, dict):
                if ip.has_key('addr'):
                    ip_address = ip['addr']
                    ips_address.append(ip_address)
    return ips_address


# 向OpenStack查询已申请资源
def _query_instance_status(task_id, result):
    vm = result.get('vm', {})
    os_inst_id = vm.get('os_inst_id', '')
    nova_client = OpenStack.nova_client
    inst = nova_client.servers.get(os_inst_id)
    Log.logger.debug(
        "Query Task ID " + str(task_id) +
        " query Instance ID " + os_inst_id +
        " Status is " + inst.status)
    if inst.status == 'ACTIVE':
        result['current_status'] = CREATE_VOLUME
        result['vm']['status'] = 'running'
        result['vm']['physical_server'] = getattr(
            inst, 'OS-EXT-SRV-ATTR:host', '')
        _ips = _get_ip_from_instance(inst)
        result['vm']['ip'] = _ips.pop() if len(_ips) >= 1 else ''
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " Instance Info: " + str(result['vm']))
        request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)
    elif inst.status == 'ERROR':
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " ERROR Instance Info: " + str(inst.to_dict()))
        result['vm']['status'] = 'error'
        request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)


# request MPC res_callback
def request_res_callback(task_id, result):
    vm = result.get('vm', {})
    data = {
        'mpc_inst_id': vm.get('mpc_inst_id', ''),
        'os_inst_id': vm.get('os_inst_id', ''),
        'ip': vm.get('ip', ''),
        'host_name': vm.get('physical_server', ''),
        'status': vm.get('status', ''),
        'err_msg': vm.get('err_msg', ''),
    }
    err_msg = None
    cbk_result = None
    try:
        data_str = json.dumps(data)
        url = MPC_RES_CALLBACK_URL
        headers = {'Content-Type': 'application/json'}
        Log.logger.debug(
            "Query Task ID " + str(task_id) + '\r\n' +
            url + ' ' + json.dumps(headers) + ' ' + data_str)
        cbk_result = requests.post(url=url, headers=headers, data=data_str)
        cbk_result = json.dumps(cbk_result.json())
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message
    finally:
        Log.logger.debug(
            "Query Task ID " + str(task_id) + '\r\n' +
            'mpc_res_callback result ' + str(cbk_result))
        if err_msg:
            Log.logger.debug(
                "Query Task ID " + str(task_id) + '\r\n' +
                'mpc_res_callback err_msg ' + str(err_msg))


# 申请资源
# 1. 创建虚机
# 2. 创建volume【暂未实现】
# 3. 挂载volume到虚机【暂未实现】
def _create_resource_set_and_query(task_id, result, resource):
    current_status = result.get('current_status', None)
    Log.logger.debug(
        "Task ID %s, current_status %s" %
        (task_id, current_status))
    Log.logger.debug(
        "Task ID %s,\r\n result %s,\r\n resource %s ." %
        (task_id, result, resource))

    try:
        if current_status == CREATE_VM:
            _create_instance_by_az(task_id, result, resource)
        elif current_status == QUERY_VM:
            _query_instance_status(task_id, result)
        # elif current_status == CREATE_VOLUME:
        #     result['current_status'] = QUERY_VOLUME
        # elif current_status == QUERY_VOLUME:
        #     result['current_status'] = ATTACH_VOLUME
        # elif current_status == ATTACH_VOLUME:
        #     TaskManager.task_exit(task_id)
    except Exception as e:
        err_msg = e.message
        Log.logger.error(err_msg)
        result['vm']['status'] = 'error'
        result['vm']['err_msg'] = err_msg
        request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)


# res_set REST API Controller
class ResourceAPI(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('resources', type=list,
                            required=True, location='json',
                            help="Resources cannot be blank!")
        args = parser.parse_args()
        Log.logger.debug(args.resources)
        try:
            for item in args.resources:
                TaskManager.task_start(
                    SLEEP_TIME, TIMEOUT, {'current_status': CREATE_VM},
                    _create_resource_set_and_query, item)
        except Exception as e:
            err_msg = e.message
            Log.logger.error('err: %s' % err_msg)
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
                    "msg": "提交成功",
                }
            }
            return res, 200


mpc_resource_api.add_resource(ResourceAPI, '/resource')
