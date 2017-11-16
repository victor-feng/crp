# -*- coding: utf-8 -*-


import logging
import json
import requests
from crp.log import Log
from crp.openstack import OpenStack
from crp.taskmgr import *
from config import APP_ENV, configs

QUERY_VOLUME = 0
DETACH_VOLUME = 1
DETACH_VOLUME_SUCCESSFUL = 2
QUERY_VM=3
DELETE_VM=4


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
        delete_request_callback(task_id, result)
        TaskManager.task_exit(task_id)

def delete_instance(task_id, result):
    os_inst_id = result.get('os_inst_id', '')
    nova_client = OpenStack.nova_client
    try:
        nova_client.servers.delete(os_inst_id)
        result['current_status'] = QUERY_VM
        result['msg']='delete instance begin query Instance status'
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
        TaskManager.task_exit(task_id)


#卸载volume
def detach_volume(task_id, result, resource):
    os_inst_id = resource.get('os_inst_id')
    os_vol_id = resource.get('os_vol_id')
    Log.logger.debug(
        'Task ID %s,begin detach_volume, os_inst_id is %s, os_vol_id is %s.'% (task_id, os_inst_id, os_vol_id))

    try:
        if os_vol_id:
            nova_client = OpenStack.nova_client
            nova_client.volumes.delete_server_volume(os_inst_id, os_vol_id)
        elif not os_vol_id:
            #如果volume不存在直接删除虚机
            result['current_status'] = QUERY_VM
    except Exception as e:
        raise e
    else:
        result['current_status'] = QUERY_VOLUME

#查询volume状态
def query_volume_status(task_id, result, resource):
    os_vol_id = resource.get('os_vol_id')
    if os_vol_id:
        #如果volume存在直接查询volume状态
        cinder_client = OpenStack.cinder_client
        vol = cinder_client.volumes.get(os_vol_id)
        Log.logger.debug(
            "Task ID %s, query_detach_status, Volume status: %s, info: %s" % (task_id, vol.status, vol))
        if vol.status == 'available':
            result['current_status'] = DETACH_VOLUME_SUCCESSFUL
            Log.logger.info(
                "Task ID %s, detach volume(%s) successful." % (task_id, os_vol_id))
        elif vol.status == 'attaching':
            result['current_status'] = DETACH_VOLUME
            Log.logger.debug(
                "Task ID %s, begin detach volume , vol_id is %s" %(task_id,os_vol_id))
        elif vol.status == 'error' or 'error' in vol.status:
            Log.logger.error(
                "Task ID %s, volume status is error begin delete volume, vol_id is %s" %(task_id,os_vol_id))
            result['current_status'] = DETACH_VOLUME_SUCCESSFUL
    elif not os_vol_id:
        #volume 不存在 直接删除虚机
        result['current_status']=QUERY_VM



def delete_volume(task_id,result,resource):
    os_vol_id = resource.get('os_vol_id')
    try:
        if os_vol_id:
            cinder_client = OpenStack.cinder_client
            cinder_client.volumes.delete(os_vol_id)
        result['current_status'] = QUERY_VM
        Log.logger.debug(
            "Task ID %s, delete volume , vol_id is %s" % (task_id,os_vol_id))
    except Exception as e:
        Log.logger.exception(
            "[CRP] _delete_volume failed, Exception:%s" %e.args)
        result['current_status'] = QUERY_VM


def delete_instance_and_query(task_id, result, resource):
    current_status = result.get('current_status', None)
    Log.logger.debug(
         "Task ID %s,\r\n resource %s ." %
         (task_id, resource))
    try:
        if current_status == QUERY_VOLUME:
            query_volume_status(task_id, result, resource)
        elif current_status == DETACH_VOLUME:
            detach_volume(task_id, result, resource)
        elif current_status == QUERY_VOLUME:
            query_volume_status(task_id, result, resource)
        elif current_status == DETACH_VOLUME_SUCCESSFUL:
            delete_volume(task_id, result,resource)
        elif current_status == QUERY_VM:
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
def delete_request_callback(task_id, result):
    data = {
            'resources_id': result.get('resources_id', ''),
            'os_inst_id': result.get('os_inst_id', ''),
            'msg': result.get('msg', ''),
            'code': result.get('code', ''),
            'unique_flag': result.get('unique_flag',''),
            'del_os_ins_ip_list': result.get('del_os_ins_ip_list', []),
            "set_flag":result.get('set_flag',''),
        }
    headers = {'Content-Type': 'application/json'}
    DELETE_CALL_BACK=configs[APP_ENV].UOP_URL + 'api/res_callback/delete'
    try:
        data_str=json.dumps(data)
        res=requests.post(DELETE_CALL_BACK,data=data_str,headers=headers)
        res=json.dumps(res.json())
        Log.logger.debug(res)
    except BaseException as e:
        err_msg = e.args
        Log.logger.debug(
                "Callback Task ID " + str(task_id) + '\r\n' +
                'delete_request_callback err_msg ' + str(err_msg))





