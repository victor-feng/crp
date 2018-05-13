# -*- coding:utf8 -*-

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


# 创建volume
# 挂载volume到虚机




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
    err_msg = None
    try:
        cinder_client = OpenStack.cinder_client
        volume_name = vm.get("vm_name","") + "-vol"
        os_inst_id = vm.get("os_inst_id")
        volume = cinder_client.volumes.create(name=volume_name, size=volume_size,scheduler_hints={"local_to_instance":os_inst_id})
        Log.logger.info("Create volume os_inst_id is {},volume is {}".format(os_inst_id,volume.to_dict().__str__()))
    except Exception as e:
        err_msg = "create volume error {e}".format(e=str(e))
        Log.logger.error(err_msg)
    return volume,err_msg



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

def create_volume_by_type(cluster_type,volume_size,quantity,os_inst_id,instance_name):

    if((cluster_type not in ["mycat", "redis"]) or (
        cluster_type in ["mycat", "redis"] and quantity == 1)) and volume_size > 0:
        #如果cluster_type是mysql 和 mongodb 就挂卷 或者 volume_size 不为0时
        vm = {
            'vm_name': instance_name,
            'os_inst_id': os_inst_id,
        }
        #创建volume
        volume,err_msg=create_volume(vm, volume_size)
        if not err_msg:
            os_vol_id = volume.id
        else:
            os_vol_id = None
    else:
        os_vol_id = None

    return  os_vol_id,err_msg

