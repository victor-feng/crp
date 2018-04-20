# -*- coding:utf8 -*-

import json
import requests
import logging
from crp.log import Log
from crp.openstack2 import OpenStack
from del_handler2 import CrpException
from crp.utils.aio import exec_cmd_ten_times
from config import configs, APP_ENV
from crp.res_set import put_request_callback

SCRIPTPATH=configs[APP_ENV].SCRIPTPATH
# 创建volume
# 挂载volume到虚机

QUERY_VM = 0
STOP_VM = 1
QUERY_VOLUME = 2
DETACH_VOLUME = 3
RESIZE_VOLUME = 4
ATTACH_VOLUME = 5
START_VM = 6
MOUNT_VOLUME = 7


'''
def create_volume(vm,volume_size):
    """
    创建卷
    :param vm:
    :param volume_size:
    :return:
    """
    data_dict = {
        "volume": {
            "status": "creating",
            "availability_zone": "nova",
            "source_volid": None,
            "display_description": None,
            "snapshot_id": None,
            "user_id": None,
            "size": volume_size,
            "display_name": "%s-vol" % vm.get('vm_name', ''),
            "imageRef": None,
            "attach_status": "detached",
            "volume_type": None,
            "project_id": None,
            "metadata": {},
            "lvm_instance_id": vm.get('os_inst_id', '')
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
        Log.logger.debug(data_str)
        cv_result = requests.post(url=url, headers=headers, data=data_str)
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.args
        Log.logger.error('error msg: %s' % err_msg)
    except BaseException as e:
        err_msg = e.args
        Log.logger.error('error msg: %s' % err_msg)
    finally:
        if err_msg:
            Log.logger.debug("CreateVolume Task ID " + str(vm.get('vm_name', '')) + '\r\n' + 'create_volume err_msg ' + str(err_msg))
            raise CrpException(err_msg)
        else:
            cv_result_dict = cv_result.json()
            volume = cv_result_dict.get('volume', {})
            res = {
                'id': volume.get('id', ''),
                'display_name': volume.get('display_name', ''),
            }
            Log.logger.debug("CreateVolume success %s" % res)
            return volume
'''

def create_volume(vm,volume_size):
    """
    创建卷，卷和虚机在同一台宿主机上
    :param vm:
    :param volume_size:
    :return:
    """
    volume = None
    try:
        cinder_client = OpenStack.cinder_client
        volume_name = vm.get("vm_name","") + "-vol"
        os_inst_id = vm.get("os_inst_id")
        volume = cinder_client.volumes.create(name=volume_name, size=volume_size,scheduler_hints={"local_to_instance":os_inst_id})
    except Exception as e:
        err_msg = "create volume error {e}".format(e=str(e))
        Log.logger.error(err_msg)
    return volume



def instance_attach_volume(os_inst_id, os_vol_id,device=None):
    """
    挂载卷
    :param os_inst_id:
    :param os_vol_id:
    :param device:
    :return:
    """
    try:
        nova_client = OpenStack.nova_client
        vol_attach_result = nova_client.volumes.create_server_volume(os_inst_id, os_vol_id, device)
        Log.logger.debug(
            "AttachVolume Task ID " +
            "\r\nvolume ID " + os_vol_id +
            "\r\ninstance ID " + os_inst_id +
            "\r\nresult: " + str(vol_attach_result.to_dict()))
        return "AttachVolumeSuccess"
    except BaseException as e:
        err_msg=str(e)
        Log.logger.error('attach volume os_inst_id is %s os_vol_id is  error msg: %s' % (os_inst_id,os_vol_id,err_msg))
        return "AttachVolumeError"





def query_vm(task_id, result, resource):
    """
    向openstack查询虚机状态
    :param task_id:
    :param result:
    :param resource:
    :return:
    """
    os_inst_id =resource.get('os_inst_id', '')
    result['os_inst_id'] = os_inst_id
    nova_client = OpenStack.nova_client
    try:
        inst = nova_client.servers.get(os_inst_id)
        if inst.status == 'SHUTOFF':
            result['current_status'] = QUERY_VOLUME
            result['msg']='vm status is shutoff  begin query volume'
        if inst.status == "ACTIVE":
            attach_state = result.get("attach_state",0)
            if attach_state == 0:
                result['current_status'] = STOP_VM
                result['msg'] = 'vm status is active  begin start vm'
            elif attach_state == 1:
                result['current_status'] = MOUNT_VOLUME
                result['msg'] = 'vm status is active  begin mount volume'
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
    volume_size = result.get("volume_size",100)
    cinder_client = OpenStack.cinder_client
    try:
        cinder_client.volumes.extend(os_vol_id,volume_size)
        result['current_status'] = ATTACH_VOLUME
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
            result['current_status'] = RESIZE_VOLUME
            result['msg'] = 'volume status is avaiable  begin resize volume'
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
    ip = resource.get("ip")
    try:
        scp_cmd = "ansible {ip} --private-key={dir}/old_id_rsa -m" \
                  " copy -a 'src={dir}/volume.py dest=/tmp/ mode=777'".format(ip=ip, dir=SCRIPTPATH)
        exec_cmd = "ansible {ip} --private-key={dir}/old_id_rsa " \
                   "-m shell -a 'python /tmp/volume.py'".format(ip=ip, dir=SCRIPTPATH)
        exec_cmd_ten_times(ip, scp_cmd, 6)
        exec_cmd_ten_times(ip, exec_cmd, 6)
        result['msg'] = 'monut volume success'
        result['status'] = 'success'
        Log.logger.debug(
            "Query Task ID " + str(task_id) +
            " result " + result.__str__())
        put_request_callback(task_id, result)
    except Exception as e:
        err_msg = "Mount volume error {e}".format(e=str(e))
        Log.logger.error(err_msg)
        raise CrpException(err_msg)





def volume_resize_and_query2(task_id, result, resource):
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
            mount_volume(task_id,result)
    except Exception as e:
        err_msg = " [CRP] volume_resize_and_query failed, Exception:%s" % str(e)
        Log.logger.error("Query Task ID " + str(task_id) + err_msg)
        result['msg'] = err_msg
        result['status'] = "fail"
        put_request_callback(task_id, result)