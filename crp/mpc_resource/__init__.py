# -*- coding: utf-8 -*-
import requests
import json

from flask import Blueprint
from crp.openstack import OpenStack
from crp.taskmgr import *
from crp.log import Log

from config import APP_ENV, configs


mpc_resource_blueprint = Blueprint('mpc_resource_blueprint', __name__)

SYNC_SLEEP_TIME = 10
SYNC_TIMEOUT = 60 * 60 * 24 * 365 * 100
MPC_URL = configs[APP_ENV].MPC_URL
MPC_RES_CALLBACK_URL = MPC_URL+'api/mpc_resource/mpc_resources_callback'


def mpc_resource_callback(vms):
    data_dict = {
        'vms': vms
    }
    data_str = json.dumps(data_dict)
    url = MPC_RES_CALLBACK_URL
    headers = {
        'Content-Type': 'application/json'
    }
    Log.logger.debug(
        "mpc_resource_callback: " + url +
        ' ' + json.dumps(headers) + ' ' + data_str)
    cbk_result = requests.put(
        url=url, headers=headers, data=data_str)
    return cbk_result


def _instance_status_sync(task_id, result):
    Log.logger.debug(
        "SYNC Inst Status Task ID %s" % task_id)
    # print "SYNC Inst Status Task ID %s" % task_id
    nc = OpenStack.nova_client
    vms = nc.servers.list()
    insts = []
    for vm in vms:
        # Log.logger.debug(str(dir(vm)))
        insts.append({
            'os_inst_id': vm.id,
            'status': vm.status,
        })
    Log.logger.debug("OpenStack vm number: "+ str(len(insts)))
    err_msg = None
    cbk_result = None
    try:
        cbk_result = mpc_resource_callback(insts)
        cbk_result = json.dumps(cbk_result.json())
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message
    finally:
        Log.logger.debug(
            "Callback Task ID " + str(task_id) + '\r\n' +
            'mpc_res_callback result ' + str(cbk_result))
        if err_msg:
            Log.logger.debug(
                "Callback Task ID " + str(task_id) + '\r\n' +
                'mpc_res_callback err_msg ' + str(err_msg))


def instance_status_sync():
    try:
        TaskManager.task_start(
            SYNC_SLEEP_TIME, SYNC_TIMEOUT,
            {}, _instance_status_sync)
    except Exception as e:
        Log.logger.error(
            'instance_status_sync err %s'
            % e.message)


from . import handler, forms, errors
