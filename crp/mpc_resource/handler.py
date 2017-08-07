# -*- coding: utf-8 -*-

import logging
import json
import requests

from flask_restful import reqparse, Api, Resource
from flask import current_app

# TODO: import* is bad!
from crp.taskmgr import *
from crp.mpc_resource import mpc_resource_blueprint
from crp.mpc_resource import mpc_resource_callback
from crp.mpc_resource.errors import mpc_resource_errors
from crp.log import Log
from crp.openstack import OpenStack

from config import APP_ENV, configs

AP_NETWORK_CONF = configs[APP_ENV].AP_NETWORK_CONF

mpc_resource_api = Api(mpc_resource_blueprint, errors=mpc_resource_errors)

# TODO: move to global conf
TIMEOUT = 600
SLEEP_TIME = 3

CREATE_VM = 0
QUERY_VM = 1
CREATE_VOLUME = 2
QUERY_VOLUME = 3
ATTACH_VOLUME = 4
QUERY_ATTACH = 5


# 向OpenStack申请资源
def _create_instance(task_id, name, image, flavor, availability_zone, network_id):
    nova_client = OpenStack.nova_client

    nics_list = []
    nic_info = {'net-id': network_id}
    nics_list.append(nic_info)
    inst = nova_client.servers.create(name, image, flavor,
                                     availability_zone=availability_zone,
                                     nics=nics_list)
    logging.debug("Task ID " + str(task_id) + " create instance:")

    return inst


# 查询AZ，并创建
def _create_instance_by_az(task_id, result, resource):
    mpc_inst_id = resource.get('mpc_inst_id', '')
    vm_name = resource.get('vm_name', '')
    az = resource.get('az', '')
    image = resource.get('image', '')
    flavor = resource.get('flavor', '')
    # volume = resource.get('volume', 0)

    #AP_NETWORK_CONF = current_app.config['AP_NETWORK_CONF']
    network_id = AP_NETWORK_CONF.get(az, None)

    result['vm'] = {
        'mpc_inst_id': mpc_inst_id,
        'vm_name': vm_name
    }

    if not network_id:
        err_msg = 'not found network_id by AZ %s' % az
        #Log.logger.error(
        logging.error(
            "Task ID %s, %s"
            % (task_id, err_msg))
        result['vm']['status'] = 'vm_error'
        result['vm']['err_msg'] = err_msg
        request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)
    else:
        inst = _create_instance(task_id, vm_name, image, flavor, az, network_id)
        result['current_status'] = QUERY_VM
        result['vm']['os_inst_id'] = inst.id
        result['vm']['status'] = inst.status
        request_res_callback(task_id, result)


def _get_ip_from_instance(server):
    ips_address = []
    for _, ips in server.addresses.items():
        for ip in ips:
            if isinstance(ip, dict):
                if ip.has_key('addr'):
                    ip_address = ip['addr']
                    ips_address.append(ip_address)
    return ips_address


# 向OpenStack查询vm状态
def _query_instance_status(task_id, result, resource):
    vm = result.get('vm', {})
    os_inst_id = vm.get('os_inst_id', '')
    nova_client = OpenStack.nova_client
    inst = nova_client.servers.get(os_inst_id)
    #Log.logger.debug(
    logging.debug(
        "Query Task ID " + str(task_id) +
        " query Instance ID " + os_inst_id +
        " Status is " + inst.status)
    if inst.status == 'ACTIVE':
        result['vm']['status'] = inst.status
        result['vm']['physical_server'] = getattr(
            inst, 'OS-EXT-SRV-ATTR:host', '')
        _ips = _get_ip_from_instance(inst)
        result['vm']['ip'] = _ips.pop() if len(_ips) >= 1 else ''
        #Log.logger.debug(
        logging.debug(
            "Query Task ID " + str(task_id) +
            " Instance Info: " + str(result['vm']))

        size = resource.get('volume', 0)
        if size > 0:
            result['current_status'] = CREATE_VOLUME
        else:
            request_res_callback(task_id, result)
            TaskManager.task_exit(task_id)
    elif inst.status == 'ERROR':
        #Log.logger.debug(
        logging.debug(
            "Query Task ID " + str(task_id) +
            " ERROR Instance Info: " + str(inst.to_dict()))
        result['vm']['status'] = 'vm_error'
        request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)


def _create_volume(task_id, result, resource):
    result['current_status'] = QUERY_VOLUME
    vm = result.get('vm', {})
    data_dict = {
        "volume": {
            # "status": "creating",
            # "availability_zone": "nova",
            # "source_volid": None,
            # "display_description": None,
            # "snapshot_id": None,
            # "user_id": None,
            "size": resource.get('volume', 0),
            "display_name": "%s-vol" % vm.get('vm_name', ''),
            # "display_name": "mpc-vol",
            # "imageRef": None,
            # "attach_status": "detached",
            # "volume_type": None,
            # "project_id": None,
            # "metadata": {},
            "lvm_instance_id": vm.get('os_inst_id', '')
            # "lvm_instance_id": '3f778431-fb41-4f8e-8e60-097ee2773314'
        }
    }
    cv_result = None
    err_msg = None
    try:
        cinder_endpoint, token = OpenStack.get_cinder_endpoint_and_token()
        url = cinder_endpoint + '/volumes'
        headers = {
            'User-Agent': 'python-cinderclient',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Auth-Token': token,
        }
        data_str = json.dumps(data_dict)
        #Log.logger.debug(
        logging.debug(
            "CreateVolume Task ID " + str(task_id) + '\r\n' +
            url + ' ' + json.dumps(headers) + ' ' + data_str)
        cv_result = requests.post(
            url=url, headers=headers, data=data_str)
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message
    finally:
        #Log.logger.debug(
        logging.debug(
            "CreateVolume Task ID " + str(task_id) + '\r\n' +
            'create_volume result ' + str(cv_result.json()))
        if err_msg:
            #Log.logger.debug(
            logging.debug(
                "CreateVolume Task ID " + str(task_id) + '\r\n' +
                'create_volume err_msg ' + str(err_msg))
            result['vm']['status'] = 'vol_error'
            result['vm']['err_msg'] = err_msg
            request_res_callback(task_id, result)
            TaskManager.task_exit(task_id)
        else:
            cv_result_dict = cv_result.json()
            volume = cv_result_dict.get('volume', {})
            result['volume'] = {
                'id': volume.get('id', ''),
                'display_name': volume.get('display_name', ''),
            }


# 向OpenStack查询volume状态
def _query_volume_status(task_id, result, for_create=True):
    volume = result.get('volume', {})
    vol_id = volume.get('id', '')
    cinder_client = OpenStack.cinder_client
    vol = cinder_client.volumes.get(vol_id)
    #Log.logger.debug(
    logging.debug(
        "QueryVolume Task ID " + str(task_id) +
        "\r\nVolume status: " + vol.status)
    if for_create and vol.status == 'available':
        result['current_status'] = ATTACH_VOLUME
        result['volume']['status'] = 'available'
        #Log.logger.debug(
        logging.debug(
            "QueryVolume Task ID " + str(task_id) +
            " volume Info: " + str(result['volume']))
    elif not for_create and vol.status == 'in-use':
        result['volume']['status'] = 'in-use'
        #Log.logger.debug(
        logging.debug(
            "QueryVolume Task ID " + str(task_id) +
            " volume Info: " + str(result['volume']))
        request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)
    elif vol.status == 'error':
        #Log.logger.debug(
        logging.debug(
            "QueryVolume Task ID " + str(task_id) +
            " ERROR volume Info: " + str(vol))
        result['vm']['status'] = 'vol_error'
        result['volume']['status'] = 'error'
        request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)


def _instance_attach_volume(task_id, result):
    result['current_status'] = QUERY_ATTACH
    vm = result.get('vm', {})
    os_inst_id = vm.get('os_inst_id', '')
    volume = result.get('volume', {})
    os_vol_id = volume.get('id', '')
    nova_client = OpenStack.nova_client
    vol_attach_result = nova_client.volumes.create_server_volume(
        os_inst_id, os_vol_id, None)
    #Log.logger.debug(
    logging.debug(
        "AttachVolume Task ID " + str(task_id) +
        "\r\nvolume ID " + os_vol_id +
        "\r\ninstance ID " + os_inst_id +
        "\r\nresult: " + str(vol_attach_result.to_dict())
    )


# request MPC res_callback
def request_res_callback(task_id, result):
    vm = result.get('vm', {})
    vol = result.get('volume', {})
    vms = [
        {
            'mpc_inst_id': vm.get('mpc_inst_id', ''),
            'os_inst_id': vm.get('os_inst_id', ''),
            'ip': vm.get('ip', ''),
            'host_name': vm.get('physical_server', ''),
            'status': vm.get('status', ''),
            'err_msg': vm.get('err_msg', ''),
            'vol_id': vol.get('id', ''),
        }
    ]
    err_msg = None
    cbk_result = None
    try:
        cbk_result = mpc_resource_callback(vms)
        cbk_result = json.dumps(cbk_result.json())
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message
    finally:
        #Log.logger.debug(
        logging.debug(
            "Callback Task ID " + str(task_id) + '\r\n' +
            'mpc_res_callback result ' + str(cbk_result))
        if err_msg:
            #Log.logger.debug(
            logging.debug(
                "Callback Task ID " + str(task_id) + '\r\n' +
                'mpc_res_callback err_msg ' + str(err_msg))


# 申请资源
# 1. 创建虚机
# 2. 创建volume
# 3. 挂载volume到虚机
def _create_resource_set_and_query(task_id, result, resource):
    current_status = result.get('current_status', None)
    #Log.logger.debug(
    logging.debug(
        "Task ID %s, current_status %s" %
        (task_id, current_status))
    #Log.logger.debug(
    logging.debug(
        "Task ID %s,\r\n result %s,\r\n resource %s ." %
        (task_id, result, resource))

    try:
        # _create_volume(task_id, result, resource)
        # TaskManager.task_exit(task_id)
        if current_status == CREATE_VM:
            _create_instance_by_az(task_id, result, resource)
        elif current_status == QUERY_VM:
            _query_instance_status(task_id, result, resource)
        elif current_status == CREATE_VOLUME:
            _create_volume(task_id, result, resource)
        elif current_status == QUERY_VOLUME:
            _query_volume_status(task_id, result)
        elif current_status == ATTACH_VOLUME:
            _instance_attach_volume(task_id, result)
        elif current_status == QUERY_ATTACH:
            _query_volume_status(task_id, result, for_create=False)
    except Exception as e:
        err_msg = e.message
        logging.exception("[CRP] _create_resource_set_and_query failed, Exception:%s", e.args)
        #Log.logger.error(err_msg)
        if not result.get('vm', {}):
            result['vm'] = {}
        result['vm']['status'] = 'vm_error'
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
        logging.debug(args.resources)
        #Log.logger.debug(args.resources)
        try:
            for item in args.resources:
                TaskManager.task_start(
                    SLEEP_TIME, TIMEOUT, {'current_status': CREATE_VM},
                    _create_resource_set_and_query, item)
        except Exception as e:
            err_msg = e.message
            logging.error('err: %s' % err_msg)
            #Log.logger.error('err: %s' % err_msg)
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


# volume REST API Controller
class VolumenAPI(Resource):

    def delete(self, vol_id):
        try:
            logging.info('DELETE volume, vol_id is %s.', vol_id)
            cinder_client = OpenStack.cinder_client
            cinder_client.volumes.detach(vol_id)
            cinder_client.volumes.delete(vol_id)
        except Exception as e:
            err_msg = e.message
            logging.exception(
                "[CRP] VolumenAPI delete failed, Exception:%s",
                e.args)
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
                    "msg": "删除成功"
                }
            }
            return res, 200


mpc_resource_api.add_resource(ResourceAPI, '/resource')
mpc_resource_api.add_resource(VolumenAPI, '/volume/<vol_id>')
