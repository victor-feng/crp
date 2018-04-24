#!/usr/bin/env python
#coding:utf-8



import json
import requests
import os
from crp.log import Log
from crp.openstack2 import OpenStack
from del_handler2 import CrpException
from crp.utils.aio import exec_cmd_ten_times
from config import configs, APP_ENV
from crp.res_set import put_request_callback
from crp.taskmgr import *

SCRIPTPATH=configs[APP_ENV].SCRIPTPATH

QUERY_VM = 0
STOP_VM = 1
QUERY_VOLUME = 2
DETACH_VOLUME = 3
RESIZE_VOLUME = 4
ATTACH_VOLUME = 5
START_VM = 6
MOUNT_VOLUME = 7
RESIZE_FLAVOR = 8
RESIZE_CONFIRM = 9



def query_vm(task_id, result, resource):
    """
    向openstack查询虚机状态
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    os_inst_id =resource.get('os_inst_id', '')
    volume_exp_size = result.get("volume_exp_size",0)
    result['os_inst_id'] = os_inst_id
    flavor = result.get("flavor")
    nova_client = OpenStack.nova_client
    try:
        attach_state = result.get("attach_state", 0)
        confirm_state = result.get("confirm_state", 0)
        inst = nova_client.servers.get(os_inst_id)
        task_state = getattr(inst, 'OS-EXT-STS:task_state')
        if inst.status == 'SHUTOFF' and not task_state:
            if volume_exp_size > 0 and attach_state == 0:
                result['current_status'] = QUERY_VOLUME
                result['msg']='vm status is shutoff  begin query volume'
            elif  volume_exp_size > 0 and attach_state == 1:
                old_flavor = inst.flavor.get("id")
                if old_flavor != flavor:
                    result['current_status'] = RESIZE_FLAVOR
                    result['msg'] = 'vm status is shutoff  begin resize flavor'
                else:
                    result['current_status'] = START_VM
                    result['msg'] = 'vm status is shutoff  begin start vm'
                    result['exit_state'] = 1
            elif  volume_exp_size == 0 :
                old_flavor = inst.flavor.get("id")
                if old_flavor != flavor:
                    result['current_status'] = RESIZE_FLAVOR
                    result['msg'] = 'vm status is shutoff  begin resize flavor'
                else:
                    result['current_status'] = START_VM
                    result['msg'] = 'vm status is shutoff  begin start vm'
                    result['exit_state'] = 1
        elif inst.status == "ACTIVE" and not task_state:
            exit_state = result.get("exit_state", 0)
            if attach_state == 0 and confirm_state == 0 and exit_state == 0:
                result['current_status'] = STOP_VM
                result['msg'] = 'vm status is active  begin stop vm'
            elif attach_state == 1 and confirm_state == 0 and exit_state == 0:
                result['current_status'] = MOUNT_VOLUME
                result['msg'] = 'vm status is active  begin mount volume'
            elif confirm_state == 1 or exit_state == 1:
                result['status'] = "success"
                put_request_callback(task_id, result)
                TaskManager.task_exit(task_id)
        elif inst.status == "VERIFY_RESIZE" and not task_state:
            result['current_status'] = RESIZE_CONFIRM
            result['msg'] = 'vm status is VERIFY_RESIZE  begin vm resize confirm'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " query Instance ID " + os_inst_id +
            " Status is " + inst.status + " Result is " + result.__str__())
    except Exception as e:
        err_msg = "Query vm error {}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)


def stop_vm(task_id,result):
    nova_client = OpenStack.nova_client
    os_inst_id = result.get('os_inst_id', '')
    try:
        nova_client.servers.stop(os_inst_id)
        result['current_status'] = QUERY_VM
        result['msg'] = 'stop vm begin query volume'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " query Instance ID " + str(os_inst_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Stop vm error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)

def start_vm(task_id,result):
    nova_client = OpenStack.nova_client
    os_inst_id = result.get('os_inst_id', '')
    try:
        nova_client.servers.start(os_inst_id)
        result['current_status'] = QUERY_VM
        result['msg'] = 'start vm begin mount volume'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " query Instance ID " + str(os_inst_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Start vm error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)

def resize_volume(task_id,result,resource):
    os_vol_id = resource.get('os_vol_id')
    volume_exp_size = result.get("volume_exp_size",0)
    cinder_client = OpenStack.cinder_client
    try:
        volume = cinder_client.volumes.get(os_vol_id)
        volume_size = volume.size
        volume_size = volume_size + volume_exp_size
        cinder_client.volumes.extend(os_vol_id,volume_size)
        result['current_status'] = QUERY_VOLUME
        result['revol_state'] = 1
        result['msg'] = 'resize volume  begin attack volume'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Resize volume error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)

def attach_volume(task_id,result,resource):
    os_inst_id = result.get('os_inst_id', '')
    try:
        nova_client = OpenStack.nova_client
        os_vol_id = resource.get('os_vol_id')
        nova_client.volumes.create_server_volume(os_inst_id, os_vol_id)
        result['current_status'] = QUERY_VOLUME
        result['msg'] = 'resize volume  begin attack volume'
        result['attach_state'] = 1
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Attach volume error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)

def detach_volume(task_id, result, resource):
    """
    卸载卷
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    os_inst_id = resource.get('os_inst_id')
    os_vol_id = resource.get('os_vol_id')
    try:
        nova_client = OpenStack.nova_client
        nova_client.volumes.delete_server_volume(os_inst_id, os_vol_id)
        result['current_status'] = QUERY_VOLUME
        result['msg'] = 'detach volume  begin query volume'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Detach volume error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)

def query_volume(task_id, result, resource):
    """
    查询volume状态
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    try:
        os_vol_id = resource.get('os_vol_id')
        #如果volume存在直接查询volume状态
        cinder_client = OpenStack.cinder_client
        vol = cinder_client.volumes.get(os_vol_id)
        if vol.status == 'available':
            revol_state = result.get("revol_state",0)
            if revol_state == 0:
                result['current_status'] = RESIZE_VOLUME
                result['msg'] = 'volume status is avaiable  begin resize volume'
            elif revol_state == 1:
                result['current_status'] = ATTACH_VOLUME
                result['msg'] = 'volume status is avaiable  begin attach volume'
        elif vol.status == 'in-use':
            attach_state = result.get("attach_state",0)
            if attach_state == 0:
                result['current_status'] = DETACH_VOLUME
                result['msg'] = 'volume status is in-use  begin detach volume'
            elif attach_state == 1:
                result['current_status'] = START_VM
                result['msg'] = 'volume status is in-use  begin start vm'
        elif vol.status == 'error' or 'error' in vol.status:
            err_msg = "volume status is error"
            Log.logger.error(err_msg)
            raise CrpException(err_msg)
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Detach volume error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)


def mount_volume(task_id,result,resource):
    dir = os.path.dirname(
        os.path.abspath(__file__))
    ip = resource.get("ip")
    try:
        scp_cmd = "ansible {ip} --private-key={key_dir}old_id_rsa -m" \
                  " copy -a 'src={dir}/volume.py dest=/tmp/ mode=777'".format(ip=ip, key_dir=SCRIPTPATH,dir=dir)
        exec_cmd = "ansible {ip} --private-key={dir}old_id_rsa " \
                   "-m raw -a 'python /tmp/volume.py'".format(ip=ip, dir=SCRIPTPATH)
        exec_cmd_ten_times(ip, scp_cmd, 6)
        exec_cmd_ten_times(ip, exec_cmd, 6)
        result['current_status'] = STOP_VM
        result['msg'] = 'monut volume success,begin stop vm'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Mount volume error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)


def resize_flavor(task_id,result):
    nova_client = OpenStack.nova_client
    os_inst_id = result.get('os_inst_id', '')
    flavor = result.get('flavor')
    try:
        inst=nova_client.servers.get(os_inst_id)
        inst.resize(flavor)
        result['current_status'] = QUERY_VM
        result['msg'] = 'vm flavor resize begin query vm'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " query Instance ID " + str(os_inst_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Resize vm flavor error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)

def confim_flavor(task_id,result):
    nova_client = OpenStack.nova_client
    os_inst_id = result.get('os_inst_id', '')
    try:
        inst = nova_client.servers.get(os_inst_id)
        inst.confirm_resize()
        result['current_status'] = START_VM
        result['msg'] = 'vm flavor resize confirm begin start vm'
        result['confirm_state'] = 1
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " query Instance ID " + str(os_inst_id) +
            " result " + result.__str__())
    except Exception as e:
        err_msg = "Resize confirm vm flavor  error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)




def modfiy_vm_config2(task_id, result, resource):
    current_status = result.get('current_status', None)
    Log.logger.debug(
        "Task ID %s,\r\n resource %s .current_status %s" %
        (task_id, resource, current_status))
    try:
        if current_status == QUERY_VM:
            query_vm(task_id, result, resource)
        elif current_status == STOP_VM:
            stop_vm(task_id, result)
        elif current_status == QUERY_VOLUME:
            query_volume(task_id, result, resource)
        elif current_status == DETACH_VOLUME:
            detach_volume(task_id,result,resource)
        elif current_status == RESIZE_VOLUME:
            resize_volume(task_id,result,resource)
        elif current_status == ATTACH_VOLUME:
            attach_volume(task_id,result,resource)
        elif current_status == START_VM:
            start_vm(task_id, result)
        elif current_status == MOUNT_VOLUME:
            mount_volume(task_id,result,resource)
        elif current_status == RESIZE_FLAVOR:
            resize_flavor(task_id,result)
        elif current_status == RESIZE_CONFIRM:
            confim_flavor(task_id,result)
    except Exception as e:
        err_msg = " [CRP] modfiy_vm_config2 failed, Exception:%s" % str(e)
        Log.logger.error("Query Task ID " + str(task_id) + err_msg)
        result['msg'] = err_msg
        result['status'] = "fail"
        put_request_callback(task_id, result)
        TaskManager.task_exit(task_id)