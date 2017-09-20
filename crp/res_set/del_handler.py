# -*- coding: utf-8 -*-


import logging
import json
import requests
from crp.log import Log
from crp.openstack import OpenStack
from crp.taskmgr import *
from config import APP_ENV, configs

QUERY_VM=0
DELETE_VM=1
UOP_URL = configs[APP_ENV].UOP_URL

#向openstack查询虚机状态
def query_instance(task_id, result, resource):
    os_inst_id =resource.get('os_inst_id', '')
    resource_id =resource.get('resources_id', '')
    result['os_inst_id'] = os_inst_id
    result['resources_id'] = resource_id
    nova_client = OpenStack.nova_client
    try:
        inst = nova_client.servers.get(os_inst_id)
        task_state=getattr(inst,'OS-EXT-STS:task_state')
        result['inst_state']=1
        Log.logger.debug(
        "Query Task ID " + str(task_id) +
        " query Instance ID " + os_inst_id +
        " Status is " + inst.status + " Instance task state is " + str(task_state)) 
        if  task_state != 'deleting' and inst.status != 'DELETED':
            result['current_status'] = DELETE_VM
            result['msg']='instance is exist  begin delete Instance'
    except Exception as e:
        inst_state=result.get('inst_state',0)
        if inst_state == 1:
            result['msg']='delete instance success'
            Log.logger.debug(
                "Query Task ID " + str(task_id) +
                " query Instance ID " + os_inst_id +
                " result " + result.__str__())
        elif inst_state == 0: 
            result['msg'] = 'instance is not exist'
            result['code'] = 404
            result['inst_state']=0
            Log.logger.debug(
                "Query Task ID " + str(task_id) +
                " query Instance ID " + os_inst_id +
                " result " + result.__str__())
        #request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)

def delete_instance(task_id, result):
    os_inst_id = result.get('os_inst_id', '')
    nova_client = OpenStack.nova_client
    try:
        nova_client.servers.delete(os_inst_id)
        result['current_status'] = QUERY_VM
        result['msg']='delete instance success begin query Instance status'
        result['code'] = 200
        Log.logger.debug(
              "Query Task ID " + str(task_id) +
              " query Instance ID " + os_inst_id +
              " result " + result.__str__())

    except Exception as e:
        result['msg'] = 'delete instance failed'
        result['code'] = 400
        Log.logger.error(
            "Query Task ID " + str(task_id) + " result " + result.__str__() + " [CRP] delete_instance failed, Exception:%s" %e)
        #request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)

def delete_instance_and_query(task_id, result, resource):
    current_status = result.get('current_status', None)
    Log.logger.debug(
         "Task ID %s,\r\n resource %s ." %
         (task_id, resource))
    try:
        if current_status == QUERY_VM:
            query_instance(task_id, result, resource)
        elif current_status == DELETE_VM:
            delete_instance(task_id, result)
        elif current_status == QUERY_VM:
            query_instance(task_id, result, resource)
    except Exception as e:
        Log.logger.error("Query Task ID " + str(task_id) +" [CRP] delete_instance_and_query failed, Exception:%s" %e)
         #request_res_callback(task_id, result)
        TaskManager.task_exit(task_id)




def delete_vip(port_id):
    try:
        neutron_client = OpenStack.neutron_client
        neutron_client.delete_port(port_id)
        Log.logger.debug('vip delete success port_id:%s' % port_id)
    except Exception as e:
        Log.logger.error(" delete vip  error, Exception:%s" % e)
    


# request UOP res_callback
def request_res_callback(task_id, result):
    ret = [
        {
            'resources_id': result.get('resources_id', ''),
            'os_inst_id': result.get('os_inst_id', ''),
            'msg': result.get('msg', ''),
            'code': result.get('code', ''),
        }
    ]
    err_msg = None
    cbk_result = None
    try:
        cbk_result = uop_resource_callback(ret)
        cbk_result = json.dumps(cbk_result.json())
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.args
    except BaseException as e:
        err_msg = e.args
    finally:
        Log.logger.debug(
            "Callback Task ID " + str(task_id) + '\r\n' +
            'mpc_res_callback result ' + str(cbk_result))
        if err_msg:
            Log.logger.debug(
                "Callback Task ID " + str(task_id) + '\r\n' +
                'mpc_res_callback err_msg ' + str(err_msg))


def uop_resource_callback(ret):
    UOP_RES_CALLBACK_URL = UOP_URL + 'api/resource/mpc_resources_callback'
    data_dict = {
        'ret': ret
    }
    data_str = json.dumps(data_dict)
    url = UOP_RES_CALLBACK_URL
    headers = {
        'Content-Type': 'application/json'
    }
    # Log.logger.debug(
    Log.logger.debug(
        "uop_resource_callback: " + url +
        ' ' + json.dumps(headers) + ' ' + data_str)
    cbk_result = requests.put(
        url=url, headers=headers, data=data_str)
    return cbk_result




