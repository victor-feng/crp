# -*- coding: utf-8 -*-

import logging
import requests
import json

from flask import Blueprint
from flask import current_app

# TODO: import * is bad!!
from crp.taskmgr import *
from crp.openstack import OpenStack
from crp.log import Log

from config import APP_ENV, configs


mpc_resource_blueprint = Blueprint('mpc_resource_blueprint', __name__)

# TODO: move to global conf
SYNC_SLEEP_TIME = 10
SYNC_TIMEOUT = 60 * 60 * 24 * 365 * 100
MPC_URL = configs[APP_ENV].MPC_URL
MPC_RES_CALLBACK_URL = MPC_URL+'api/mpc_resource/mpc_resources_callback'


def mpc_resource_callback(vms):

    MPC_RES_CALLBACK_URL = MPC_URL + 'api/mpc_resource/mpc_resources_callback'
    #MPC_RES_CALLBACK_URL = current_app.config['MPC_URL'] + 'api/mpc_resource/mpc_resources_callback'
    
    data_dict = {
        'vms': vms
    }
    data_str = json.dumps(data_dict)
    url = MPC_RES_CALLBACK_URL
    headers = {
        'Content-Type': 'application/json'
    }
    #Log.logger.debug(
    logging.debug(
        "mpc_resource_callback: " + url +
        ' ' + json.dumps(headers) + ' ' + data_str)
    cbk_result = requests.put(
        url=url, headers=headers, data=data_str)
    return cbk_result


def _instance_status_sync(task_id, result):
    #Log.logger.debug(
    logging.debug(
        "SYNC Inst Status Task ID %s" % task_id)
    # print "SYNC Inst Status Task ID %s" % task_id
    nc = OpenStack.nova_client
    vms = nc.servers.list()
    insts = []
    for vm in vms:
        insts.append({
            'os_inst_id': vm.id,
            'status': 'vm_error'
            if vm.status == 'ERROR'
            else vm.status,
        })
    logging.debug("OpenStack vm number: "+ str(len(insts)))
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
        #Log.logger.debug(
        logging.debug(
            "Callback Task ID " + str(task_id) + '\r\n' +
            'mpc_res_callback result ' + str(cbk_result))
        if err_msg:
            #Log.logger.debug(
            logging.debug(
                "Callback Task ID " + str(task_id) + '\r\n' +
                'mpc_res_callback err_msg ' + str(err_msg))


def instance_status_sync(mpc_sync=False):
    if not mpc_sync:
    #if MPC_URL == '' or MPC_URL is None:
        logging.info('[CRP] MPC instance_status_sync not support, mpc_sync: %s', mpc_sync)
    else:
        logging.info('[CRP] MPC instance_status_sync started')
        try:
            TaskManager.task_start(
                SYNC_SLEEP_TIME, SYNC_TIMEOUT,
                {}, _instance_status_sync)
        except Exception as e:
            #Log.logger.error(
            logging.error(
                'instance_status_sync err %s'
                % e.message)


from . import handler, forms, errors
